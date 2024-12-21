from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from timbrel.base import BaseViewSet

from .serializers import (
    StoreSerializer,
    ProductSerializer,
)
from .models import (
    FavoriteProduct,
    Store,
    Product,
)
from .filters import ProductFilter


class StoreViewSet(BaseViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    filterset_fields = ["name", "phone", "email"]
    search_fields = ["name", "url", "description", "slug"]


class ProductViewSet(BaseViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    filterset_class = ProductFilter
    search_fields = [
        "name",
        "price",
        "sku",
        "brand",
        "category",
        "conditions",
        "url",
        "description",
        "slug",
    ]

    @action(detail=True, methods=["get"])
    def favorite(self, request, pk=None):
        user = request.user
        product = self.get_object()
        favorite, created = FavoriteProduct.objects.get_or_create(
            user=user, product=product
        )

        if not created:
            favorite.delete()

        return Response({"success": True})
