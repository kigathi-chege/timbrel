import uuid
import datetime

from django.db import models, transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
from simple_history.models import HistoricalRecords
from phonenumber_field.phonenumber import PhoneNumber


from .utils import mpesa_express
from .utils import generate_random_string
from .base import CommonModel, BaseModel


"""ACCOUNT MODELS"""


class User(AbstractUser, BaseModel):
    phone = models.CharField(max_length=100, unique=True)
    newsletter = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def name(self):
        return (
            f"{self.first_name} {self.last_name}"
            if self.first_name and self.last_name
            else self.first_name or self.last_name or self.username
        )

    def get_slug_source(self):
        return "username"

    def exclude_from_representation(self):
        return [
            "id",
            "password",
            "groups",
            "user_permissions",
            "created_at",
            "updated_at",
            "last_login",
            "deleted_at",
            "is_superuser",
            "is_staff",
        ]

    def verify_otp(self, data):
        otp = OTP.objects.filter(user=self, status="active").first()
        if not otp:
            raise Exception("User does not have an active otp")
        if otp.code != data["code"]:
            otp.tries += 1
            otp.save()
            if otp.tries >= otp.max_tries:
                otp.status = "expired"
                otp.save()
            raise Exception("Invalid otp")
        if otp.expires_at < timezone.make_aware(
            datetime.datetime.now(), timezone.get_current_timezone()
        ):
            raise Exception("Otp has expired")
        otp.status = "used"
        otp.save()
        return True


class OTP(models.Model):
    STATUS_OPTIONS = (
        ("active", "Active"),
        ("used", "Used"),
        ("expired", "Expired"),
    )

    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_tries = models.IntegerField(default=settings.OTP_MAX_TRIES)
    tries = models.IntegerField(default=0)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="otps",
    )
    status = models.CharField(
        choices=STATUS_OPTIONS,
        default="active",
        max_length=10,
    )

    def save(self, *args, **kwargs):
        if self.id is None or not self.__class__.objects.filter(pk=self.pk).exists():
            active_otp = self.__class__.objects.filter(
                user=self.user, status="active"
            ).first()
            if active_otp:
                if active_otp.expires_at < timezone.make_aware(
                    datetime.datetime.now(), timezone.get_current_timezone()
                ):
                    active_otp.status = "expired"
                    active_otp.save()
                else:
                    raise Exception("User already has an active otp")
            self.code = generate_random_string(4, True)
            self.expires_at = timezone.make_aware(
                datetime.datetime.now(), timezone.get_current_timezone()
            ) + datetime.timedelta(minutes=int(settings.OTP_EXPIRY))

        super().save(*args, **kwargs)


"""INVENTORY MODELS"""


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


"""PAYMENT MODELS"""


