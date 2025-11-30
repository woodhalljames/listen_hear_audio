from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify


class PropertyType(models.Model):
    """Top-level property type categorization (Residential, Commercial, Industrial)"""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='property_types/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Property Type'
        verbose_name_plural = 'Property Types'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Category(models.Model):
    """Second-level categorization (e.g., Networking, Media & Entertainment)"""
    
    property_type = models.ForeignKey(
        PropertyType, 
        on_delete=models.CASCADE, 
        related_name='categories'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        unique_together = ['property_type', 'slug']

    def __str__(self):
        return f"{self.property_type.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def has_subcategories(self):
        """Check if this category has any subcategories"""
        return self.subcategories.exists()

    def has_packages(self):
        """Check if this category has packages directly attached"""
        return self.packages.exists()


class SubCategory(models.Model):
    """Optional third-level categorization (e.g., Audio, TV & Display under Media & Entertainment)"""
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='subcategories'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='subcategories/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Sub-Category'
        verbose_name_plural = 'Sub-Categories'
        unique_together = ['category', 'slug']

    def __str__(self):
        return f"{self.category.property_type.name} - {self.category.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Package(models.Model):
    """The actual packages/products that customers add to their quote"""
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='packages'
    )
    subcategory = models.ForeignKey(
        SubCategory, 
        on_delete=models.CASCADE, 
        related_name='packages',
        blank=True,
        null=True,
        help_text="Optional - only needed if category uses subcategories"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    short_description = models.CharField(
        max_length=300, 
        blank=True,
        help_text="Brief description shown on package card"
    )
    description = models.TextField(
        blank=True,
        help_text="Full description shown on detail view"
    )
    features = models.TextField(
        blank=True,
        help_text="Enter features as bullet points, one per line"
    )
    starting_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Starting price for this package"
    )
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    is_custom = models.BooleanField(
        default=False,
        help_text="Mark as true for custom/quote-only packages"
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'

    def __str__(self):
        if self.subcategory:
            return f"{self.subcategory.name} - {self.name}"
        return f"{self.category.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_features_list(self):
        """Return features as a list for template rendering"""
        if self.features:
            return [f.strip() for f in self.features.split('\n') if f.strip()]
        return []

    def get_price_display(self):
        """Return price with 'Starting at' or 'Contact for Pricing' for custom packages"""
        if self.is_custom:
            return "Contact for Pricing"
        return f"Starting at ${self.starting_price:,.2f}"

    def get_absolute_url(self):
        """Get URL for package detail view"""
        return reverse('products:package_detail', kwargs={'slug': self.slug})


# New models for builder package management


class Property(models.Model):
    """Property/project that builders manage"""
    
    name = models.CharField(max_length=200, help_text="Property name or identifier")
    address = models.TextField(help_text="Full property address")
    property_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., Residential, Commercial"
    )
    builders = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='managed_properties',
        limit_choices_to={'is_builder': True},
        help_text="Builders assigned to manage this property"
    )
    quote_request = models.ForeignKey(
        'quotes.QuoteRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='properties',
        help_text="Original quote request that created this property"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.address[:50]}"

    def get_absolute_url(self):
        return reverse('users:builder_property_detail', kwargs={'pk': self.pk})

    def get_package_status_summary(self):
        """Get summary of package statuses"""
        packages = self.packages.all()
        return {
            'total': packages.count(),
            'pending': packages.filter(status='pending').count(),
            'date_requested': packages.filter(status='date_requested').count(),
            'scheduled': packages.filter(status='scheduled').count(),
            'in_progress': packages.filter(status='in_progress').count(),
            'completed': packages.filter(status='completed').count(),
        }


class PurchasedPackage(models.Model):
    """Package assigned to a property for installation"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('date_requested', 'Date Requested'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='packages'
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Snapshot of package details
    package_name = models.CharField(max_length=200)
    package_description = models.TextField(blank=True)
    price_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    
    # Status and dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_install_date = models.DateField(null=True, blank=True)
    confirmed_install_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    
    # Notes
    builder_notes = models.TextField(blank=True, help_text="Notes from builder")
    company_notes = models.TextField(blank=True, help_text="Notes from company")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Purchased Package'
        verbose_name_plural = 'Purchased Packages'
        ordering = ['status', 'requested_install_date', 'created_at']

    def __str__(self):
        return f"{self.package_name} - {self.property.name} ({self.get_status_display()})"

    def get_subtotal(self):
        """Calculate subtotal"""
        if self.price_snapshot:
            return self.price_snapshot * self.quantity
        return 0


class PropertyNote(models.Model):
    """Activity timeline notes for properties"""
    
    NOTE_TYPE_CHOICES = [
        ('general', 'General Note'),
        ('date_request', 'Date Request'),
        ('date_confirmation', 'Date Confirmation'),
        ('date_denial', 'Date Denial'),
        ('status_change', 'Status Change'),
    ]
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    package = models.ForeignKey(
        PurchasedPackage,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Associated package if note is package-specific"
    )
    note_type = models.CharField(max_length=30, choices=NOTE_TYPE_CHOICES)
    message = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Property Note'
        verbose_name_plural = 'Property Notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_note_type_display()} - {self.property.name} - {self.created_at.strftime('%Y-%m-%d')}"