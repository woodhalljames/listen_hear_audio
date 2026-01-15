from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager


class GalleryImage(models.Model):
    """Gallery image with optional SEO and marketing fields"""

    # Core fields
    image = models.ImageField(
        upload_to='gallery/',
        help_text="Upload gallery image (any size, will auto-fit in masonry grid)"
    )

    # Optional SEO/Marketing fields
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="SEO: Describe the image for search engines and accessibility"
    )
    caption = models.TextField(
        blank=True,
        help_text="Optional caption or description for marketing"
    )

    # Tags for filtering
    tags = TaggableManager(
        blank=True,
        help_text="Tags: living room, lighting, outdoor, theater, pool, etc."
    )

    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Manual ordering (0 = use upload date)"
    )

    class Meta:
        ordering = ['-uploaded_at']  # Chronological by default
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery Images'

    def __str__(self):
        return f"Gallery Image {self.id} - {self.uploaded_at.strftime('%Y-%m-%d')}"

    def get_absolute_url(self):
        return reverse('gallery:gallery')
