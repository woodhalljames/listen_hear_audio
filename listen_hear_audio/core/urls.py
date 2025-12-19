from django.urls import path

from .views import ContactView, ServiceRequestSuccessView, ServiceRequestView

app_name = "core"
urlpatterns = [
    path("contact/", ContactView.as_view(), name="contact"),
    path("service-request/", ServiceRequestView.as_view(), name="service_request"),
    path("service-request/success/", ServiceRequestSuccessView.as_view(), name="service_request_success"),
]
