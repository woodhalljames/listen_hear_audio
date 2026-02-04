from django.contrib.sessions.models import Session
from .models import Cart, CartItem
from listen_hear_audio.products.models import Package


def get_or_create_cart(request):
    """Get or create a cart for the current user/session"""
    if request.user.is_authenticated:
        # For authenticated users, get or create cart by user
        cart, created = Cart.objects.get_or_create(user=request.user)
        # If user had a session cart, merge it
        if not created and request.session.session_key:
            session_cart = Cart.objects.filter(
                session_key=request.session.session_key
            ).first()
            if session_cart and session_cart.id != cart.id:
                # Merge session cart into user cart
                for item in session_cart.items.all():
                    add_to_cart(cart, item.package.id, item.quantity, item.notes)
                session_cart.delete()
    else:
        # For anonymous users, use session key
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(
            session_key=request.session.session_key
        )
    
    return cart


def add_to_cart(cart, package_id, quantity=1, notes=''):
    """Add a package to the cart or update quantity if already exists"""
    try:
        package = Package.objects.get(id=package_id, is_active=True)
    except Package.DoesNotExist:
        return None
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        package=package,
        defaults={'quantity': quantity, 'notes': notes}
    )
    
    if not created:
        # Item already in cart, update quantity
        cart_item.quantity += quantity
        if notes:
            cart_item.notes = notes
        cart_item.save()
    
    return cart_item


def update_cart_item(cart, package_id, quantity, notes=''):
    """Update quantity and notes for a cart item"""
    try:
        cart_item = CartItem.objects.get(cart=cart, package_id=package_id)
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.notes = notes
            cart_item.save()
        else:
            cart_item.delete()
        return True
    except CartItem.DoesNotExist:
        return False


def remove_from_cart(cart, package_id):
    """Remove a package from the cart"""
    try:
        cart_item = CartItem.objects.get(cart=cart, package_id=package_id)
        cart_item.delete()
        return True
    except CartItem.DoesNotExist:
        return False


def get_cart_context(cart):
    """Get cart context data for templates"""
    items = cart.items.select_related(
        'package__category__property_type',
        'package__subcategory'
    ).order_by(
        'package__category__property_type__name',
        'package__category__name',
        'package__name'
    ).all()

    # Build category summary for simplified order display
    # Structure: {property_type_name: {category_name: total, ...}, ...}
    category_summary = {}
    for item in items:
        property_type_name = item.package.category.property_type.name
        category_name = item.package.category.name

        if property_type_name not in category_summary:
            category_summary[property_type_name] = {}

        if category_name not in category_summary[property_type_name]:
            category_summary[property_type_name][category_name] = {
                'total': 0,
                'has_custom': False,
            }

        if item.package.is_custom:
            category_summary[property_type_name][category_name]['has_custom'] = True
        else:
            category_summary[property_type_name][category_name]['total'] += item.get_subtotal()

    return {
        'cart': cart,
        'cart_items': items,
        'category_summary': category_summary,
        'total_items': cart.get_total_items(),
        'estimated_total': cart.get_estimated_total(),
        'discount_amount': cart.get_discount_amount(),
        'final_total': cart.get_final_total(),
        'applied_coupon': cart.coupon,
    }