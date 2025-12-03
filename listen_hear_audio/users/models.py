from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from slugify import slugify

from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for Listen Hear Audio.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]
    
    # Builder fields
    is_builder = BooleanField(
        default=False,
        help_text="Designates whether this user is a builder/contractor with property management access."
    )
    company_name = CharField(
        max_length=200,
        blank=True,
        help_text="Builder/contractor company name"
    )

    # Installation address fields (for business purposes)
    street = CharField(
        _("Street Address"),
        max_length=300,
        blank=True,
        help_text="Street address for installations"
    )
    city = CharField(
        _("City"),
        max_length=100,
        blank=True,
        help_text="City"
    )
    state = CharField(
        _("State"),
        max_length=2,
        blank=True,
        help_text="State (2-letter abbreviation)"
    )
    zip_code = CharField(
        _("ZIP Code"),
        max_length=10,
        blank=True,
        help_text="ZIP code"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        if self.is_builder:
            return reverse("builders:dashboard")
        return reverse("users:detail", kwargs={"pk": self.id})