from django.contrib import admin
from .models import Property, PurchasedPackage, PropertyNote
from .tasks import send_property_creation_email, send_date_confirmation_email


class PurchasedPackageInline(admin.TabularInline):
    """Inline admin for purchased packages"""
    model = PurchasedPackage
    extra = 0
    fields = ('package_name', 'status', 'requested_install_date', 'confirmed_install_date', 'builder_notes', 'company_notes')
    readonly_fields = ('package_name',)


class PropertyNoteInline(admin.TabularInline):
    """Inline admin for property notes"""
    model = PropertyNote
    extra = 0
    fields = ('note_type', 'message', 'created_by', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """Admin for Property model"""
    list_display = ('name', 'address_short', 'property_type', 'get_builders', 'package_count', 'updated_at', 'created_at')
    list_filter = ('property_type', 'created_at', 'updated_at')
    search_fields = ('name', 'address')
    filter_horizontal = ('builders',)
    inlines = [PurchasedPackageInline, PropertyNoteInline]
    readonly_fields = ('created_at', 'updated_at', 'quote_link')

    fieldsets = (
        ('Property Information', {
            'fields': ('name', 'address', 'property_type')
        }),
        ('Builders & Quote', {
            'fields': ('builders', 'quote_request', 'quote_link'),
            'description': 'Select one or more builders to manage this property. Builders will see this property in their dashboard and can request installation dates.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_builders(self, obj):
        """Display builder names"""
        builders = obj.builders.all()
        if builders:
            return ", ".join([b.company_name or b.email for b in builders])
        return "-"
    get_builders.short_description = 'Assigned Builders'

    def address_short(self, obj):
        """Show shortened address"""
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_short.short_description = 'Address'

    def package_count(self, obj):
        """Show number of packages"""
        return obj.packages.count()
    package_count.short_description = 'Packages'

    def quote_link(self, obj):
        """Show link to original quote"""
        if obj.quote_request:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse('admin:quotes_quoterequest_change', args=[obj.quote_request.pk])
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.quote_request.quote_number)
        return "-"
    quote_link.short_description = 'Original Quote'

    def save_model(self, request, obj, form, change):
        """Trigger email notification when property is created"""
        is_new = not change
        super().save_model(request, obj, form, change)

        # If this is a new property and it has builders assigned, send notification
        if is_new and obj.builders.exists():
            send_property_creation_email.delay(obj.id)


@admin.register(PurchasedPackage)
class PurchasedPackageAdmin(admin.ModelAdmin):
    """Admin for PurchasedPackage model"""
    list_display = ('package_name', 'property_link', 'status_badge', 'requested_install_date', 'confirmed_install_date', 'updated_at')
    list_filter = ('status', 'created_at', 'requested_install_date', 'confirmed_install_date')
    search_fields = ('package_name', 'property__name', 'property__address')
    readonly_fields = ('created_at', 'updated_at', 'package_name', 'package_description', 'price_snapshot')
    actions = ['confirm_requested_dates', 'mark_in_progress', 'mark_completed']

    fieldsets = (
        ('Package Information', {
            'fields': ('property', 'package', 'package_name', 'package_description', 'price_snapshot', 'quantity')
        }),
        ('Status & Dates', {
            'fields': ('status', 'requested_install_date', 'confirmed_install_date', 'completion_date'),
            'description': 'Confirm installation dates requested by builders. When you confirm a date, the builder will be notified and the status will update to "Scheduled".'
        }),
        ('Notes', {
            'fields': ('builder_notes', 'company_notes'),
            'description': 'Builder notes are visible to builders. Company notes are internal only.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def property_link(self, obj):
        """Link to property"""
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:builders_property_change', args=[obj.property.pk])
        return format_html('<a href="{}">{}</a>', url, obj.property.name)
    property_link.short_description = 'Property'

    def status_badge(self, obj):
        """Colored status badge"""
        from django.utils.html import format_html
        colors = {
            'pending': '#6c757d',
            'date_requested': '#ffc107',
            'scheduled': '#0d6efd',
            'in_progress': '#6f42c1',
            'completed': '#198754',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def confirm_requested_dates(self, request, queryset):
        """Confirm the requested installation dates"""
        updated = 0
        for package in queryset.filter(status='date_requested', requested_install_date__isnull=False):
            package.confirmed_install_date = package.requested_install_date
            package.status = 'scheduled'
            package.save()

            # Create note
            PropertyNote.objects.create(
                property=package.property,
                package=package,
                note_type='date_confirmation',
                message=f"Installation date confirmed for {package.confirmed_install_date}",
                created_by=request.user
            )

            # Send email notification to all parties
            send_date_confirmation_email.delay(package.id)

            updated += 1

        self.message_user(request, f'{updated} installation date(s) confirmed. Email notifications sent.')
    confirm_requested_dates.short_description = 'Confirm requested installation dates'

    def mark_in_progress(self, request, queryset):
        """Mark packages as in progress"""
        updated = 0
        for package in queryset.filter(status='scheduled'):
            package.status = 'in_progress'
            package.save()

            PropertyNote.objects.create(
                property=package.property,
                package=package,
                note_type='status_change',
                message=f"Installation started for {package.package_name}",
                created_by=request.user
            )
            updated += 1

        self.message_user(request, f'{updated} package(s) marked as in progress.')
    mark_in_progress.short_description = 'Mark as In Progress'

    def mark_completed(self, request, queryset):
        """Mark packages as completed"""
        from django.utils import timezone
        updated = 0
        for package in queryset.filter(status='in_progress'):
            package.status = 'completed'
            if not package.completion_date:
                package.completion_date = timezone.now().date()
            package.save()

            PropertyNote.objects.create(
                property=package.property,
                package=package,
                note_type='status_change',
                message=f"Installation completed for {package.package_name}",
                created_by=request.user
            )
            updated += 1

        self.message_user(request, f'{updated} package(s) marked as completed.')
    mark_completed.short_description = 'Mark as Completed'

    def save_model(self, request, obj, form, change):
        """Auto-create notes when dates are confirmed or denied"""
        if change:
            # Check if confirmed_install_date was changed
            original = PurchasedPackage.objects.get(pk=obj.pk)
            if original.confirmed_install_date != obj.confirmed_install_date and obj.confirmed_install_date:
                # Create a confirmation note
                PropertyNote.objects.create(
                    property=obj.property,
                    package=obj,
                    note_type='date_confirmation',
                    message=f"Installation date confirmed: {obj.confirmed_install_date}",
                    created_by=request.user
                )
                # Update status to scheduled if not already
                if obj.status == 'date_requested':
                    obj.status = 'scheduled'

                # Send email notification to all parties
                send_date_confirmation_email.delay(obj.id)

        super().save_model(request, obj, form, change)


@admin.register(PropertyNote)
class PropertyNoteAdmin(admin.ModelAdmin):
    """Admin for PropertyNote model"""
    list_display = ('property', 'note_type', 'message_preview', 'created_by', 'created_at')
    list_filter = ('note_type', 'created_at')
    search_fields = ('property__name', 'message')
    readonly_fields = ('created_at',)

    def message_preview(self, obj):
        """Show first 50 characters of message"""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'
