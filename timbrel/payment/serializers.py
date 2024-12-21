import uuid

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from timbrel.base import BaseSerializer
from timbrel.account.serializers import UserSerializer
from timbrel.inventory.models import Product, Store
from timbrel.utils import get_class, only_pop

from .models import Order, OrderProduct, Transaction, PaymentMethod, Coupon, Customer


class CouponSerializer(BaseSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"


class CustomerSerializer(BaseSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


class OrderSerializer(BaseSerializer):
    # TODO: Kigathi - November 28 2024 - Figure out how to create an order for another user
    user = serializers.CharField(required=False)
    store = serializers.PrimaryKeyRelatedField(
        required=False, queryset=get_class(Store).objects.all()
    )
    customer = serializers.PrimaryKeyRelatedField(
        required=False, queryset=get_class(Customer).objects.all()
    )
    coupon = serializers.PrimaryKeyRelatedField(
        required=False, queryset=get_class(Coupon).objects.all()
    )
    payment_method = serializers.CharField(required=False)
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
        order_fields = [
            "store",
            "delivery_method",
            "delivery_address",
            "payment_method",
        ]
        if (
            self.context["request"].user
            and self.context["request"].user.is_authenticated
        ):
            return order_fields
        more_fields = [
            "first_name",
            "last_name",
            "email",
            "region",
            "phone",
            "orderproducts",
        ]
        return more_fields + order_fields

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
        user = self.context["request"].user

        if (
            "delivery_address" not in validated_data
            and "customer" not in validated_data
        ):
            raise ValidationError(
                "Either 'delivery_address' or 'customer' must be provided."
            )

        if user.is_authenticated:
            validated_data["user"] = user

        if user.is_anonymous or "first_name" in validated_data:
            required_fields = ["first_name", "last_name", "email", "phone"]
            missing_fields = [
                field for field in required_fields if field not in validated_data
            ]
            if missing_fields:
                raise ValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

            user = get_class(UserSerializer).get_user(
                data=only_pop(
                    validated_data,
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "password",
                )
            )

        customer_profile = (
            validated_data["customer"]
            if "customer" in validated_data
            else get_class(Customer).get_profile(
                user,
                validated_data["delivery_address"],
                (
                    validated_data["payment_method"]
                    if "payment_method" in validated_data
                    else "" or None
                ),
            )
        )

        validated_data["delivery_address"] = customer_profile.address
        validated_data["delivery_latitude"] = customer_profile.latitude
        validated_data["delivery_longitude"] = customer_profile.longitude
        validated_data["user"] = user
        validated_data["customer"] = customer_profile

        products = validated_data.pop("orderproducts")

        order = self.cart(validated_data, products, True)

        order.pay()

        return order

    def before_new_cart(self, operation, product, quantity):
        pass

    def before_old_cart(self, operation, product, orderproduct, quantity):
        pass

    def cart(self, validated_data, product=None, checkout=False):
        # TODO: Kigathi - November 28 2024 - Issue determining which price to use depending on the store. Currently using main price.
        validated_data["user"] = (
            validated_data["user"]
            if "user" in validated_data
            else self.context["request"].user
        )

        if not validated_data["user"]:
            raise serializers.ValidationError("Order cannot be created without a user.")

        quantity = validated_data.pop("quantity", 1)
        operation = validated_data.pop("operation", "add")
        product = validated_data.pop("products", product)
        product_model = get_class(Product)
        order_model = get_class(Order)

        if isinstance(product, list):
            product_ids = [
                (
                    item["product"],
                    item.get("quantity", 1),
                )
                for item in product
            ]
        else:
            product_ids = [(product, quantity)]

        products = product_model.objects.filter(
            id__in=[item[0] for item in product_ids]
        )

        for product_id, quantity in product_ids:
            product_instance = products.get(id=product_id)
            self.before_new_cart(operation, product_instance, quantity)

        pending_order = order_model.objects.filter(
            user=validated_data["user"], order_status="pending"
        ).first()

        if not pending_order:
            if operation == "remove":
                raise serializers.ValidationError(
                    "You cannot remove a product from an order that does not exist."
                )

            order = order_model.objects.create(**validated_data)

            for product_id, product_quantity in product_ids:
                product_instance = product_model.objects.get(id=product_id)
                orderproduct, _ = get_class(OrderProduct).objects.update_or_create(
                    order=order,
                    product=product_instance,
                    quantity=product_quantity,
                    price=(
                        product_instance.offer_price
                        if product_instance.offer
                        else product_instance.price
                    ),
                )

            total_amount = sum(
                (orderproduct.price * orderproduct.quantity)
                for orderproduct in order.order_products.all()
            )
            order.total_amount = total_amount
            order.save()
            return order

        for product_id, product_quantity in product_ids:
            product_instance = product_model.objects.get(id=product_id)
            orderproduct = OrderProduct.objects.filter(
                order=pending_order, product=product_instance
            ).first()

            if not orderproduct:
                if operation == "remove":
                    raise serializers.ValidationError(
                        "Product does not exist in the order."
                    )

                orderproduct = OrderProduct.objects.create(
                    order=pending_order,
                    product=product_instance,
                    quantity=product_quantity,
                    price=(
                        product_instance.offer_price
                        if product_instance.offer
                        else product_instance.price
                    ),
                )
            else:
                if operation == "add":
                    self.before_old_cart(
                        operation, product_instance, orderproduct, product_quantity
                    )

                orderproduct.quantity = (
                    orderproduct.quantity + product_quantity
                    if operation == "add"
                    else orderproduct.quantity - product_quantity
                )
                orderproduct.save()

            if orderproduct.quantity == 0:
                orderproduct.delete()

        total_amount = sum(
            (orderproduct.price * orderproduct.quantity)
            for orderproduct in pending_order.order_products.all()
        )

        pending_order.total_amount = total_amount

        if "coupon" in validated_data and checkout:
            pending_order.coupon = validated_data["coupon"]
            pending_order.apply_coupon()

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
