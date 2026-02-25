from django.contrib import admin
from .models import Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'subscribed_at', 'unsubscribed_at']
    list_filter = ['is_active']
    search_fields = ['email']
    readonly_fields = ['subscribed_at', 'unsubscribed_at']
    ordering = ['-subscribed_at']
    actions = ['mark_unsubscribed', 'mark_resubscribed']

    def mark_unsubscribed(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_active=False, unsubscribed_at=timezone.now())
        self.message_user(request, f'{queryset.count()} subscriber(s) unsubscribed.')
    mark_unsubscribed.short_description = 'Unsubscribe selected'

    def mark_resubscribed(self, request, queryset):
        queryset.update(is_active=True, unsubscribed_at=None)
        self.message_user(request, f'{queryset.count()} subscriber(s) re-activated.')
    mark_resubscribed.short_description = 'Re-subscribe selected'
