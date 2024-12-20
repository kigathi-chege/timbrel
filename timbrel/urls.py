from cities_light.contrib.restframework3 import (
    CityModelViewSet,
    CountryModelViewSet,
    RegionModelViewSet,
    SubRegionModelViewSet,
)
from rest_framework import routers
from .utils import register_viewsets

router = routers.DefaultRouter()

register_viewsets(router, "timbrel")

router.register(r"cities", CityModelViewSet, basename="cities-light-api-city")
router.register(
    r"countries",
    CountryModelViewSet,
    basename="cities-light-api-country",
)
router.register(r"regions", RegionModelViewSet, basename="cities-light-api-region")
router.register(
    r"subregions",
    SubRegionModelViewSet,
    basename="cities-light-api-subregion",
)
