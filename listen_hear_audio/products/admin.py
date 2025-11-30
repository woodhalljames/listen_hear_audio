from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from .models import PropertyType, Category, SubCategory, Package, Property, PurchasedPackage, PropertyNote


@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_order', 'is_active', 'created_at']
    list_editable = ['display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'property_type', 'display_order', 'is_active', 'has_subcategories', 'has_packages']
    list_editable = ['display_order', 'is_active']
    list_filter = ['property_type', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['property_type', 'display_order', 'name']
    
    def has_subcategories(self, obj):
        return obj.has_subcategories()
    has_subcategories.boolean = True
    has_subcategories.short_description = 'Has SubCats'
    
    def has_packages(self, obj):
        return obj.has_packages()
    has_packages.boolean = True
    has_packages.short_description = 'Has Packages'


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'display_order', 'is_active', 'package_count']
    list_editable = ['display_order', 'is_active']
    list_filter = ['category__property_type', 'category', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['category', 'display_order', 'name']
    
    def package_count(self, obj):
        return obj.packages.count()
    package_count.short_description = 'Packages'


class PackageAdminForm(forms.ModelForm):
    """Custom form for Package admin with improved field displays"""
    
    short_description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'cols': 80,
            'style': 'width: 100%;'
        }),
        max_length=300,
        required=False,
        help_text='Brief description shown on package card (max 300 characters)'
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'cols': 80,
            'style': 'width: 100%;'
        }),
        required=False,
        help_text='Full description shown on detail view'
    )
    
    features = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 8,
            'cols': 80,
            'style': 'width: 100%;'
        }),
        required=False,
        help_text='Enter features as bullet points, one per line'
    )
    
    class Meta:
        model = Package
        fields = '__all__'


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    form = PackageAdminForm
    list_display = ['name', 'category', 'subcategory', 'starting_price', 'is_custom', 'is_featured', 'is_active', 'display_order']
    list_editable = ['display_order', 'is_active', 'is_featured']
    list_filter = ['category__property_type', 'category', 'subcategory', 'is_custom', 'is_featured', 'is_active']
    search_fields = ['name', 'description', 'short_description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['category', 'subcategory', 'display_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'subcategory', 'name', 'slug')
        }),
        ('Descriptions', {
            'fields': ('short_description', 'description', 'features'),
            'description': 'Use short_description for card display, description for detail page, and features as a bullet list'
        }),
        ('Pricing & Options', {
            'fields': ('starting_price', 'is_custom')
        }),
        ('Display Settings', {
            'fields': ('image', 'display_order', 'is_featured', 'is_active')
        }),
    )


# Builder Package Management Admins


class PurchasedPackageInline(admin.TabularInline):
    model = PurchasedPackage
    extra = 0
    fields = ['package_name', 'quantity', 'status', 'requested_install_date', 'confirmed_install_date']
    readonly_fields = []
    can_delete = True


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'address_short', 'property_type', 'builder_list', 'package_count', 'updated_at']
    list_filter = ['property_type', 'created_at']
    search_fields = ['name', 'address']
    filter_horizontal = ['builders']
    inlines = [PurchasedPackageInline]
    readonly_fields = ['created_at', 'updated_at', 'quote_request_link']
    
    fieldsets = (
        ('Property Information', {
            'fields': ('name', 'address', 'property_type')
        }),
        ('Management', {
            'fields': ('builders', 'quote_request_link')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def address_short(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_short.short_description = 'Address'
    
    def builder_list(self, obj):
        builders = obj.builders.all()
        if builders.exists():
            return ', '.join([b.name or b.email for b in builders[:3]])
        return '-'
    builder_list.short_description = 'Builders'
    
    def package_count(self, obj):
        return obj.packages.count()
    package_count.short_description = 'Packages'
    
    def quote_request_link(self, obj):
        if obj.quote_request:
            url = reverse('admin:quotes_quoterequest_change', args=[obj.quote_request.pk])
            return format_html('<a href="{}">{}</a>', url, obj.quote_request.quote_number)
        return '-'
    quote_request_link.short_description = 'Original Quote'


@admin.register(PurchasedPackage)
class PurchasedPackageAdmin(admin.ModelAdmin):
    list_display = [
        'package_name',
        'property_link',
        'quantity',
        'status_badge',
        'requested_install_date',
        'confirmed_install_date',
        'updated_at'
    ]
    list_filter = ['status', 'property', 'requested_install_date', 'confirmed_install_date']
    search_fields = ['package_name', 'property__name', 'property__address']
    date_hierarchy = 'requested_install_date'
    readonly_fields = ['created_at', 'updated_at']
    
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
    
    actions = ['confirm_date', 'mark_in_progress', 'mark_completed']
    
    def property_link(self, obj):
        url = reverse('admin:products_property_change', args=[obj.property.pk])
        return format_html('<a href="{}">{}</a>', url, obj.property.name)
    property_link.short_description = 'Property'
    
    def status_badge(self, obj):
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
    
    def confirm_date(self, request, queryset):
        """Confirm requested installation dates"""
        updated = 0
        for package in queryset.filter(status='date_requested'):
            if package.requested_install_date:
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
                updated += 1
        
        self.message_user(request, f'{updated} package(s) confirmed.')
    confirm_date.short_description = "Confirm requested installation dates"
    
    def mark_in_progress(self, request, queryset):
        """Mark packages as in progress"""
        updated = queryset.filter(status='scheduled').update(status='in_progress')
        for package in queryset.filter(status='in_progress'):
            PropertyNote.objects.create(
                property=package.property,
                package=package,
                note_type='status_change',
                message=f"Installation started for {package.package_name}",
                created_by=request.user
            )
        self.message_user(request, f'{updated} package(s) marked as in progress.')
    mark_in_progress.short_description = "Mark as In Progress"
    
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
    mark_completed.short_description = "Mark as Completed"


@admin.register(PropertyNote)
class PropertyNoteAdmin(admin.ModelAdmin):
    list_display = ['property', 'note_type', 'message_short', 'created_by', 'created_at']
    list_filter = ['note_type', 'created_at', 'property']
    search_fields = ['property__name', 'message']
    readonly_fields = ['created_at']
    
    def message_short(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_short.short_description = 'Message'