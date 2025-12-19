from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .models import BusinessInfo, ServiceRequest


class ContactView(TemplateView):
    """Contact page view."""

    template_name = "pages/contact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["business_info"] = BusinessInfo.load()
        return context


class ServiceRequestView(CreateView):
    """Service request form view."""

    model = ServiceRequest
    template_name = "core/service_request.html"
    fields = [
        "name",
        "email",
        "phone",
        "street_address",
        "city",
        "state",
        "zip_code",
        "service_type",
        "description",
        "preferred_date",
        "preferred_time",
    ]
    success_url = reverse_lazy("service_request_success")

    def get_initial(self):
        """Pre-fill form with user data if logged in."""
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            user = self.request.user
            initial.update({
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "street_address": user.street,
                "city": user.city,
                "state": user.state,
                "zip_code": user.zip_code,
            })
        return initial

    def form_valid(self, form):
        # Associate with user if logged in
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user

        # Save the service request
        response = super().form_valid(form)

        # Send email notification
        business_info = BusinessInfo.load()
        subject = f"New Service Request from {form.instance.name}"
        message = render_to_string("core/emails/service_request_notification.html", {
            "service_request": form.instance,
        })

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [business_info.email],
                html_message=message,
                fail_silently=False,
            )
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error sending service request email: {e}")

        messages.success(self.request, "Your service request has been submitted! We'll contact you soon.")
        return response


class ServiceRequestSuccessView(TemplateView):
    """Success page after submitting service request."""

    template_name = "core/service_request_success.html"
