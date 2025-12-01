from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BuildersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "listen_hear_audio.builders"
    verbose_name = _("Builders")
