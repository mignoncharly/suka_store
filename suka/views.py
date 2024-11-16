from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart, CartItem, Category, Order, OrderItem
from django.db.models import Sum, F
import urllib.parse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from decimal import Decimal


def home(request):
    category_name = request.GET.get('category')
    search_query = request.GET.get('search', '').strip()

    products = Product.objects.all()
    if category_name:
        products = products.filter(category__name=category_name)
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    categories = Category.objects.all()
    return render(request, 'home.html', {'products': products, 'categories': categories})



####################### Cart ########################

def cart(request):
    cart = get_or_create_cart(request)
    return render(request, 'cart.html', {
        'cart': cart,
        'cart_items': cart.items.all()
    })


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

def cart_item_count(request):
    cart = get_or_create_cart(request)
    count = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
    return JsonResponse({'count': count})


@require_POST
def add_to_cart(request, product_id):
    cart = get_or_create_cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return JsonResponse({
        'success': True,
        'cart_count': cart.items.aggregate(total=Sum('quantity'))['total'] or 0
    })

def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    quantity = int(request.POST.get('quantity', 0))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    cart = cart_item.cart
    return JsonResponse({
        'success': True,
        'total_price': float(cart.get_total()),
        'item_total': float(cart_item.total_price) if quantity > 0 else 0,
        'cart_count': cart.items.aggregate(total=Sum('quantity'))['total'] or 0
    })

def delete_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = cart_item.cart
    cart_item.delete()
    
    return JsonResponse({
        'success': True,
        'total_price': float(cart.get_total()),
        'cart_count': cart.items.aggregate(total=Sum('quantity'))['total'] or 0
    })


######################### Checkout ##########################

def checkout(request):
    try:
        # Get or create cart
        cart = get_or_create_cart(request)
        cart_items = cart.items.all()
        
        if not cart_items.exists():
            messages.error(request, 'Your cart is empty!')
            return redirect('cart')
        
        total_price = cart.get_total()
        
        if request.method == 'POST':
            # Validate form data
            customer_name = request.POST.get('name', '').strip()
            customer_phone = request.POST.get('phone', '').strip()
            shipping_address = request.POST.get('address', '').strip()
            
            if not all([customer_name, customer_phone, shipping_address]):
                messages.error(request, 'Veuillez remplir tous les champs.')
                return render(request, 'checkout.html', {
                    'cart_items': cart_items,
                    'total_price': total_price
                })
                
            try:
                # Create the Order first
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    total=Decimal(str(total_price)),  # Convert to Decimal explicitly
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    shipping_address=shipping_address
                )
                
                # Create Order Items
                order_items = []
                for item in cart_items:
                    item_total = Decimal(str(item.product.price)) * item.quantity
                    order_items.append(OrderItem(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=Decimal(str(item.product.price)),
                        total_price=item_total
                    ))
                OrderItem.objects.bulk_create(order_items)
                
                # Generate WhatsApp message
                message = (
                    f"Nouvelle commande #{order.id}\n\n"
                    f"Client: {customer_name}\n"
                    f"Téléphone: {customer_phone}\n"
                    f"Addresse: {shipping_address}\n\n"
                    "Détails de la commande:\n"
                )
                
                for item in cart_items:
                    message += f"• {item.product.name} (x{item.quantity}): {item.quantity * item.product.price:.2f} Fcfa\n"
                
                message += f"\n Prix total: {total_price:.2f} Fcfa"
                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/+4917640455470?text={encoded_message}"
                
                # Clear the cart
                cart.items.all().delete()
                
                # Store order ID in session for confirmation page
                request.session['last_order_id'] = order.id
                
                return redirect('order_confirmation')
                
            except Exception as e:
                print(f"Error processing order: {str(e)}")  # Debug print
                messages.error(request, f'Error processing order: {str(e)}')
                return render(request, 'checkout.html', {
                    'cart_items': cart_items,
                    'total_price': total_price
                })
        
        return render(request, 'checkout.html', {
            'cart_items': cart_items,
            'total_price': total_price
        })
        
    except Exception as e:
        print(f"Outer error: {str(e)}")  # Debug print
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('cart')
 


# order_confirmation
def order_confirmation(request):
    order_id = request.session.get('last_order_id')
    if not order_id:
        return redirect('home')
        
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return redirect('home')
        
    # Generate WhatsApp message again for the confirmation page
    message = (
        f"Nouvelle commande #{order.id}\n\n"
        f"Client: {order.customer_name}\n"
        f"Téléphone: {order.customer_phone}\n"
        f"Addresse: {order.shipping_address}\n\n"
        "Détails de la commande:\n"
    )
    
    for item in order.orderitem_set.all():
        message += f"• {item.product.name} (x{item.quantity}): {item.total_price:.2f} Fcfa\n"
    
    message += f"\n Prix total: {order.total:.2f} Fcfa"
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/+4917640455470?text={encoded_message}"
    
    # Clear the order ID from session
    del request.session['last_order_id']
    
    return render(request, 'order_confirmation.html', {
        'order': order,
        'whatsapp_url': whatsapp_url
    })