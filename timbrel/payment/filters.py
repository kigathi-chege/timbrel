from django_filters import rest_framework as filters

from .models import Order


class OrderFilter(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    max_amount = filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    user = filters.CharFilter(field_name="user__id", lookup_expr="iexact")

    class Meta:
        model = Order
        fields = ["reference", "url", "description", "total_amount", "order_status"]
