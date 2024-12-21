from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.decorators import display

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
                    "reference",
                    ("user", "total_amount", "order_status"),
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
    list_filter = ["order_status"]
    list_filter_submit = True
    list_filter_sheet = False
    list_fullwidth = True
    list_display = ("reference", "user", "created_at", "total_amount", "display_status")
    search_fields = ["reference"]
    custom_inlines = [OrderProductsInline]

    @display(
        description=_("Status"),
        label={
            "pending": "info",
            "confirmed": "primary",
            "shipped": "warning",
            "delivered": "success",
            # "canceled": "danger",
        },
    )
    def display_status(self, instance: Order):
        if instance.order_status:
            return instance.order_status

        return None


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
    list_filter = ["active", "valid_from", "valid_to", "is_percentage"]
    search_fields = ["code", "discount"]

    actions = ["deactivate_all_coupons"]

    def deactivate_all_coupons(self, request, queryset):
        """
        Deactivate all active coupons.
        """
        Coupon.objects.filter(active=True).update(active=False)
        self.message_user(request, "All active coupons have been deactivated.")
