import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings


from timbrel.utils import generate_random_string
from timbrel.base import BaseModel


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
