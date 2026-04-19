from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from listen_hear_audio.blog.models import BlogPost
from listen_hear_audio.products.models import Category


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
        return Category.objects.filter(is_active=True, show_in_catalog=True)

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "static": StaticViewSitemap,
    "blog": BlogSitemap,
    "categories": CategorySitemap,
}
