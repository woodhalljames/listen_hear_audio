import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from listen_hear_audio.products.models import Package


class Cart(models.Model):
    """Shopping cart that persists across sessions"""
    
    session_key = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Cart {self.session_key}"

    def get_total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())

    def get_estimated_total(self):
        """Get estimated total price"""
        return sum(item.get_subtotal() for item in self.items.all())

    def clear(self):
        """Remove all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    """Individual items in a cart"""
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    notes = models.TextField(
        blank=True,
        help_text="Customer notes for this specific package"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['added_at']
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ['cart', 'package']

    def __str__(self):
        return f"{self.quantity}x {self.package.name}"

    def get_subtotal(self):
        """Get subtotal for this item"""
        return self.package.starting_price * self.quantity


class QuoteRequest(models.Model):
    """Customer quote request after checkout"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('quoted', 'Quote Sent'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
    ]
    
    quote_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='quote_requests'
    )
    
    # Customer information
    contact_person = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(help_text="Full installation address")
    zip_code = models.CharField(max_length=10, blank=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True, help_text="Customer notes and special requests")
    
    # Quote details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    estimated_total = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_path = models.FileField(upload_to='quotes/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quote Request'
        verbose_name_plural = 'Quote Requests'

    def __str__(self):
        return f"Quote {self.quote_number} - {self.contact_person}"

    def save(self, *args, **kwargs):
        if not self.quote_number:
            # Generate unique quote number: QR-YYYYMMDD-XXXX
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = str(uuid.uuid4())[:4].upper()
            self.quote_number = f"QR-{date_str}-{random_str}"
        super().save(*args, **kwargs)

    def get_total_items(self):
        """Get total number of items"""
        return sum(item.quantity for item in self.items.all())


class QuoteRequestItem(models.Model):
    """Items in a quote request - snapshot of package at time of quote"""
    
    quote_request = models.ForeignKey(
        QuoteRequest,
        on_delete=models.CASCADE,
        related_name='items'
    )
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True)
    
    # Snapshot of package details at time of quote
    package_name = models.CharField(max_length=200)
    package_description = models.TextField(blank=True)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Quote Request Item'
        verbose_name_plural = 'Quote Request Items'

    def __str__(self):
        return f"{self.quantity}x {self.package_name}"

    def get_subtotal(self):
        """Get subtotal for this item"""
        if self.price_snapshot is None:
            return 0
        return self.price_snapshot * self.quantity


class SiteConfiguration(models.Model):
    """Site-wide configuration for quote notifications and business info"""
    
    # Business information for PDF
    business_name = models.CharField(max_length=200, default="Listen Hear Audio")
    business_logo = models.ImageField(upload_to='site/', blank=True, null=True)
    business_address = models.TextField(blank=True)
    business_phone = models.CharField(max_length=20, blank=True)
    business_email = models.EmailField(blank=True)
    business_website = models.URLField(blank=True)
    
    # Notification emails (stored as JSON array)
    notification_emails = models.JSONField(
        default=list,
        help_text="List of email addresses to receive quote notifications"
    )
    
    # Email content
    customer_email_subject = models.CharField(
        max_length=200,
        default="Your Listen Hear Audio Quote Request"
    )
    customer_email_message = models.TextField(
        default="Thank you for your quote request. We'll review your requirements and get back to you within 24-48 hours."
    )
    
    # Terms and disclaimer
    quote_disclaimer = models.TextField(
        blank=True,
        default="This is an estimate based on the packages selected. Final pricing will be determined after consultation and site evaluation."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Configuration'
        verbose_name_plural = 'Site Configuration'

    def __str__(self):
        return f"Site Configuration (updated: {self.updated_at.strftime('%Y-%m-%d')})"

    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration"""
        config, created = cls.objects.get_or_create(pk=1)
        return config