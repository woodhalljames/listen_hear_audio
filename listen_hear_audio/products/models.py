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


