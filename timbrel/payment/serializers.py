import uuid

from django.shortcuts import get_object_or_404
from rest_framework import serializers

from .models import Order, OrderProduct, Transaction, PaymentMethod, Coupon

from timbrel.base import BaseSerializer
from timbrel.utils import get_model
from .models import (
    Product,
)


class CouponSerializer(BaseSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"


class OrderSerializer(BaseSerializer):
    # TODO: Kigathi - November 28 2024 - Figure out how to create an order for another user
    user = serializers.CharField(required=False)
    store = serializers.CharField(required=False)
    orderproducts = serializers.ListField(required=False)
    total_amount = serializers.FloatField(required=False, read_only=True)
    reference = serializers.CharField(required=False, read_only=True)
    quantity = serializers.IntegerField(required=False)
    operation = serializers.ChoiceField(
        required=False, write_only=True, choices=Order.OPERATIONS
    )
    first_name = serializers.CharField(required=False, write_only=True)
    last_name = serializers.CharField(required=False, write_only=True)
    email = serializers.EmailField(required=False, write_only=True)
    region = serializers.CharField(required=False, write_only=True)
    phone = serializers.CharField(required=False, write_only=True)
    coupon = serializers.CharField(required=False)

    def get_required_fields(self):
        user_fields = ["first_name", "last_name", "email", "region", "phone"]
        order_fields = ["orderproducts", "store", "delivery_method", "delivery_address"]
        return user_fields + order_fields

    def __init__(self, *args, **kwargs):
        required = kwargs.get("required", False)

        super().__init__(*args, **kwargs)

        if required:
            for field_name, field in self.fields.items():
                if field_name in self.get_required_fields():
                    field.required = True

    def validate_orderproducts(self, orderproducts):
        """
        Should be a list that looks like this:{
            "product": "8e5a9a63-aebf-4c7d-9662-3b592517546d",
            "quantity": 2
        }
        """
        if orderproducts is not None:
            for product in orderproducts:
                if not isinstance(product, dict):
                    raise serializers.ValidationError(
                        "Each product must be a dictionary."
                    )
                if "product" not in product or "quantity" not in product:
                    raise serializers.ValidationError(
                        "Each product must contain 'product' and 'quantity'."
                    )

                try:
                    uuid.UUID(product["product"])
                except ValueError:
                    raise serializers.ValidationError(
                        f"Invalid UUID format for 'product': {product['product']}."
                    )

                if not isinstance(product["quantity"], int) or product["quantity"] < 1:
                    raise serializers.ValidationError(
                        f"'quantity' must be a positive integer, got {product['quantity']}."
                    )

        return orderproducts

    def create(self, validated_data):
        print(validated_data)

        raise NotImplementedError

    def before_new_cart(self, operation, product, quantity):
        pass

    def before_old_cart(self, operation, product, orderproduct, quantity):
        pass

    def cart(self, validated_data, pk=None):
        # TODO: Kigathi - November 28 2024 - Issue determining which price to use depending on the store. Currently using main price.
        quantity = validated_data.pop("quantity", 1)
        operation = validated_data.pop("operation", "add")
        product_model = get_model(Product)
        order_model = get_model(Order)
        product = get_object_or_404(product_model, pk=pk)

        self.before_new_cart(operation, product, quantity)

        pending_order = order_model.objects.filter(
            user=self.context["request"].user, order_status="pending"
        ).first()

        if not pending_order:
            if operation == "remove":
                raise serializers.ValidationError(
                    "You cannot remove a product from an order that does not exist."
                )

            order = order_model.objects.create(user=self.context["request"].user)
            orderproduct, _ = OrderProduct.objects.update_or_create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.offer_price if product.offer else product.price,
            )
            order.total_amount = orderproduct.price * orderproduct.quantity
            order.save()
            return order

        orderproduct = OrderProduct.objects.filter(
            order=pending_order, product=product
        ).first()

        if not orderproduct:
            if operation == "remove":
                raise serializers.ValidationError(
                    "Product does not exist in the order."
                )

            orderproduct = OrderProduct.objects.create(
                order=pending_order,
                product=product,
                quantity=quantity,
                price=product.offer_price if product.offer else product.price,
            )

        else:
            self.before_old_cart(operation, product, orderproduct, quantity)

            orderproduct.quantity = (
                orderproduct.quantity + quantity
                if operation == "add"
                else orderproduct.quantity - quantity
            )
            orderproduct.save()

        if orderproduct.quantity == 0:
            orderproduct.delete()

        total_amount = sum(
            (orderproduct.price * orderproduct.quantity)
            for orderproduct in pending_order.order_products.all()
        )

        pending_order.total_amount = total_amount
        pending_order.save()
        return pending_order

    def after_cart(self, validated_data):
        pass

    class Meta:
        model = Order
        fields = "__all__"


class TransactionSerializer(BaseSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"


class PaymentMethodSerializer(BaseSerializer):
    class Meta:
        model = PaymentMethod
        fields = "__all__"
