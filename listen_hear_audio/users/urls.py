from django.urls import path

from .views import (
    user_detail_view,
    user_redirect_view,
    user_update_view,
    BuilderDashboardView,
    BuilderPropertyDetailView,
    request_install_date,
    update_package_notes,
)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
    
    # Builder routes
    path("builder/dashboard/", BuilderDashboardView.as_view(), name="builder_dashboard"),
    path("builder/property/<int:pk>/", BuilderPropertyDetailView.as_view(), name="builder_property_detail"),
    path("builder/package/<int:package_id>/request-date/", request_install_date, name="request_install_date"),
    path("builder/package/<int:package_id>/update-notes/", update_package_notes, name="update_package_notes"),
]