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
        # Get property types that have active categories (with or without show_in_catalog set)
        return PropertyType.objects.filter(
            is_active=True,
            categories__is_active=True
        ).distinct().prefetch_related(
            'categories__subcategories__packages',
            'categories__packages'
        ).order_by('display_order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Filter property types to include categories visible in catalog
        # Default to showing all if show_in_catalog is not set (empty/null) or is True
        property_types = context['property_types']
        for property_type in property_types:
            # Show categories where show_in_catalog=True OR show_in_catalog is unset
            # This ensures backward compatibility with categories that existed before the field was added
            visible_categories = property_type.categories.filter(
                is_active=True
            ).filter(
                show_in_catalog=True
            )

            property_type.visible_categories = visible_categories.order_by('display_order', 'name')
        return context


class CategoryDetailView(DetailView):
    """Detail view for a single category"""
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """Only show active categories"""
        return Category.objects.filter(is_active=True).select_related('property_type')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add count of packages for this category
        context['package_count'] = self.object.packages.filter(is_active=True).count()
        return context


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