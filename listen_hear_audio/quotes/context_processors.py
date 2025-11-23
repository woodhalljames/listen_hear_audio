from listen_hear_audio.quotes.cart import get_or_create_cart


def cart_context(request):
    """Add cart information to all template contexts"""
    cart = get_or_create_cart(request)
    return {
        'cart_count': cart.get_total_items(),
        'cart': cart,
    }