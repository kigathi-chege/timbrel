from unfold.admin import TabularInline

from .models import Order


class OrderProductsInline(TabularInline):
    model = Order.products.through
    tab = True
    extra = 0
    show_change_link = True
    verbose_name = "product"
    fields = ["product", "quantity", "price"]
    autocomplete_fields = ["product"]
    ordering = ["-created_at"]
