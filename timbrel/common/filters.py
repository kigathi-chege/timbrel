from django.utils import timezone
from django_filters import rest_framework as filters

from .models import Advertisement


class AdvertisementFilter(filters.FilterSet):
    status = filters.ChoiceFilter(
        choices=[
            ("expired", "Expired"),
            ("inactive", "Inactive"),
            ("active", "Active"),
        ],
        method="filter_by_status",
    )

    class Meta:
        model = Advertisement
        fields = ["title", "ad_type"]

    def filter_by_status(self, queryset, name, value):
        now = timezone.now()

        if value == "expired":
            return queryset.filter(end_time__lt=now)
        elif value == "inactive":
            return queryset.filter(start_time__gt=now)
        elif value == "active":
            return queryset.filter(start_time__lte=now, end_time__gte=now)

        return queryset
