from django.utils import timezone
from django_filters import rest_framework as filters

from .models import Advertisement, Product, Order



class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    in_stock = filters.BooleanFilter(method="in_stock_filter")
    has_offer = filters.BooleanFilter(field_name="offer", method="filter_has_offer")

    class Meta:
        model = Product
        fields = ["name", "url", "description", "is_saleable", "price", "sku"]

    def in_stock_filter(self, queryset, name, value):
        if value is False:
            return queryset.filter(stock_level=0)
        elif value is True:
            return queryset.filter(stock_level__gt=0)
        return queryset

    def filter_has_offer(self, queryset, name, value):
        if value:
            return queryset.filter(offer__isnull=False)
        return queryset


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


class OrderFilter(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    max_amount = filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    user = filters.CharFilter(field_name="user__id", lookup_expr="iexact")

    class Meta:
        model = Order
        fields = ["reference", "url", "description", "total_amount", "order_status"]
