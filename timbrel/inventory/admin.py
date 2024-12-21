from django.contrib import admin

from timbrel.admin import BaseAdmin

from .models import Product, Store, Offer


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    fields = (
        ("name", "price"),
        ("sku", "stock_level"),
        "is_saleable",
        "url",
        "offer",
        "description",
    )

    list_display = (
        "name",
        "price",
        "sku",
        "stock_level",
    )
    search_fields = ("name", "description", "url", "sku")
    readonly_fields = ("sku",)
    autocomplete_fields = ("offer",)


@admin.register(Store)
class StoreAdmin(BaseAdmin):
    fields = (
        "name",
        "phone",
        "email",
        "longitude",
        "latitude",
        "description",
        "url",
        "users",
    )
    list_display = ("name", "phone")
    search_fields = ("name", "phone")
    filter_horizontal = ("users",)


@admin.register(Offer)
class OfferAdmin(BaseAdmin):
    fields = (
        "name",
        "discount",
        "is_percentage",
        "valid_from",
        "valid_to",
        "description",
        "url",
    )
    list_display = ("name", "discount", "is_percentage", "valid_from", "valid_to")
    search_fields = ("name",)
