from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from timbrel.admin import BaseAdmin

from .models import Order, Transaction, Coupon
from .inlines import OrderProductsInline


@admin.register(Order)
class OrderAdmin(BaseAdmin):
    fieldsets = [
        (
            _("Order Information"),
            {
                "fields": [
                    "user",
                    ("reference", "total_amount", "order_status"),
                    "description",
                ],
                "classes": ["tab"],
            },
        ),
        (
            _("Delivery Information"),
            {
                "fields": (
                    ("delivery_method", "delivery_address"),
                    ("delivery_latitude", "delivery_longitude"),
                    ("delivery_charges", "packaging_cost"),
                ),
                "classes": ["tab"],
            },
        ),
        (
            _("More Details"),
            {
                "fields": (
                    "coupon",
                    "coupon_applied",
                    ("promotional_discount", "custom_discount"),
                ),
                "classes": ["tab"],
            },
        ),
    ]
    readonly_fields = ["user", "reference", "total_amount"]
    list_display = ("user", "reference", "created_at", "total_amount", "order_status")
    search_fields = ["reference"]
    custom_inlines = [OrderProductsInline]


@admin.register(Transaction)
class TransactionAdmin(BaseAdmin):
    fields = (
        "user",
        "reference",
        ("amount", "balance"),
        ("transaction_type", "transaction_status"),
        "order",
        "payment_method",
        "description",
    )
    list_display = (
        "user",
        "reference",
        "amount",
        "transaction_type",
        "transaction_status",
    )
    readonly_fields = [
        "user",
        "reference",
        "amount",
        "order",
        "balance",
        "transaction_type",
        "transaction_status",
        "payment_method",
    ]
    search_fields = ["reference"]


@admin.register(Coupon)
class CouponAdmin(BaseAdmin):
    fields = [
        ("code", "discount"),
        "is_percentage",
        "valid_from",
        "valid_to",
        ("usage_limit", "used_count"),
        "active",
    ]
    list_display = [
        "code",
        "discount",
        "is_percentage",
        "valid_from",
        "valid_to",
        "usage_limit",
        "used_count",
        "active",
    ]
    readonly_fields = ["code"]
    list_filter = ["active", "valid_from", "valid_to"]
    search_fields = ["code"]
    filter_horizontal = ("tags", "files", "facetvalues")
