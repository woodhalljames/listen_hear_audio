from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse, FileResponse, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import QuoteRequest, QuoteRequestItem
from .cart import get_or_create_cart, add_to_cart, update_cart_item, remove_from_cart, get_cart_context
from .forms import CheckoutForm
from .tasks import generate_quote_pdf, send_quote_emails
from listen_hear_audio.products.models import Package


def cart_view(request):
    """Display the shopping cart"""
    cart = get_or_create_cart(request)
    context = get_cart_context(cart)
    return render(request, 'quotes/cart.html', context)


@require_POST
def add_to_cart_view(request, package_id):
    """Add a package to cart (AJAX)"""
    cart = get_or_create_cart(request)
    quantity = int(request.POST.get('quantity', 1))
    notes = request.POST.get('notes', '')
    
    cart_item = add_to_cart(cart, package_id, quantity, notes)
    
    if cart_item:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Package added to quote',
                'cart_count': cart.get_total_items()
            })
        messages.success(request, 'Package added to your quote!')
        return redirect('quotes:cart')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Package not found'
            }, status=404)
        messages.error(request, 'Package not found.')
        return redirect('products:catalog')


@require_POST
def update_cart_view(request, package_id):
    """Update cart item quantity"""
    cart = get_or_create_cart(request)
    quantity = int(request.POST.get('quantity', 0))
    notes = request.POST.get('notes', '')
    
    if update_cart_item(cart, package_id, quantity, notes):
        messages.success(request, 'Cart updated!')
    else:
        messages.error(request, 'Item not found in cart.')
    
    return redirect('quotes:cart')


@require_POST
def remove_from_cart_view(request, package_id):
    """Remove item from cart"""
    cart = get_or_create_cart(request)
    
    if remove_from_cart(cart, package_id):
        messages.success(request, 'Item removed from cart.')
    else:
        messages.error(request, 'Item not found in cart.')
    
    return redirect('quotes:cart')


@require_POST
def apply_coupon_view(request):
    """Apply a coupon code to the cart"""
    from .models import Coupon

    cart = get_or_create_cart(request)
    coupon_code = request.POST.get('coupon_code', '').strip().upper()

    if not coupon_code:
        messages.error(request, 'Please enter a coupon code.')
        return redirect('quotes:cart')

    try:
        coupon = Coupon.objects.get(code=coupon_code)

        # Check if coupon is valid
        total = cart.get_estimated_total()
        is_valid, message = coupon.is_valid(total)

        if is_valid:
            cart.coupon = coupon
            cart.save()
            discount = cart.get_discount_amount()
            messages.success(request, f'Coupon "{coupon_code}" applied! You save ${discount:.2f}')
        else:
            messages.error(request, f'Coupon "{coupon_code}" is not valid: {message}')

    except Coupon.DoesNotExist:
        messages.error(request, f'Coupon "{coupon_code}" not found.')

    return redirect('quotes:cart')


@require_POST
def remove_coupon_view(request):
    """Remove the applied coupon from the cart"""
    cart = get_or_create_cart(request)

    if cart.coupon:
        coupon_code = cart.coupon.code
        cart.coupon = None
        cart.save()
        messages.success(request, f'Coupon "{coupon_code}" removed.')

    return redirect('quotes:cart')


def checkout_view(request):
    """Checkout page"""
    cart = get_or_create_cart(request)
    
    # Redirect if cart is empty
    if cart.get_total_items() == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('products:catalog')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create quote request
            quote_request = QuoteRequest.objects.create(
                user=request.user if request.user.is_authenticated else None,
                contact_person=form.cleaned_data['contact_person'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                street=form.cleaned_data.get('street', ''),
                city=form.cleaned_data['city'],
                state=form.cleaned_data.get('state', ''),
                zip_code=form.cleaned_data['zip_code'],
                website=form.cleaned_data.get('website', ''),
                notes=form.cleaned_data.get('notes', ''),
                estimated_total=cart.get_estimated_total(),
                email_recipients=form.cleaned_data['email']  # Pre-populate with customer email
            )
            
            # Copy cart items to quote request
            for cart_item in cart.items.all():
                QuoteRequestItem.objects.create(
                    quote_request=quote_request,
                    package=cart_item.package,
                    package_name=cart_item.package.name,
                    package_description=cart_item.package.short_description,
                    installation_phase_snapshot=cart_item.package.installation_phase,
                    price_snapshot=cart_item.package.starting_price,
                    quantity=cart_item.quantity,
                    notes=cart_item.notes
                )
            
            # Clear the cart
            cart.clear()

            # Chain tasks: generate PDF first, then send emails
            # This prevents the 60-second delay from retries
            from celery import chain
            task_chain = chain(
                generate_quote_pdf.si(quote_request.id),
                send_quote_emails.si(quote_request.id)
            )
            task_chain.apply_async()

            # Redirect to confirmation
            return redirect('quotes:quote_confirmation', quote_number=quote_request.quote_number)
    else:
        # Pre-fill form for authenticated users
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'contact_person': request.user.name,
                'email': request.user.email,
            }
        form = CheckoutForm(initial=initial_data)
    
    context = {
        **get_cart_context(cart),
        'form': form,
    }
    return render(request, 'quotes/checkout.html', context)


def quote_confirmation_view(request, quote_number):
    """Quote confirmation page"""
    quote_request = get_object_or_404(QuoteRequest, quote_number=quote_number)
    
    # Ensure user can only view their own quotes
    if quote_request.user and quote_request.user != request.user:
        messages.error(request, 'You do not have permission to view this quote.')
        return redirect('products:catalog')
    
    context = {
        'quote_request': quote_request,
    }
    return render(request, 'quotes/confirmation.html', context)


@login_required
def download_quote_pdf(request, quote_number):
    """Download PDF for a quote request"""
    quote_request = get_object_or_404(QuoteRequest, quote_number=quote_number)

    # Ensure user can only download their own quotes
    if quote_request.user != request.user:
        raise Http404("Quote not found")

    # Check if PDF exists
    if not quote_request.pdf_path:
        messages.error(request, "PDF is not yet available. Please try again in a moment.")
        return redirect('users:detail', pk=request.user.pk)

    # Return PDF as download
    return FileResponse(
        quote_request.pdf_path.open('rb'),
        as_attachment=True,
        filename=f'quote_{quote_request.quote_number}.pdf'
    )