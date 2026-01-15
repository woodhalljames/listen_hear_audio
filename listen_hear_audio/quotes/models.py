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
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='carts',
        help_text="Applied coupon code"
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

    def get_discount_amount(self):
        """Calculate discount amount if coupon is applied"""
        if not self.coupon:
            return 0

        total = self.get_estimated_total()
        is_valid, message = self.coupon.is_valid(total)

        if not is_valid:
            # Invalid coupon, clear it
            self.coupon = None
            self.save()
            return 0

        return self.coupon.calculate_discount(total)

    def get_final_total(self):
        """Get total after discount"""
        return self.get_estimated_total() - self.get_discount_amount()

    def clear(self):
        """Remove all items from cart"""
        self.items.all().delete()
        self.coupon = None
        self.save()


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
        if self.package.is_custom:
            return 0  # Custom packages don't have a price until quoted
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
    street = models.CharField(max_length=300, blank=True, help_text="Street address")
    city = models.CharField(max_length=100, help_text="City")
    state = models.CharField(max_length=2, blank=True, help_text="State (2-letter abbreviation)")
    zip_code = models.CharField(max_length=10)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True, help_text="Customer notes and special requests")
    
    # Quote details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    estimated_total = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_path = models.FileField(upload_to='quotes/', blank=True, null=True)

    # Admin finalization
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes for admin team (not visible to customer)"
    )
    final_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Final quoted price (overrides estimated total when set)"
    )
    email_recipients = models.TextField(
        blank=True,
        verbose_name="Email Recipients",
        help_text="Email addresses to send finalized quote to (one per line or comma-separated). Defaults to customer email."
    )
    builder_email = models.EmailField(
        blank=True,
        verbose_name="Builder Email",
        help_text="Email of the builder account to assign to the property created from this quote"
    )
    finalized_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the quote was finalized and sent to customer"
    )
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='finalized_quotes',
        help_text="Admin user who finalized this quote"
    )

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

    def get_effective_total(self):
        """Get the final total if set, otherwise estimated total"""
        return self.final_total if self.final_total is not None else self.estimated_total

    def is_finalized(self):
        """Check if quote has been finalized"""
        return self.finalized_at is not None

    def get_recipient_options(self):
        """Get list of email options for finalization"""
        emails = [self.email]  # Quote submitter email

        if self.user and self.user.email:
            emails.append(self.user.email)

        # Return unique emails
        return list(set(filter(None, emails)))

    def recalculate_estimated_total(self):
        """Recalculate estimated total from items"""
        self.estimated_total = sum(item.get_subtotal() for item in self.items.all())
        return self.estimated_total

    def get_email_recipients(self):
        """Parse email_recipients field into list of email addresses. Defaults to quote email if empty."""
        if not self.email_recipients:
            # Default to the customer's email
            return [self.email] if self.email else []

        # Split by newlines or commas
        import re
        emails = re.split(r'[,\n]+', self.email_recipients)
        # Clean up whitespace and filter empty strings
        emails = [email.strip() for email in emails if email.strip()]
        return emails


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
    installation_phase_snapshot = models.CharField(
        max_length=50,
        blank=True,
        help_text="Installation phase at time of quote"
    )
    price_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Price per unit (leave blank for custom pricing)"
    )

    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(
        blank=True,
        verbose_name="Customer Notes",
        help_text="Notes from the customer about this package (visible to customer in emails/PDFs)"
    )

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

    def save(self, *args, **kwargs):
        """Auto-populate installation_phase_snapshot from package if not set"""
        if self.package and not self.installation_phase_snapshot:
            self.installation_phase_snapshot = self.package.installation_phase
        super().save(*args, **kwargs)


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


class Coupon(models.Model):
    """Discount coupon codes for quotes"""

    DISCOUNT_TYPES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Coupon code (case-insensitive)"
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Internal description of this coupon"
    )
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPES,
        default='percentage'
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Percentage (e.g., 10 for 10%) or fixed amount (e.g., 100.00)"
    )

    # Validity
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    # Usage limits
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of times this coupon can be used (leave blank for unlimited)"
    )
    current_uses = models.PositiveIntegerField(default=0)

    # Order amount restrictions
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum order amount required (e.g., 5000.00)"
    )
    max_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum order amount allowed (e.g., 25000.00)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'

    def __str__(self):
        return f"{self.code} - {self.get_discount_display()}"

    def clean(self):
        """Validate coupon data"""
        from django.core.exceptions import ValidationError

        if self.discount_value is not None:
            if self.discount_type == 'percentage' and self.discount_value > 100:
                raise ValidationError({'discount_value': 'Percentage discount cannot exceed 100%'})

            if self.discount_value < 0:
                raise ValidationError({'discount_value': 'Discount value cannot be negative'})

        if self.valid_from and self.valid_until:
            if self.valid_until <= self.valid_from:
                raise ValidationError({'valid_until': 'End date must be after start date'})

        if self.min_order_amount and self.max_order_amount:
            if self.min_order_amount > self.max_order_amount:
                raise ValidationError({'max_order_amount': 'Maximum amount must be greater than minimum amount'})

    def save(self, *args, **kwargs):
        """Uppercase the code for consistency"""
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    def get_discount_display(self):
        """Return human-readable discount"""
        if self.discount_type == 'percentage':
            return f"{self.discount_value}% off"
        else:
            return f"${self.discount_value} off"

    def is_valid(self, order_total=None):
        """Check if coupon is currently valid"""
        from django.utils import timezone
        now = timezone.now()

        if not self.active:
            return False, "This coupon is no longer active"

        if now < self.valid_from:
            return False, "This coupon is not yet valid"

        if now > self.valid_until:
            return False, "This coupon has expired"

        if self.max_uses and self.current_uses >= self.max_uses:
            return False, "This coupon has reached its usage limit"

        # Check order amount restrictions if total is provided
        if order_total is not None:
            if self.min_order_amount and order_total < self.min_order_amount:
                return False, f"Minimum order amount is ${self.min_order_amount}"

            if self.max_order_amount and order_total > self.max_order_amount:
                return False, f"Maximum order amount is ${self.max_order_amount}"

        return True, "Valid"

    def calculate_discount(self, total):
        """Calculate discount amount for a given total"""
        if self.discount_type == 'percentage':
            return (total * self.discount_value) / 100
        else:
            # Fixed amount discount, but not more than the total
            return min(self.discount_value, total)

    def apply_to_quote(self):
        """Increment usage counter"""
        self.current_uses += 1
        self.save()