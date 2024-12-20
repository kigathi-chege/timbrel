from django.contrib.auth.backends import ModelBackend
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers.phonenumberutil import NumberParseException

from .models import User


class PhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("phone")

        region = kwargs.get("region", "KE")
        try:
            number = PhoneNumber.from_string(username, region=region)
        except NumberParseException:
            return

        username = number.as_e164.strip("+")

        if username is None or password is None:
            return

        user = User.objects.filter(phone=username).first()

        if not user:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User.set_password(User, password)
            return

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
