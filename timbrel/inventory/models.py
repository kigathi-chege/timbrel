from django.db import models

from timbrel.base import BaseModel
from timbrel.account.models import User


class Offer(BaseModel):
    name = models.CharField(max_length=100)
    discount = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Discount amount or percentage"
    )
    is_percentage = models.BooleanField(
        default=True,
        help_text="True if discount is a percentage, False if it's a fixed amount",
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def __str__(self):
        return self.name


class Store(BaseModel):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    longitude = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.CharField(max_length=100, blank=True, null=True)
    users = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return self.name

    def exclude_from_representation(self):
        return [
            "slug",
            "created_at",
            "updated_at",
        ]


class Product(BaseModel):
    name = models.CharField(max_length=100)
    price = models.FloatField(default=0)
    sku = models.CharField(max_length=100, null=True, blank=True)
    is_saleable = models.BooleanField(default=True)
    stock_level = models.IntegerField(default=0)
    stores = models.ManyToManyField(
        Store, blank=True, through="timbrel.StoreProduct", related_name="products"
    )
    offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def offer_price(self):
        if self.offer:
            if self.offer.is_percentage:
                return self.price * (1 - self.offer.discount / 100)
            else:
                return self.price - self.offer.discount

    def exclude_from_representation(self):
        return [
            "slug",
            "created_at",
            "updated_at",
        ]


class StoreProduct(BaseModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, null=True, blank=True)
    stock_level = models.IntegerField(default=0)
    price = models.FloatField(default=0)

    def __str__(self):
        return f"{self.store.name} - {self.product.name}"


class FavoriteProduct(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
