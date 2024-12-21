import uuid
import datetime

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from phonenumber_field.phonenumber import PhoneNumber

from timbrel.base import BaseModel
from timbrel.account.models import User
from timbrel.inventory.models import Store, Product, StoreProduct
from timbrel.utils import mpesa_express, generate_random_string
from timbrel.gmaps import retrieve


class Customer(BaseModel):
    BILLING_CYCLES = (
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("semi_annually", "Semi Annually"),
        ("annually", "Annually"),
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="customerprofiles"
    )
    address = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.CharField(max_length=100, null=True, blank=True)
    longitude = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    address_line_1 = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_comment="The main address line (house/building number, street name).",
    )
    address_line_2 = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_comment="Optional field for additional address details (e.g., apartment number, suite, floor).",
    )
    city = models.ForeignKey("cities_light.City", on_delete=models.SET_NULL, null=True)
    subregion = models.ForeignKey(
        "cities_light.SubRegion", on_delete=models.SET_NULL, null=True
    )
    postal_code = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=100, null=True, blank=True)
    delivery_instructions = models.TextField(null=True, blank=True)
    company_name = models.CharField(max_length=100, null=True, blank=True)
    vat_number = models.CharField(max_length=100, null=True, blank=True)
    billing_cycle = models.CharField(
        max_length=100, choices=BILLING_CYCLES, null=True, blank=True
    )
    payment_method = models.ForeignKey(
        "timbrel.PaymentMethod", on_delete=models.CASCADE, null=True, blank=True
    )

    def clean(self):
        if self.is_primary:
            if (
                Customer.objects.filter(user=self.user, is_primary=True)
                .exclude(id=self.id)
                .exists()
            ):
                raise ValidationError(
                    "A customer can only have one primary profile at a time."
                )

    def save(self, *args, **kwargs):
        if self.is_primary:
            Customer.objects.filter(user=self.user, is_primary=True).exclude(
                id=self.id
            ).update(is_primary=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_profile(cls, user, address, payment_method=None):
        customer_profile = cls.objects.filter(address=address).first()

        if not customer_profile:
            (
                delivery_address,
                latitude,
                longitude,
            ) = retrieve(address)

            customer_profile, _ = cls.objects.get_or_create(
                user=user,
                address=delivery_address,
                latitude=latitude,
                longitude=longitude,
                payment_method=payment_method,
                defaults={
                    "is_primary": True,
                },
            )

        if not customer_profile.is_primary:
            customer_profile.is_primary = True
            customer_profile.save()
        return customer_profile

    def __str__(self):
        return self.user.name


class Coupon(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Discount amount or percentage"
    )
    is_percentage = models.BooleanField(
        default=True,
        help_text="True if discount is a percentage, False if it's a fixed amount",
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text="Number of times the coupon can be used"
    )
    used_count = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def is_valid(self):
        return (
            self.active
            and self.valid_from <= timezone.now() <= self.valid_to
            and (self.usage_limit is None or self.used_count < self.usage_limit)
        )

    def apply_discount(self, total_amount):
        if self.is_percentage:
            return total_amount - (total_amount * (self.discount / 100))
        return max(0, total_amount - self.discount)

    @classmethod
    def toggle_all_coupons(on=True):
        coupons = Coupon.objects.filter(active=True)
        print("COUPONS", coupons)
        return f"All active coupons have been {'' if on else 'de'}activated."

    def __str__(self):
        return self.code


class Order(BaseModel):
    OPERATIONS = (
        ("add", "add"),
        ("remove", "remove"),
    )
    ORDER_STATUS = (
        ("pending", "pending"),
        ("confirmed", "confirmed"),
        ("shipped", "shipped"),
        ("delivered", "delivered"),
    )
    DELIVERY_METHODS = (
        ("pickup", "pickup"),
        ("delivery", "delivery"),
    )
    reference = models.CharField(max_length=100, default=uuid.uuid4, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    coupon_applied = models.BooleanField(default=False)
    products = models.ManyToManyField(
        Product, through="timbrel.OrderProduct", related_name="orders"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, null=True, blank=True
    )
    order_status = models.CharField(choices=ORDER_STATUS, default="pending")
    delivery_method = models.CharField(
        max_length=100, choices=DELIVERY_METHODS, default="delivery"
    )
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    delivery_address = models.CharField(max_length=100, null=True, blank=True)
    delivery_latitude = models.CharField(max_length=100, null=True, blank=True)
    delivery_longitude = models.CharField(max_length=100, null=True, blank=True)
    delivery_charges = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    packaging_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    promotional_discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True
    )
    custom_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return self.reference

    def get_slug_source(self):
        return "reference"

    def save(self, *args, **kwargs):
        if self.id is None or not self.__class__.objects.filter(pk=self.pk).exists():
            reference = generate_random_string(3)
            date_part = datetime.datetime.now().strftime("%y%m%d")
            reference_number = f"ORD-{date_part}-{reference.upper()}"
            self.reference = reference_number
            count = 1
            while self.__class__.objects.filter(reference=self.reference).exists():
                self.reference = f"{self.reference}-{count}"
                count += 1
            self.reference = self.reference.upper()

        super().save(*args, **kwargs)

    def pay(self, payment_details=None):
        if self.order_status != "pending":
            raise ValueError("Only pending orders can be paid.")

        phone = self.user.phone

        # TODO: Kigathi - December 5 2024 - This assumes payment_details is a phone number and that region is always KE

        if payment_details:
            phone = PhoneNumber.from_string(payment_details, "KE")
            if not phone.is_valid():
                raise ValueError("Phone number is invalid")
            phone = phone.as_e164.strip("+")

        self.apply_coupon()

        # TODO: Kigathi - December 20 2024 - Response depends on the payment method

        response = mpesa_express(
            float(self.total_amount),
            phone,
            self.reference,
            "Order Payment",
        )

        if "errorCode" in response:
            raise ValueError(response["errorMessage"])

        with transaction.atomic():
            self.order_status = "confirmed"
            self.save()

            payment_method, created = PaymentMethod.objects.get_or_create(name="mpesa")
            Transaction.objects.create(
                payment_method=payment_method,
                amount=self.total_amount,
                user=self.user,
                order=self,
                reference=response["MerchantRequestID"],
            )

        return True

    def apply_coupon(self):
        if self.coupon and self.coupon.is_valid() and not self.coupon_applied:
            discounted_total = self.coupon.apply_discount(self.total_amount)
            self.total_amount = discounted_total
            self.promotional_discount = self.total_amount - discounted_total
            self.coupon_applied = True
            self.coupon.used_count += 1
            self.coupon.save()
            self.save()


class OrderProduct(BaseModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_products"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    store_product = models.ForeignKey(
        StoreProduct, on_delete=models.CASCADE, null=True, blank=True
    )
    quantity = models.IntegerField(default=1)
    price = models.FloatField(default=0)

    def __str__(self):
        return f"{self.order.reference} - {self.product.name}"


class Transaction(BaseModel):
    TRANSACTION_TYPE = (
        ("credit", "credit"),
        ("debit", "debit"),
    )
    TRANSACTION_STATUS = (
        ("pending", "pending"),
        ("success", "success"),
        ("failed", "failed"),
    )
    transaction_type = models.CharField(choices=TRANSACTION_TYPE, default="debit")
    payment_method = models.ForeignKey(
        "timbrel.PaymentMethod", on_delete=models.CASCADE
    )
    transaction_status = models.CharField(choices=TRANSACTION_STATUS, default="pending")
    amount = models.FloatField()
    balance = models.FloatField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    reference = models.CharField(max_length=100, null=True, blank=True)


class PaymentMethod(BaseModel):
    PAYMENT_METHOD = (
        ("cash", "cash"),
        ("card", "card"),
        ("bank-transfer", "bank-transfer"),
        ("paypal", "paypal"),
        ("mpesa", "mpesa"),
    )
    name = models.CharField(max_length=100)
    payment_method = models.CharField(choices=PAYMENT_METHOD, default="cash")

    def __str__(self):
        return self.name
