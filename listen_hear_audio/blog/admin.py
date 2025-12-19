from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect, get_object_or_404
from django_summernote.admin import SummernoteModelAdmin

from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(SummernoteModelAdmin):
    list_display = ["title", "author", "published", "created_at", "updated_at"]
    list_filter = ["published", "created_at", "tags", "author"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    summernote_fields = ("body",)
    date_hierarchy = "created_at"
    readonly_fields = ["preview_link", "created_at", "updated_at"]

    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'featured_image', 'author', 'body')
        }),
        ('Publishing', {
            'fields': ('published', 'tags', 'preview_link')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def preview_link(self, obj):
        if not obj.pk:
            return "Save post first to preview"

        preview_url = reverse('admin:blog_blogpost_preview', args=[obj.pk])
        return format_html(
            '<a href="{}" class="button" target="_blank" style="background-color: #417690; color: white;">👁 Preview Post</a>',
            preview_url
        )
    preview_link.short_description = 'Preview'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:post_id>/preview/',
                self.admin_site.admin_view(self.preview_view),
                name='blog_blogpost_preview',
            ),
        ]
        return custom_urls + urls

    def preview_view(self, request, post_id):
        """Preview blog post (works for both published and unpublished)"""
        post = get_object_or_404(BlogPost, id=post_id)
        # Redirect to the post detail view
        return redirect('blog:post_detail', slug=post.slug)

    def save_model(self, request, obj, form, change):
        # Auto-set author to current user if not set
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)
