from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from listen_hear_audio.blog.models import BlogPost
from listen_hear_audio.products.models import Category, Package


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return ["home", "about", "contact", "products:catalog", "blog:post_list", "gallery:gallery", "careers:job_list"]

    def location(self, item):
        return reverse(item)


class BlogSitemap(Sitemap):
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        return BlogPost.objects.filter(published=True)

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        return Category.objects.filter(is_active=True)


class PackageSitemap(Sitemap):
    priority = 0.5
    changefreq = "weekly"

    def items(self):
        return Package.objects.filter(is_active=True)


sitemaps = {
    "static": StaticViewSitemap,
    "blog": BlogSitemap,
    "categories": CategorySitemap,
    "packages": PackageSitemap,
}
