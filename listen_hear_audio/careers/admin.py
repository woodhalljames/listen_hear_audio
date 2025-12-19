from django.contrib import admin
from django.utils.html import format_html
from django_summernote.admin import SummernoteModelAdmin

from .models import JobPosting, JobApplication, CareersPageConfig


@admin.register(CareersPageConfig)
class CareersPageConfigAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Page Content', {
            'fields': ('introduction',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Only allow one configuration instance
        return not CareersPageConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the configuration
        return False


@admin.register(JobPosting)
class JobPostingAdmin(SummernoteModelAdmin):
    list_display = ["title", "active", "application_count", "created_at", "updated_at"]
    list_filter = ["active", "created_at"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    summernote_fields = ("body",)
    date_hierarchy = "created_at"

    def application_count(self, obj):
        count = obj.applications.count()
        if count > 0:
            return format_html('<strong>{}</strong>', count)
        return count
    application_count.short_description = 'Applications'


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'job_posting', 'email', 'phone', 'resume_link', 'created_at']
    list_filter = ['job_posting', 'created_at']
    search_fields = ['name', 'email', 'phone', 'job_posting__title']
    readonly_fields = ['created_at', 'resume_link']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Job Information', {
            'fields': ('job_posting',)
        }),
        ('Applicant Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Application Materials', {
            'fields': ('cover_letter', 'resume', 'resume_link')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def resume_link(self, obj):
        if obj.resume:
            return format_html(
                '<a href="{}" target="_blank" class="button">📄 Download Resume</a>',
                obj.resume.url
            )
        return '-'
    resume_link.short_description = 'Resume File'