class Customer(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.CharField(max_length=100, null=True, blank=True)
    longitude = models.CharField(max_length=100, null=True, blank=True)

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
    # PAYMENT_METHOD = (
    #     ("cash", "cash"),
    #     ("card", "card"),
    #     ("bank-transfer", "bank-transfer"),
    #     ("paypal", "paypal"),
    #     ("mpesa", "mpesa"),
    # )
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


"""UICOPY MODELS"""


class Text(BaseModel):
    content = models.TextField(null=True, blank=True)
    link = models.CharField(null=True, blank=True)

    def __str__(self):
        return self.content


class Button(BaseModel):
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    link = models.CharField(null=True, blank=True)

    def __str__(self):
        return self.text.content


class Image(BaseModel):
    title = models.CharField(max_length=200)
    link = models.CharField(null=True, blank=True)
    is_svg = models.BooleanField(default=False)
    svg_content = models.TextField(null=True, blank=True)
    alt = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title


class Data(BaseModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    filters = models.JSONField(null=True, blank=True)


class Section(BaseModel):
    title = models.CharField(max_length=200, unique=True)
    children = models.ManyToManyField("self", blank=True, through="SectionSection")
    texts = models.ManyToManyField(Text, blank=True, through="SectionText")
    buttons = models.ManyToManyField(Button, blank=True, through="SectionButton")
    images = models.ManyToManyField(Image, blank=True, through="SectionImage")
    data = models.ManyToManyField(Data, blank=True, through="SectionData")

    def __str__(self):
        return self.title


class SectionSection(BaseModel):
    parent = models.ForeignKey(
        Section, related_name="parent_sections", on_delete=models.CASCADE
    )
    child = models.ForeignKey(
        Section, related_name="child_sections", on_delete=models.CASCADE
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        unique_together = ("parent", "child")

    def __str__(self):
        return f"{self.parent} -> {self.child}"


class Page(BaseModel):
    title = models.CharField(max_length=200, unique=True)
    content = models.TextField(null=True, blank=True)
    sections = models.ManyToManyField(Section, blank=True, through="PageSection")
    meta_description = models.TextField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    canonical_url = models.URLField(blank=True, null=True)
    og_title = models.CharField(max_length=60, blank=True, null=True)
    og_description = models.TextField(blank=True, null=True)
    og_image = models.ImageField(upload_to="og_images/", blank=True, null=True)
    twitter_title = models.CharField(max_length=60, blank=True, null=True)
    twitter_description = models.TextField(blank=True, null=True)
    twitter_image = models.ImageField(
        upload_to="twitter_images/", blank=True, null=True
    )
    schema_markup = models.JSONField(blank=True, null=True)
    robots_meta_tag = models.CharField(max_length=10, default="index")
    total_views = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class SectionText(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]


class SectionButton(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    button = models.ForeignKey(Button, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]


class SectionImage(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]


class PageSection(BaseModel):
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.page.title} - {self.section.title}"

    class Meta:
        ordering = ["order"]


class SectionData(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    data = models.ForeignKey(Data, on_delete=models.CASCADE, null=True, blank=True)


"""COMMON MODELS"""


class Setting(BaseModel):
    name = models.CharField()
    value = models.TextField(null=True, blank=True)


class Tag(BaseModel):
    name = models.CharField(unique=True)

    def __str__(self):
        return self.name


class Facet(CommonModel):
    name = models.CharField(unique=True)
    tags = models.ManyToManyField("timbrel.Tag", blank=True)
    history = HistoricalRecords(inherit=True)

    def __str__(self):
        return self.name


class FacetValue(CommonModel):
    name = models.CharField()
    facet = models.ForeignKey(
        Facet, on_delete=models.CASCADE, related_name="facetvalues"
    )
    tags = models.ManyToManyField("timbrel.Tag", blank=True)
    history = HistoricalRecords(inherit=True)

    def __str__(self):
        return f"{self.facet.name} - {self.name}"


class File(BaseModel):
    name = models.CharField(max_length=200)
    path = models.TextField(null=True, blank=True)
    size = models.IntegerField(default=0)
    extension = models.CharField(max_length=10, null=True, blank=True)
    mimetype = models.CharField(max_length=100, null=True, blank=True)
    usagecount = models.IntegerField(default=1)
    checksum = models.CharField(max_length=100, null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name


class Advertisement(BaseModel):
    BIG = "big"
    SMALL = "small"
    AD_TYPE_CHOICES = [
        (BIG, "Big"),
        (SMALL, "Small"),
    ]

    ad_type = models.CharField(
        max_length=10,
        choices=AD_TYPE_CHOICES,
        default=SMALL,
    )
    start_time = models.DateTimeField(help_text="When the advertisement starts")
    end_time = models.DateTimeField(help_text="When the advertisement ends")
    user = models.ForeignKey(
        "timbrel.User",
        on_delete=models.CASCADE,
        related_name="advertisements",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_ad_type_display()})"

    @property
    def advertisement_status(self, *args, **kwargs):
        if self.end_time < timezone.now():
            return "expired"
        elif self.start_time > timezone.now():
            return "inactive"
        else:
            return "active"

    @property
    def is_active(self):
        return self.advertisement_status == "active"


class Article(BaseModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ArticleText(BaseModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]


class ArticleImage(BaseModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
