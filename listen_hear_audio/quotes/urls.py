from django.urls import path
from . import views

app_name = 'quotes'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:package_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/update/<int:package_id>/', views.update_cart_view, name='update_cart'),
    path('cart/remove/<int:package_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirmation/<str:quote_number>/', views.quote_confirmation_view, name='quote_confirmation'),
    path('quote/<str:quote_number>/download/', views.download_quote_pdf, name='download_pdf'),
]