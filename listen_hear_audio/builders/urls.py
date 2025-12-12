from django.urls import path
from . import views

app_name = 'builders'

urlpatterns = [
    # Builder showroom - consultation experience
    path('showroom/', views.builder_showroom_intro, name='showroom'),
    path('showroom/browse/', views.builder_showroom, name='showroom_browse'),
    path('showroom/guided/', views.builder_showroom_guided, name='showroom_guided'),
    path('showroom/guided/<int:step>/', views.builder_showroom_guided, name='showroom_guided_step'),

    # Builder dashboard
    path('dashboard/', views.BuilderDashboardView.as_view(), name='dashboard'),

    # Property detail
    path('property/<int:pk>/', views.BuilderPropertyDetailView.as_view(), name='property_detail'),

    # Package actions
    path('package/<int:package_id>/request-date/', views.request_install_date, name='request_install_date'),
    path('package/<int:package_id>/update-notes/', views.update_package_notes, name='update_package_notes'),
]
