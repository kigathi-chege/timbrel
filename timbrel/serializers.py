import os
import mimetypes
import hashlib
import uuid
from typing import Any, Dict

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.models import update_last_login
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.views import api_settings
from phonenumber_field.phonenumber import PhoneNumber


from .models import Order, OrderProduct, Transaction, PaymentMethod, Coupon

from .tasks import send_sms
from .base import BaseSerializer
from .utils import get_serializer_dict, generate_random_string
from .models import (
    Tag,
    File,
    Advertisement,
    Article,
    Facet,
    FacetValue,
    Page,
    Section,
    Text,
    Button,
    Image,
    Data,
    User,
    OTP,
    Store,
    Product,
    FavoriteProduct,
)


"""ACCOUNT SERIALIZER"""


class TokenObtainPairSerializer(TokenObtainSerializer):
    token_class = RefreshToken

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        data["lifetime"] = refresh.access_token.lifetime

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data


class UserSerializer(BaseSerializer):
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    name = serializers.ReadOnlyField()

    def create(self, validated_data):
        validated_data["username"] = self.retrieve_username(validated_data)
        user = super().create(validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user

    def register(self, validated_data):
        user = self.create(validated_data)
        phone = user.phone
        otp = OTP.objects.create(user=user)
        send_sms.delay_on_commit(
            f"+{phone}",
            f"Welcome to Pharmaplus. Your OTP is {otp.code}. It is valid for {settings.OTP_EXPIRY} minutes.",
        )
        return {"id": user.id}

    def token(self, user):
        refresh = RefreshToken.for_user(user)
        token = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "lifetime": refresh.lifetime,
        }

        return token

    def validate_phone(self, phone):
        region = self.initial_data["region"] if "region" in self.initial_data else "KE"
        phone = PhoneNumber.from_string(phone, region)
        if not phone.is_valid():
            raise serializers.ValidationError("Phone number is invalid")
        phone = phone.as_e164.strip("+")
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("Phone number already registered")
        return phone

    def retrieve_username(self, validated_data):
        if ("username" in validated_data) and validated_data["username"]:
            return validated_data["username"]

        attrs = validated_data

        if attrs.get("first_name") and attrs.get("last_name"):
            base_username = (
                f"{attrs['first_name'][0].lower()}{attrs['last_name'].lower()}"
            )
        elif attrs.get("phone"):
            base_username = attrs["phone"]
        else:
            raise ValidationError(
                "Unable to generate username. Provide first name, last name, or phone."
            )

        username = base_username
        while User.objects.filter(username=username).exists():
            random_suffix = generate_random_string()
            username = f"{base_username}{random_suffix}"

        return username

    class Meta:
        model = User
        fields = "__all__"


