from django.conf import settings
from django.db import models


class ServiceRequest(models.Model):
    """Model for service requests from customers."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="service_requests",
        null=True,
        blank=True,
        help_text="User who submitted the request (if logged in)",
    )

    # Contact Information
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # Service Address
    street_address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=10)

    # Service Details
    service_type = models.CharField(
        max_length=100,
        help_text="Type of service needed (e.g., Installation, Repair, Consultation)",
    )
    description = models.TextField(help_text="Detailed description of service needed")
    preferred_date = models.DateField(
        verbose_name="Preferred date(s)",
        null=True,
        blank=True,
    )
    preferred_time = models.CharField(max_length=50, blank=True)

    # Status and Admin Response
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    admin_notes = models.TextField(blank=True, help_text="Internal notes from admin")
    admin_response = models.TextField(blank=True, help_text="Response sent to customer")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"

    def __str__(self):
        return f"Service Request from {self.name} - {self.created_at.strftime('%Y-%m-%d')}"

    @property
    def full_address(self):
        """Return formatted full address."""
        return f"{self.street_address}, {self.city}, {self.state} {self.zip_code}"


class SiteConfiguration(models.Model):
    """Singleton model for all site-wide configuration and business information."""

    # Contact Information
    business_name = models.CharField(max_length=200, default="Listen Hear Smart Homes")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Address
    street_address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)

    # Store Hours
    monday_hours = models.CharField(max_length=50, default="9:00 AM - 5:00 PM")
    tuesday_hours = models.CharField(max_length=50, default="9:00 AM - 5:00 PM")
    wednesday_hours = models.CharField(max_length=50, default="9:00 AM - 5:00 PM")
    thursday_hours = models.CharField(max_length=50, default="9:00 AM - 5:00 PM")
    friday_hours = models.CharField(max_length=50, default="9:00 AM - 5:00 PM")
    saturday_hours = models.CharField(max_length=50, default="Closed")
    sunday_hours = models.CharField(max_length=50, default="Closed")

    # Social Media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # Website & Branding
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='site/', blank=True, null=True)

    # Notification emails (stored as JSON array)
    notification_emails = models.JSONField(
        default=list,
        help_text="List of email addresses to receive quote notifications"
    )

    # Email content
    customer_email_subject = models.CharField(
        max_length=200,
        default="Your Listen Hear! Quote Request"
    )
    customer_email_message = models.TextField(
        default="Thank you for your quote request. We'll review your requirements and get back to you within 24-48 hours."
    )

    # Terms and disclaimer
    quote_disclaimer = models.TextField(
        blank=True,
        default="This is an estimate based on the packages selected. Final pricing will be determined after consultation and site evaluation."
    )

    # Hero Video (looping background video for home/about pages)
    hero_video = models.FileField(
        upload_to='site/video/',
        blank=True,
        null=True,
        help_text="Upload an MP4 video for the hero background loop"
    )
    hero_video_url = models.URLField(
        blank=True,
        help_text="Or provide an external URL to a video file (used if no upload)"
    )

    # Google Maps
    google_maps_embed_url = models.TextField(
        blank=True,
        help_text="Full Google Maps embed URL from maps.google.com (Share > Embed a map)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return f"Site Configuration ({self.business_name})"

    def save(self, *args, **kwargs):
        """Ensure only one instance exists."""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Load the singleton instance."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def get_config(cls):
        """Alias for load() for backward compatibility."""
        return cls.load()

    @property
    def full_address(self):
        """Return formatted full address."""
        parts = [self.street_address, self.city]
        if self.state and self.zip_code:
            parts.append(f"{self.state} {self.zip_code}")
        return ", ".join(filter(None, parts))

    @property
    def hero_video_src(self):
        """Return the hero video source — uploaded file takes priority over URL."""
        if self.hero_video:
            return self.hero_video.url
        return self.hero_video_url or ""

    @property
    def google_maps_url(self):
        """Return Google Maps URL for the address."""
        if self.full_address:
            import urllib.parse
            return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(self.full_address)}"
        return ""


class BrandPartner(models.Model):
    """Brand logos displayed on the home page trust bar."""

    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='brands/', help_text="Brand logo image")
    website_url = models.URLField(blank=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Brand Partner"
        verbose_name_plural = "Brand Partners"

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    """Team member displayed on the about page."""

    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, help_text="Job title or role")
    bio = models.TextField(blank=True, help_text="Short blurb about this team member")
    photo = models.ImageField(upload_to='team/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

    def __str__(self):
        return f"{self.name} - {self.title}"
