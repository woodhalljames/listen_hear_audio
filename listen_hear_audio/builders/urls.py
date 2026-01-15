from django.urls import path
from . import views

app_name = 'builders'

urlpatterns = [
    # Builder showroom
    path('showroom/', views.builder_showroom_intro, name='showroom'),
    path('showroom/guided/', views.builder_showroom, name='showroom_guided'),
    path('showroom/guided/<int:step>/', views.builder_showroom, name='showroom_guided_step'),

    # Property detail
    path('property/<int:pk>/', views.BuilderPropertyDetailView.as_view(), name='property_detail'),

    # Phase installation request
    path('property/<int:property_id>/phase/<str:phase>/request/', views.request_phase_install, name='request_phase_install'),
]
