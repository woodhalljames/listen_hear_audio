from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Prefetch
from .models import PropertyType, Category, CategoryImage, CategoryVideo, SubCategory, Package


class CatalogView(ListView):
    """Single-page view showing all property types, categories, and packages"""
    model = PropertyType
    template_name = 'products/catalog.html'
    context_object_name = 'property_types'

    def get_queryset(self):
        """Get all active property types with related data"""
        # Get property types that have active categories (with or without show_in_catalog set)
        catalog_packages = Package.objects.filter(
            is_active=True, visibility__in=['both', 'catalog']
        )
        return PropertyType.objects.filter(
            is_active=True,
            categories__is_active=True
        ).distinct().prefetch_related(
            Prefetch(
                'categories__subcategories__packages',
                queryset=catalog_packages,
            ),
            Prefetch(
                'categories__packages',
                queryset=catalog_packages,
            ),
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
        catalog_packages = Package.objects.filter(
            is_active=True, visibility__in=['both', 'catalog']
        )
        return Category.objects.filter(is_active=True).select_related(
            'property_type'
        ).prefetch_related(
            'gallery_images',
            'videos',
            Prefetch(
                'subcategories',
                queryset=SubCategory.objects.filter(is_active=True).prefetch_related(
                    Prefetch('packages', queryset=catalog_packages)
                )
            ),
            Prefetch(
                'packages',
                queryset=catalog_packages,
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        packages = category.packages.filter(is_active=True, visibility__in=['both', 'catalog'])
        context['package_count'] = packages.count()
        context['packages'] = packages
        context['gallery_images'] = category.gallery_images.all()
        context['category_videos'] = category.videos.all()

        # Group packages by subcategory if applicable
        if category.has_subcategories():
            subcategories = category.subcategories.filter(is_active=True)
            grouped = []
            for sub in subcategories:
                sub_packages = packages.filter(subcategory=sub)
                if sub_packages.exists():
                    grouped.append({'subcategory': sub, 'packages': sub_packages})
            # Also get packages with no subcategory
            unsorted = packages.filter(subcategory__isnull=True)
            if unsorted.exists():
                grouped.append({'subcategory': None, 'packages': unsorted})
            context['grouped_packages'] = grouped
        else:
            context['grouped_packages'] = None

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