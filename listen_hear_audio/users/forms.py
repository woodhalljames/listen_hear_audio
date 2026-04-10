from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.contrib.auth import forms as admin_forms
from django import forms
from django.forms import EmailField, BooleanField, CharField
from django.utils.translation import gettext_lazy as _

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = ("email",)
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """

    subscribe_to_newsletter = BooleanField(
        label=_("Subscribe to our newsletter"),
        required=False,
        initial=True,
        help_text=_("Receive occasional updates, tips, and offers from Listen Hear.")
    )

    is_builder = BooleanField(
        label=_("I am a Builder / Contractor / Designer"),
        required=False,
        help_text=_("Check this box to request builder access. A member of our team will review and approve your account.")
    )

    company_name = CharField(
        max_length=255,
        label=_("Company Name"),
        required=False,
        help_text=_("Required if requesting builder/contractor/designer access.")
    )

    def clean(self):
        cleaned_data = super().clean()
        is_builder = cleaned_data.get('is_builder', False)
        company_name = cleaned_data.get('company_name', '')

        if is_builder and not company_name:
            self.add_error('company_name', _('Company name is required for builders/contractors/designers.'))

        return cleaned_data

    def save(self, request):
        user = super().save(request)
        user.subscribe_to_newsletter = self.cleaned_data.get('subscribe_to_newsletter', False)
        # is_builder is NOT set from the form — admin must grant builder status manually.
        # company_name is saved so admin can identify pending builder requests.
        user.company_name = self.cleaned_data.get('company_name', '')
        user.save()
        return user


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """
