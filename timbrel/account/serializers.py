from typing import Any, Dict

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.views import api_settings
from phonenumber_field.phonenumber import PhoneNumber


from timbrel.tasks import send_sms
from timbrel.base import BaseSerializer
from timbrel.utils import generate_random_string, get_class
from .models import User, OTP


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
    password = serializers.CharField(required=False)
    region = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    name = serializers.ReadOnlyField()

    def create(self, validated_data):
        validated_data["username"] = self.retrieve_username(validated_data)
        user = super().create(validated_data)
        if "password" not in validated_data or validated_data["password"] is None:
            validated_data["password"] = generate_random_string()
            # TODO: Kigathi - December 21 2024 - Should send notification email if password is generated
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
            raise serializers.ValidationError("Phone number already registered", phone)
        return phone

    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already registered.")

        return email

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

    @classmethod
    def get_user(cls, data):
        serializer = cls(data=data)

        if serializer.is_valid():
            user = serializer.save()
        else:
            # TODO: Kigathi - December 21 2024 - Note that if the error message changes, this code will fail
            if (
                "phone" in serializer.errors
                and serializer.errors["phone"][0] == "Phone number already registered"
            ):
                user = get_class(User).objects.get(
                    phone=serializer.errors["phone"][0].code
                )
            else:
                raise ValidationError(serializer.errors)

        return user

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
