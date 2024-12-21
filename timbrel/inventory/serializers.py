from rest_framework import serializers

from timbrel.base import BaseSerializer
from .models import (
    Store,
    Product,
    FavoriteProduct,
)


class StoreSerializer(BaseSerializer):
    class Meta:
        model = Store
        fields = "__all__"


class ProductSerializer(BaseSerializer):
    offer_price = serializers.ReadOnlyField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return (
                True
                if FavoriteProduct.objects.filter(
                    user=request.user, product=obj
                ).exists()
                else None
            )
        return None
