from django.contrib import admin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django_celery_beat.models import ClockedSchedule, IntervalSchedule, SolarSchedule
from django_summernote.models import Attachment

from .models import BrandPartner, SiteConfiguration, ServiceRequest, TeamMember

# Unregister unused admin models
admin.site.unregister(ClockedSchedule)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(Attachment)


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
                        SiteConfiguration.load().email,
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


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Business Information",
            {
                "fields": ("business_name", "phone", "email", "website", "logo"),
            },
        ),
        (
            "Address",
            {
                "fields": ("street_address", "city", "state", "zip_code"),
            },
        ),
        (
            "Hero Video",
            {
                "fields": ("hero_video", "hero_video_url"),
                "description": "Upload an MP4 or provide a URL for the looping background video. Uploaded file takes priority.",
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
            "Notifications",
            {
                "fields": ("notification_emails",),
                "description": 'Enter email addresses as a JSON array, e.g., ["email1@example.com", "email2@example.com"]',
            },
        ),
        (
            "Email Templates",
            {
                "fields": ("customer_email_subject", "customer_email_message"),
            },
        ),
        (
            "Legal",
            {
                "fields": ("quote_disclaimer",),
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
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion."""
        return False


@admin.register(BrandPartner)
class BrandPartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "title")

    fieldsets = (
        (None, {
            "fields": ("name", "title", "bio", "photo"),
        }),
        ("Display", {
            "fields": ("display_order", "is_active"),
        }),
    )
