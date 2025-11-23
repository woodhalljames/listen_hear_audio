import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "listen_hear_audio.users"
    verbose_name = _("Users")

    def ready(self):
        with contextlib.suppress(ImportError):
            import listen_hear_audio.users.signals  # noqa: F401, PLC0415
