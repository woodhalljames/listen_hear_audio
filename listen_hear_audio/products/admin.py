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