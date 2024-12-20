from django.db.models import Count
from celery import shared_task

from .at import sms, on_finish
from .models import Product, Tag, Facet, FacetValue


@shared_task(name="send_sms")
def send_sms(recipient, message):
    sms.send(message, [recipient], callback=on_finish)


@shared_task
def calculate_popular_products():
    # TODO: Kigathi - December 17 2024 - Ensure that this function is doing the right thing

    popular_tag, created = Tag.objects.get_or_create(name="Popular")

    if not created:
        for product in Product.objects.filter(tags=popular_tag):
            product.tags.remove(popular_tag)
        for tag in Tag.objects.filter(tags=popular_tag):
            tag.tags.remove(popular_tag)

    popular_products = (
        Product.objects.filter(orders__order_status="confirmed")
        .annotate(confirmed_order_count=Count("orders"))
        .order_by("-confirmed_order_count")[:4]
    )

    for product in popular_products:
        product.tags.add(popular_tag)

    category_facet = Facet.objects.filter(name="Category").first()
    if not category_facet:
        return

    product_facetvalues = FacetValue.objects.filter(
        id__in=popular_products.values_list("facetvalues__id", flat=True)
    ).distinct()

    popular_facetvalues = category_facet.facetvalues.filter(
        id__in=product_facetvalues.values_list("id", flat=True)
    ).distinct()

    for facetvalue in popular_facetvalues:
        facetvalue.tags.add(popular_tag)

    return
