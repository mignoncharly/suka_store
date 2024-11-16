from django.db.models import Sum

def cart_item_count(request):
    if hasattr(request, 'cart'):
        count = request.cart.items.aggregate(total=Sum('quantity'))['total'] or 0
    else:
        count = 0
    return {'cart_item_count': count}