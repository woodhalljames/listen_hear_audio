from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.CatalogView.as_view(), name='catalog'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('package/<slug:slug>/', views.PackageDetailView.as_view(), name='package_detail'),
]