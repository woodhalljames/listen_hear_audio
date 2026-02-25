from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Prefetch
from .models import Category, CategoryImage, CategoryVideo, SubCategory, Package


class CatalogView(ListView):
    """Single-page view showing all categories and packages"""
    model = Category
    template_name = 'products/catalog.html'
    context_object_name = 'categories'

    def get_queryset(self):
        catalog_packages = Package.objects.filter(
            is_active=True, visibility__in=['both', 'catalog']
        )
        return Category.objects.filter(
            is_active=True,
            show_in_catalog=True
        ).prefetch_related(
            Prefetch(
                'subcategories__packages',
                queryset=catalog_packages,
            ),
            Prefetch(
                'packages',
                queryset=catalog_packages,
            ),
        ).order_by('display_order', 'name')


class CategoryDetailView(DetailView):
    """Detail view for a single category"""
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        catalog_packages = Package.objects.filter(
            is_active=True, visibility__in=['both', 'catalog']
        )
        return Category.objects.filter(is_active=True).prefetch_related(
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
        return Package.objects.filter(is_active=True).select_related(
            'category',
            'subcategory'
        )
