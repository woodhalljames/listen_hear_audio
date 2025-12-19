from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import TemplateView

from listen_hear_audio.core.views import ContactView

# Customize admin site
admin.site.site_header = "Listen Hear Administration"
admin.site.site_title = "Listen Hear Admin"
admin.site.index_title = "Welcome to Listen Hear Administration"

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    path("contact/", ContactView.as_view(), name="contact"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("listen_hear_audio.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Core app (service requests, etc.)
    path("", include("listen_hear_audio.core.urls", namespace="core")),
    # E-commerce apps
    path("catalog/", include("listen_hear_audio.products.urls", namespace="products")),
    path("quote/", include("listen_hear_audio.quotes.urls", namespace="quotes")),
    # Builders app
    path("builders/", include("listen_hear_audio.builders.urls", namespace="builders")),
    # Blog app
    path("blog/", include("listen_hear_audio.blog.urls", namespace="blog")),
    # Careers app
    path("careers/", include("listen_hear_audio.careers.urls", namespace="careers")),
    # Summernote
    path("summernote/", include("django_summernote.urls")),
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]