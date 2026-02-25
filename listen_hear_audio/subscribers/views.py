from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from .models import Subscriber


@require_POST
@csrf_protect
def subscribe(request):
    email = request.POST.get('email', '').strip().lower()
    if not email or '@' not in email:
        return JsonResponse({'success': False, 'message': 'Please enter a valid email address.'})

    subscriber, created = Subscriber.objects.get_or_create(email=email)

    if created:
        return JsonResponse({'success': True, 'message': "You're subscribed! We'll send new posts your way."})

    if not subscriber.is_active:
        subscriber.is_active = True
        subscriber.unsubscribed_at = None
        subscriber.save(update_fields=['is_active', 'unsubscribed_at'])
        return JsonResponse({'success': True, 'message': "Welcome back! You've been re-subscribed."})

    return JsonResponse({'success': True, 'message': "You're already subscribed — thanks!"})


@csrf_protect
def unsubscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if not email or '@' not in email:
            return render(request, 'subscribers/unsubscribe.html', {
                'error': 'Please enter a valid email address.',
            })
        try:
            subscriber = Subscriber.objects.get(email=email)
            if subscriber.is_active:
                subscriber.unsubscribe()
                message = "You've been unsubscribed. Sorry to see you go!"
            else:
                message = 'That email is not currently subscribed.'
        except Subscriber.DoesNotExist:
            message = 'That email is not currently subscribed.'
        return render(request, 'subscribers/unsubscribe.html', {'success': message})

    return render(request, 'subscribers/unsubscribe.html')
