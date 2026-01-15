from django.contrib import admin
from django.utils.html import format_html
from .models import GalleryImage


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    """Admin for gallery images - simple one-at-a-time upload"""

    list_display = ('image_thumbnail', 'alt_text', 'tag_list', 'uploaded_at')
    list_filter = ('tags', 'uploaded_at')
    search_fields = ('alt_text', 'caption')
    readonly_fields = ('uploaded_at', 'updated_at', 'image_preview')

    fieldsets = (
        ('Image', {
            'fields': ('image', 'image_preview')
        }),
        ('SEO & Marketing (Optional)', {
            'fields': ('alt_text', 'caption'),
            'classes': ('collapse',),
            'description': 'These fields are optional. Add them later for better SEO and marketing.'
        }),
        ('Organization', {
            'fields': ('tags', 'order')
        }),
        ('Metadata', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_thumbnail(self, obj):
        """Show small thumbnail in list view"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: auto; object-fit: cover;" />',
                obj.image.url
            )
        return "-"
    image_thumbnail.short_description = 'Preview'

    def image_preview(self, obj):
        """Show larger preview in edit form"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 500px; max-height: 500px; object-fit: contain;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = 'Image Preview'

    def tag_list(self, obj):
        """Show tags in list view"""
        return ", ".join(o.name for o in obj.tags.all())
    tag_list.short_description = 'Tags'
