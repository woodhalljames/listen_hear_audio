from django.contrib import admin
from django import forms
from django.contrib import messages
from .models import PropertyType, Category, SubCategory, Package, CSVImport
from .csv_import import import_packages_from_csv

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
    list_display = ['name', 'property_type', 'builder_section', 'show_in_catalog', 'display_order', 'is_active', 'has_video', 'has_subcategories', 'has_packages']
    list_editable = ['display_order', 'is_active', 'show_in_catalog']
    list_filter = ['property_type', 'builder_section', 'show_in_catalog', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['property_type', 'display_order', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('property_type', 'name', 'slug', 'description', 'details', 'image')
        }),
        ('Video Content', {
            'fields': ('video', 'youtube_url'),
            'description': 'Add a video to showcase this category. You can upload a video file directly or provide a YouTube URL. Uploaded videos take priority.'
        }),
        ('Builder Showroom', {
            'fields': ('builder_section',),
            'description': 'Configure how this category appears in the builder showroom. Select a builder section.'
        }),
        ('Visibility', {
            'fields': ('show_in_catalog', 'display_order', 'is_active'),
            'description': 'Control where this category is shown. Uncheck "Show in catalog" for builder-only items.'
        }),
    )

    def has_video(self, obj):
        return obj.has_video()
    has_video.boolean = True
    has_video.short_description = 'Video'
    
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
    search_fields = ['name', 'description', 'details']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['category', 'display_order', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'slug', 'description', 'details', 'image')
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active')
        }),
    )

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
    list_display = ['name', 'category', 'subcategory', 'installation_phase', 'starting_price', 'is_custom', 'is_featured', 'is_active', 'display_order']
    list_editable = ['display_order', 'is_active', 'is_featured']
    list_filter = ['installation_phase', 'category__property_type', 'category', 'subcategory', 'is_custom', 'is_featured', 'is_active']
    search_fields = ['name', 'short_description', 'features']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['installation_phase', 'category', 'subcategory', 'display_order', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'subcategory', 'installation_phase', 'name', 'slug')
        }),
        ('Content', {
            'fields': ('short_description', 'features'),
            'description': 'Short description appears on package cards. Features are displayed as bullet points.'
        }),
        ('Pricing & Options', {
            'fields': ('starting_price', 'is_custom')
        }),
        ('Display Settings', {
            'fields': ('image', 'display_order', 'is_featured', 'is_active')
        }),
    )


@admin.register(CSVImport)
class CSVImportAdmin(admin.ModelAdmin):
    """Admin for CSV imports with upload history"""
    list_display = ['uploaded_at', 'uploaded_by', 'packages_created', 'packages_updated', 'packages_skipped', 'property_types_detected', 'has_errors']
    list_filter = ['uploaded_at']
    readonly_fields = ['uploaded_by', 'uploaded_at', 'packages_created', 'packages_updated', 'packages_skipped', 'property_types_detected', 'error_log']

    fieldsets = (
        ('Upload CSV File', {
            'fields': ('csv_file',),
            'description': 'Upload a CSV file with columns: category, type, item, labor_Phase_Name, Unit Price. Property types are auto-detected from category names.'
        }),
        ('Import Results', {
            'fields': ('uploaded_by', 'uploaded_at', 'packages_created', 'packages_updated', 'packages_skipped', 'property_types_detected', 'error_log'),
            'classes': ('collapse',)
        }),
    )

    def has_errors(self, obj):
        return bool(obj.error_log)
    has_errors.boolean = True
    has_errors.short_description = 'Errors?'

    def save_model(self, request, obj, form, change):
        """Process CSV import when saved"""
        # Set the user
        if not obj.uploaded_by:
            obj.uploaded_by = request.user

        # Save first to get the file
        super().save_model(request, obj, form, change)

        # Process the CSV import
        try:
            stats = import_packages_from_csv(
                obj.csv_file.path,
                overwrite=False
            )

            # Update statistics
            obj.packages_created = stats['created']
            obj.packages_updated = stats['updated']
            obj.packages_skipped = stats['skipped']

            # Format property types detected
            if stats.get('property_types'):
                property_types_str = ', '.join([f"{ptype} ({count})" for ptype, count in stats['property_types'].items()])
                obj.property_types_detected = property_types_str

            obj.error_log = '\n'.join(stats['errors']) if stats['errors'] else ''
            obj.save()

            # Show success message
            property_types_msg = f" Property types: {obj.property_types_detected}" if obj.property_types_detected else ""
            messages.success(
                request,
                f"CSV import completed! Created: {stats['created']}, Updated: {stats['updated']}, Skipped: {stats['skipped']}.{property_types_msg}"
            )

            if stats['errors']:
                messages.warning(request, f"{len(stats['errors'])} errors occurred. Check error log below.")

        except Exception as e:
            obj.error_log = f"Import failed: {str(e)}"
            obj.save()
            messages.error(request, f"CSV import failed: {str(e)}")