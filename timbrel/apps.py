from django.apps import AppConfig
from cities_light.apps import CitiesLightConfig


class TimbrelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "timbrel"
    label = "timbrel"


class CustomCitiesLightConfig(CitiesLightConfig):
    verbose_name = "Location"
