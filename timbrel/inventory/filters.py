from django_filters import rest_framework as filters

from .models import Product


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
