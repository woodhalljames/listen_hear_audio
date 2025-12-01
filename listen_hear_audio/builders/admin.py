from django.contrib import admin
from .models import Property, PurchasedPackage, PropertyNote


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
    list_display = ('name', 'address', 'property_type', 'get_builders', 'updated_at', 'created_at')
    list_filter = ('property_type', 'created_at', 'updated_at')
    search_fields = ('name', 'address')
    filter_horizontal = ('builders',)
    inlines = [PurchasedPackageInline, PropertyNoteInline]
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Property Information', {
            'fields': ('name', 'address', 'property_type')
        }),
        ('Builders & Quote', {
            'fields': ('builders', 'quote_request')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_builders(self, obj):
        """Display builder names"""
        return ", ".join([builder.email for builder in obj.builders.all()])
    get_builders.short_description = 'Builders'


@admin.register(PurchasedPackage)
class PurchasedPackageAdmin(admin.ModelAdmin):
    """Admin for PurchasedPackage model"""
    list_display = ('package_name', 'property', 'status', 'requested_install_date', 'confirmed_install_date', 'updated_at')
    list_filter = ('status', 'created_at', 'requested_install_date', 'confirmed_install_date')
    search_fields = ('package_name', 'property__name', 'property__address')
    readonly_fields = ('created_at', 'updated_at', 'package_name', 'package_description', 'price_snapshot')

    fieldsets = (
        ('Package Information', {
            'fields': ('property', 'package', 'package_name', 'package_description', 'price_snapshot', 'quantity')
        }),
        ('Status & Dates', {
            'fields': ('status', 'requested_install_date', 'confirmed_install_date', 'completion_date')
        }),
        ('Notes', {
            'fields': ('builder_notes', 'company_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

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
                # Update status to scheduled
                obj.status = 'scheduled'
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
