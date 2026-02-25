from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """Categorization for packages (e.g., Networking, Media & Entertainment)"""

    # Builder section choices for showroom organization (organized by construction phase)
    PRE_WIRE = 'pre_wire'
    AUTOMATIONS = 'automations'
    ENTERTAINMENT_AUDIO = 'entertainment_audio'
    CUSTOM_SOLUTIONS = 'custom_solutions'

    BUILDER_SECTION_CHOICES = [
        (PRE_WIRE, 'Pre-wire and Networking'),
        (AUTOMATIONS, 'Automations'),
        (ENTERTAINMENT_AUDIO, 'Entertainment & Audio'),
        (CUSTOM_SOLUTIONS, 'Custom Solutions'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True, unique=True)
    description = models.TextField(
        blank=True,
        help_text="Brief description shown in catalog listings"
    )
    details = models.TextField(
        blank=True,
        help_text="Detailed information, specifications, benefits - shown on category detail pages"
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    video = models.FileField(
        upload_to='categories/videos/',
        blank=True,
        null=True,
        help_text="Upload a video file directly (MP4, MOV, etc.). If both video and YouTube URL are provided, uploaded video takes priority."
    )
    youtube_url = models.URLField(
        max_length=500,
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

    def __str__(self):
        return self.name

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

    def has_video(self):
        """Check if category has an uploaded video, legacy YouTube URL, or CategoryVideo entries"""
        return bool(self.video) or bool(self.youtube_url) or self.videos.exists()

    def get_youtube_embed_id(self):
        """Extract YouTube video ID from URL for embedding"""
        if not self.youtube_url:
            return None

        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.youtube_url)
            if match:
                return match.group(1)
        return None

    def get_absolute_url(self):
        """Get URL for category detail view"""
        from django.urls import reverse
        return reverse('products:category_detail', kwargs={'slug': self.slug})


class CategoryImage(models.Model):
    """Gallery images for a category detail page"""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='gallery_images'
    )
    image = models.ImageField(upload_to='categories/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")

    class Meta:
        ordering = ['display_order']
        verbose_name = 'Category Image'
        verbose_name_plural = 'Category Images'

    def __str__(self):
        return f"{self.category.name} - Image {self.pk}"


class CategoryVideo(models.Model):
    """YouTube video embeds for a category detail page"""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    youtube_url = models.URLField(
        max_length=500,
        help_text="YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)"
    )
    title = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")

    class Meta:
        ordering = ['display_order']
        verbose_name = 'Category Video'
        verbose_name_plural = 'Category Videos'

    def __str__(self):
        return f"{self.category.name} - {self.title or 'Video'}"

    def get_youtube_embed_id(self):
        """Extract YouTube video ID from URL for embedding"""
        if not self.youtube_url:
            return None
        import re
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
        return f"{self.category.name} - {self.name}"

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
    FINISHED_PROPERTY = 'finished_property'

    INSTALLATION_PHASE_CHOICES = [
        (FRAMING, 'Framing'),
        (ROUGH_INS, 'Rough-Ins'),
        (INSULATION_DRYWALL, 'Insulation and Drywall'),
        (TRIM_FINISHES, 'Trim and Finishes'),
        (FINISHED_PROPERTY, 'Finished Property'),
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
    VISIBILITY_BOTH = 'both'
    VISIBILITY_CATALOG = 'catalog'
    VISIBILITY_SHOWROOM = 'showroom'
    VISIBILITY_CHOICES = [
        (VISIBILITY_BOTH, 'Both'),
        (VISIBILITY_CATALOG, 'Catalog Only'),
        (VISIBILITY_SHOWROOM, 'Showroom Only'),
    ]
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_BOTH,
        help_text="Where this package appears: catalog, builder showroom, or both"
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
        """Return price with 'Starting at' prefix"""
        return f"Starting at ${self.starting_price:,.2f}"

    def get_custom_label(self):
        """Return custom label for custom packages"""
        if self.is_custom:
            return "Custom design"
        return ""

    def get_absolute_url(self):
        """Get URL for package detail view"""
        return reverse('products:package_detail', kwargs={'slug': self.slug})

    def get_installation_phase_display_value(self):
        """Get human-readable installation phase name"""
        return dict(self.INSTALLATION_PHASE_CHOICES).get(self.installation_phase, '')
