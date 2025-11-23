from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import PropertyType, Category, SubCategory, Package


class CatalogView(ListView):
    """Single-page view showing all property types, categories, and packages"""
    model = PropertyType
    template_name = 'products/catalog.html'
    context_object_name = 'property_types'
    
    def get_queryset(self):
        """Get all active property types with related data"""
        return PropertyType.objects.filter(
            is_active=True
        ).prefetch_related(
            'categories__subcategories__packages',
            'categories__packages'
        ).order_by('display_order')


class PackageDetailView(DetailView):
    """Detail view for a single package"""
    model = Package
    template_name = 'products/package_detail.html'
    context_object_name = 'package'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """Only show active packages"""
        return Package.objects.filter(is_active=True).select_related(
            'category__property_type',
            'subcategory'
        )