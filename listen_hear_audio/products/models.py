from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()


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

    # Builder section choices for showroom organization
    NETWORK_AUTOMATION = 'network_automation'
    SECURITY = 'security'
    AUDIO = 'audio'
    ENTERTAINMENT = 'entertainment'

    BUILDER_SECTION_CHOICES = [
        (NETWORK_AUTOMATION, 'Network & Automation'),
        (SECURITY, 'Security'),
        (AUDIO, 'Audio'),
        (ENTERTAINMENT, 'Entertainment'),
    ]

    property_type = models.ForeignKey(
        PropertyType,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField(
        blank=True,
        help_text="Brief description shown in catalog listings"
    )
    details = models.TextField(
        blank=True,
        help_text="Detailed information, specifications, benefits - shown on category detail pages"
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    youtube_url = models.URLField(
        blank=True,
        help_text="YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID or https://youtu.be/VIDEO_ID)"
    )
    builder_section = models.CharField(
        max_length=50,
        choices=BUILDER_SECTION_CHOICES,
        blank=True,
        help_text="Section to display in builder showroom (e.g., Network & Automation, Security, etc.)"
    )
    show_in_catalog = models.BooleanField(
        default=True,
        help_text="Show this category in the regular catalog (uncheck for builder-only items)"
    )
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

    def get_youtube_embed_id(self):
        """Extract YouTube video ID from URL for embedding"""
        if not self.youtube_url:
            return None

        import re
        # Handle various YouTube URL formats
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.youtube_url)
            if match:
                return match.group(1)
        return None


class SubCategory(models.Model):
    """Optional third-level categorization (e.g., Audio, TV & Display under Media & Entertainment)"""
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='subcategories'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField(
        blank=True,
        help_text="Brief description shown in catalog listings"
    )
    details = models.TextField(
        blank=True,
        help_text="Detailed information, specifications, benefits - shown on subcategory pages"
    )
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

    # Installation phase choices - aligned with construction workflow
    FRAMING = 'framing'
    ROUGH_INS = 'rough_ins'
    INSULATION_DRYWALL = 'insulation_drywall'
    TRIM_FINISHES = 'trim_finishes'

    INSTALLATION_PHASE_CHOICES = [
        (FRAMING, 'Framing'),
        (ROUGH_INS, 'Rough-Ins'),
        (INSULATION_DRYWALL, 'Insulation and Drywall'),
        (TRIM_FINISHES, 'Trim and Finishes'),
    ]

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
    installation_phase = models.CharField(
        max_length=50,
        choices=INSTALLATION_PHASE_CHOICES,
        default=ROUGH_INS,
        help_text="Construction phase when this package is installed"
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

    def get_installation_phase_display_value(self):
        """Get human-readable installation phase name"""
        return dict(self.INSTALLATION_PHASE_CHOICES).get(self.installation_phase, '')


class CSVImport(models.Model):
    """Track CSV imports for audit trail"""

    csv_file = models.FileField(upload_to='csv_imports/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Import statistics
    packages_created = models.IntegerField(default=0)
    packages_updated = models.IntegerField(default=0)
    packages_skipped = models.IntegerField(default=0)
    property_types_detected = models.CharField(max_length=500, blank=True, help_text="Auto-detected property types")
    error_log = models.TextField(blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'CSV Import'
        verbose_name_plural = 'CSV Imports'

    def __str__(self):
        return f"CSV Import {self.uploaded_at.strftime('%Y-%m-%d %H:%M')} - {self.packages_created} created"