class GroupSerializer(BaseSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class PermissionSerializer(BaseSerializer):
    class Meta:
        model = Permission
        fields = ["url", "name"]


"""INVENTORY SERIALIZER"""


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


"""PAYMENT SERIALIZER"""


class CouponSerializer(BaseSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"


class OrderSerializer(BaseSerializer):
    # TODO: Kigathi - November 28 2024 - Figure out how to create an order for another user
    user = serializers.CharField(required=False)
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

    def create(self, validated_data):
        raise NotImplementedError

    def operate(self, validated_data, pk=None):
        # TODO: Kigathi - November 28 2024 - Issue determining which price to use depending on the store. Currently using main price.
        quantity = validated_data.pop("quantity", 1)
        operation = validated_data.pop("operation", "add")
        product = get_object_or_404(Product, pk=pk)

        pending_order = Order.objects.filter(
            user=self.context["request"].user, order_status="pending"
        ).first()

        if not pending_order:
            if operation == "remove":
                raise serializers.ValidationError(
                    "You cannot remove a product from an order that does not exist."
                )

            order = Order.objects.create(user=self.context["request"].user)
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
            if operation == "add":
                raise serializers.ValidationError(
                    f"Product {product.name} is out of stock."
                )

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


"""COMMON SERIALIZER"""


class TagSerializer(BaseSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "url",
            "description",
            "tags",
            "absolute_url",
        ]


class FileSerializer(BaseSerializer):
    file = serializers.FileField(write_only=True)
    name = serializers.CharField(required=False)
    folder = serializers.CharField(write_only=True, max_length=100, required=False)

    def create(self, validated_data):
        file = validated_data["file"]
        upload_folder = (
            validated_data["folder"] if "folder" in validated_data else "general"
        )

        file_extension = os.path.splitext(file.name)[1]
        file_mime_type, _ = mimetypes.guess_type(file.name)

        hash_obj = hashlib.new("md5")
        file_content = file.read()
        hash_obj.update(file_content)
        checksum = hash_obj.hexdigest()

        """ 
        Check if there is an existing file with the same checksum
        If exists update usage_count by one and return
        """
        if existing_file := File.objects.filter(checksum=checksum).first():
            existing_file.usagecount += 1
            existing_file.save()
            return existing_file

        upload_file_path = f"{upload_folder}/{uuid.uuid4()}{file_extension}"
        file_path = default_storage.save(upload_file_path, file)

        file_data = {
            "name": validated_data["name"] if "name" in validated_data else file.name,
            "description": (
                validated_data["description"]
                if "description" in validated_data
                else None
            ),
            "path": file_path,
            "size": file.size,
            "extension": file_extension,
            "mimetype": file_mime_type,
            "checksum": checksum,
        }

        file = File.objects.create(**file_data)
        file.url = settings.APP_URL + reverse("timbrel-file-view", args=[file.id])
        return file

    class Meta:
        model = File
        fields = "__all__"


class AdvertisementSerializer(BaseSerializer):
    class Meta:
        model = Advertisement
        fields = "__all__"


class ArticleSerializer(BaseSerializer):
    class Meta:
        model = Article
        fields = "__all__"


class FacetSerializer(BaseSerializer):
    class Meta:
        model = Facet
        fields = "__all__"


class FacetValueSerializer(BaseSerializer):
    class Meta:
        model = FacetValue
        fields = "__all__"


"""UICOPY SERIALIZER"""


class TextSerializer(BaseSerializer):
    class Meta:
        model = Text
        fields = "__all__"


class ButtonSerializer(BaseSerializer):
    button_text = TextSerializer(
        many=False, read_only=True, source="text", allow_null=True
    )

    class Meta:
        model = Button
        fields = "__all__"


class ImageSerializer(BaseSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = "__all__"

    def get_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class DataSerializer(BaseSerializer):
    class Meta:
        model = Data
        fields = "__all__"

    def to_representation(self, instance):
        try:
            content_type = ContentType.objects.get(id=instance.content_type_id)
            model_class = content_type.model_class()

            if model_class is None:
                raise ValueError("No model found for this content type.")

            # get all the filters from instance.filters
            # check if there is a page_size filter

            if "page_size" in instance.filters:
                print("PAGE SIZE IN FILTERS", content_type.model)
                page_size = int(instance.filters["page_size"])
                queryset = model_class.objects.all()[:page_size]
            else:
                print("PAGE SIZE NOT FOUND IN FILTERS", content_type.model)
                queryset = model_class.objects.all()

            serializer_dict = get_serializer_dict()
            serializer_class = serializer_dict.get(content_type.model)
            serialized_data = serializer_class(queryset, many=True).data

            return serialized_data

        except ObjectDoesNotExist:
            print("ContentType with this ID does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return super().to_representation(instance)


class SectionSerializer(BaseSerializer):
    section_texts = serializers.SerializerMethodField()
    section_buttons = serializers.SerializerMethodField()
    section_images = serializers.SerializerMethodField()
    child_sections = serializers.SerializerMethodField()
    section_data = serializers.SerializerMethodField()

    def get_section_texts(self, obj):
        return TextSerializer(obj.texts.order_by("sectiontext__order"), many=True).data

    def get_section_buttons(self, obj):
        return ButtonSerializer(
            obj.buttons.order_by("sectionbutton__order"), many=True
        ).data

    def get_section_images(self, obj):
        return ImageSerializer(
            obj.images.order_by("sectionimage__order"), many=True
        ).data

    def get_child_sections(self, obj):
        serializer = SectionSerializer(
            obj.children.order_by("child_sections__order"), many=True
        )
        return serializer.data

    def get_section_data(self, obj):
        return DataSerializer(obj.data, many=True).data

    class Meta:
        model = Section
        fields = "__all__"


class PageSerializer(BaseSerializer):
    page_sections = serializers.SerializerMethodField()
    # page_images = serializers.SerializerMethodField()

    def get_page_sections(self, obj):
        return SectionSerializer(
            obj.sections.order_by("pagesection__order"), many=True
        ).data

    class Meta:
        model = Page
        fields = "__all__"
