// Add this to a new static/js/cart.js file
function addToCart(productId) {
    fetch(`/add-to-cart/${productId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount(data.cart_count);
            showNotification('Item added to cart');
        }
    });
}

function updateQuantity(itemId, newValue) {
    let quantity;
    if (typeof newValue === 'number') {
        // Handle + / - buttons
        const input = document.querySelector(`#cart-item-${itemId} .quantity-input`);
        quantity = parseInt(input.value) + newValue;
        input.value = quantity;
    } else {
        // Handle direct input
        quantity = parseInt(newValue);
    }

    if (quantity < 1) quantity = 1;

    fetch(`/update-cart-item/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById(`item-total-${itemId}`).textContent = data.item_total.toFixed(2);
            document.getElementById('cart-total').textContent = data.total_price.toFixed(2);
            updateCartCount(data.cart_count);
        }
    });
}

function deleteItem(itemId) {
    fetch(`/delete-cart-item/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const itemElement = document.getElementById(`cart-item-${itemId}`);
            itemElement.remove();
            document.getElementById('cart-total').textContent = data.total_price.toFixed(2);
            updateCartCount(data.cart_count);
            
            // Check if cart is empty and refresh if needed
            if (data.cart_count === 0) {
                window.location.reload();
            }
        }
    });
}

function updateCartCount(count) {
    // Update cart count in the header
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        cartCount.textContent = count;
    }
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Optional: Add a notification system
function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}