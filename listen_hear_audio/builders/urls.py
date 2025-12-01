from django.urls import path
from . import views

app_name = 'builders'

urlpatterns = [
    # Builder dashboard
    path('dashboard/', views.BuilderDashboardView.as_view(), name='dashboard'),

    # Property detail
    path('property/<int:pk>/', views.BuilderPropertyDetailView.as_view(), name='property_detail'),

    # Package actions
    path('package/<int:package_id>/request-date/', views.request_install_date, name='request_install_date'),
    path('package/<int:package_id>/update-notes/', views.update_package_notes, name='update_package_notes'),
]
