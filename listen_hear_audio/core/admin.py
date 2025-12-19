from django.contrib import admin
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import BusinessInfo, ServiceRequest


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "service_type", "status", "created_at")
    list_filter = ("status", "service_type", "created_at")
    search_fields = ("name", "email", "phone", "street_address", "city", "description")
    readonly_fields = ("user", "created_at", "updated_at")

    fieldsets = (
        (
            "Contact Information",
            {
                "fields": ("user", "name", "email", "phone"),
            },
        ),
        (
            "Service Address",
            {
                "fields": ("street_address", "city", "state", "zip_code"),
            },
        ),
        (
            "Service Details",
            {
                "fields": ("service_type", "description", "preferred_date", "preferred_time"),
            },
        ),
        (
            "Status & Response",
            {
                "fields": ("status", "admin_notes", "admin_response"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["send_response_email"]

    def send_response_email(self, request, queryset):
        """Send response email to selected service requests."""
        count = 0
        for service_request in queryset:
            if service_request.admin_response:
                subject = f"Re: Your Service Request - Listen Hear Smart Homes"
                message = render_to_string("core/emails/service_request_response.html", {
                    "service_request": service_request,
                })

                try:
                    send_mail(
                        subject,
                        message,
                        BusinessInfo.load().email,
                        [service_request.email],
                        html_message=message,
                        fail_silently=False,
                    )
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error sending email to {service_request.email}: {e}", level="error")

        if count:
            self.message_user(request, f"Successfully sent response emails to {count} customers.")

    send_response_email.short_description = "Send response email to selected"


@admin.register(BusinessInfo)
class BusinessInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Business Information",
            {
                "fields": ("business_name", "phone", "email"),
            },
        ),
        (
            "Address",
            {
                "fields": ("street_address", "city", "state", "zip_code"),
            },
        ),
        (
            "Google Maps",
            {
                "fields": ("google_maps_embed_url",),
                "description": "Go to Google Maps, search for your address, click Share > Embed a map, and paste the full iframe src URL here.",
            },
        ),
        (
            "Store Hours",
            {
                "fields": (
                    "monday_hours",
                    "tuesday_hours",
                    "wednesday_hours",
                    "thursday_hours",
                    "friday_hours",
                    "saturday_hours",
                    "sunday_hours",
                ),
            },
        ),
        (
            "Social Media",
            {
                "fields": ("facebook_url", "instagram_url", "twitter_url", "linkedin_url"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        """Only allow one instance."""
        return not BusinessInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion."""
        return False
