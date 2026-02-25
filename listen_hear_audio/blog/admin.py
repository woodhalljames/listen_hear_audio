from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect, get_object_or_404
from django_summernote.admin import SummernoteModelAdmin

from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(SummernoteModelAdmin):
    list_display = ["title", "author", "published", "notified_at", "created_at", "updated_at"]
    list_filter = ["published", "created_at", "tags", "author"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    summernote_fields = ("body",)
    date_hierarchy = "created_at"
    readonly_fields = ["preview_link", "notified_at", "notify_button", "created_at", "updated_at"]
    actions = ["notify_subscribers"]

    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'featured_image', 'author', 'author_name', 'body')
        }),
        ('Publishing', {
            'fields': ('published', 'tags', 'preview_link')
        }),
        ('Subscriber Notification', {
            'fields': ('notified_at', 'notify_button'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # ── Admin action ──────────────────────────────────────────────────────────

    def notify_subscribers(self, request, queryset):
        from listen_hear_audio.subscribers.tasks import send_blog_post_notification
        sent, skipped = 0, 0
        for post in queryset:
            if not post.published:
                self.message_user(request, f'"{post.title}" is not published — skipped.', level='warning')
                skipped += 1
                continue
            if post.notified_at:
                self.message_user(
                    request,
                    f'"{post.title}" was already notified on {post.notified_at:%b %d, %Y} — skipped.',
                    level='warning',
                )
                skipped += 1
                continue
            send_blog_post_notification.delay(post.pk)
            sent += 1
        if sent:
            self.message_user(
                request,
                f'Notification queued for {sent} post(s). '
                'Emails will be batched (20/batch, ≤50/day) across subscriber list.'
            )
    notify_subscribers.short_description = 'Notify subscribers of selected posts'

    # ── Helpers ───────────────────────────────────────────────────────────────

    def preview_link(self, obj):
        if not obj.pk:
            return "Save post first to preview"
        preview_url = reverse('admin:blog_blogpost_preview', args=[obj.pk])
        return format_html(
            '<a href="{}" class="button" target="_blank" '
            'style="background-color:#417690;color:white;">👁 Preview Post</a>',
            preview_url,
        )
    preview_link.short_description = 'Preview'

    def notify_button(self, obj):
        from listen_hear_audio.subscribers.models import Subscriber
        from listen_hear_audio.subscribers.tasks import BATCH_SIZE, DAILY_SEND_LIMIT
        import math

        if not obj.pk:
            return "Save post first."

        active_count = Subscriber.active().count()

        if obj.notified_at:
            return format_html(
                '<p style="color:#666;">Sent on {}</p>'
                '<p style="color:#666;font-size:0.85em;">{} active subscriber(s)</p>',
                obj.notified_at.strftime('%b %d, %Y at %H:%M'),
                active_count,
            )

        if not obj.published:
            return format_html(
                '<p style="color:#e65c00;">Post must be published before notifying.</p>'
                '<p style="color:#666;font-size:0.85em;">{} active subscriber(s)</p>',
                active_count,
            )

        if active_count == 0:
            return "No active subscribers."

        num_batches = math.ceil(active_count / BATCH_SIZE)
        batches_per_day = max(1, DAILY_SEND_LIMIT // BATCH_SIZE)
        days_needed = math.ceil(num_batches / batches_per_day)

        notify_url = reverse('admin:blog_blogpost_notify', args=[obj.pk])
        return format_html(
            '<p style="font-size:0.85em;color:#666;margin-bottom:6px;">'
            '{} active subscriber(s) &mdash; {} batch(es) over {} day(s) '
            '({} emails/day max)</p>'
            '<a href="{}" class="button" '
            'style="background-color:#417690;color:white;">'
            '&#9993; Send Notification Now</a>',
            active_count, num_batches, days_needed, DAILY_SEND_LIMIT,
            notify_url,
        )
    notify_button.short_description = 'Send to Subscribers'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:post_id>/preview/',
                self.admin_site.admin_view(self.preview_view),
                name='blog_blogpost_preview',
            ),
            path(
                '<int:post_id>/notify/',
                self.admin_site.admin_view(self.notify_view),
                name='blog_blogpost_notify',
            ),
        ]
        return custom_urls + urls

    def preview_view(self, request, post_id):
        post = get_object_or_404(BlogPost, id=post_id)
        return redirect('blog:post_detail', slug=post.slug)

    def notify_view(self, request, post_id):
        from listen_hear_audio.subscribers.tasks import send_blog_post_notification
        post = get_object_or_404(BlogPost, id=post_id)
        if not post.published:
            self.message_user(request, f'"{post.title}" is not published — skipped.', level='warning')
        elif post.notified_at:
            self.message_user(
                request,
                f'"{post.title}" was already notified on {post.notified_at:%b %d, %Y} — skipped.',
                level='warning',
            )
        else:
            send_blog_post_notification.delay(post.pk)
            self.message_user(request, f'Notification queued for "{post.title}".')
        return redirect(reverse('admin:blog_blogpost_change', args=[post_id]))

    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)
