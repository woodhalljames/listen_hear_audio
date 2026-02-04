from django.contrib import admin
from django import forms
from .models import PropertyType, Category, SubCategory, Package

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
    list_display = ['name', 'category', 'subcategory', 'installation_phase', 'starting_price', 'is_custom', 'catalog_only', 'is_featured', 'is_active', 'display_order']
    list_editable = ['display_order', 'is_active', 'is_featured', 'catalog_only']
    list_filter = ['installation_phase', 'category__property_type', 'category', 'subcategory', 'is_custom', 'catalog_only', 'is_featured', 'is_active']
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
            'fields': ('image', 'display_order', 'catalog_only', 'is_featured', 'is_active'),
            'description': 'Catalog only packages will only show in the main catalog, not the builder showroom.'
        }),
    )


