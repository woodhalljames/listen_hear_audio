from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView

from listen_hear_audio.users.models import User


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "public_id"
    slug_url_kwarg = "public_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add builder properties if user is a builder
        if self.object.is_builder:
            from listen_hear_audio.builders.models import Property
            context['properties'] = Property.objects.filter(
                builders=self.object
            ).prefetch_related('packages', 'builders').order_by('-updated_at')
        return context


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name", "phone", "website", "company_name", "street", "city", "state", "zip_code"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None=None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        if self.request.user.is_builder:
            return reverse("builders:showroom")
        return reverse("users:detail", kwargs={"public_id": self.request.user.public_id})


user_redirect_view = UserRedirectView.as_view()