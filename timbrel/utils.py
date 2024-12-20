import inspect
import random
import string
import inflect
import base64
import requests
import importlib
from datetime import datetime

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ForeignKey, OneToOneField, ManyToManyField
from django.urls import path, include
from django.conf import settings
from rest_framework import viewsets, serializers, routers
from base64 import b64encode

p = inflect.engine()


def register_viewsets(router, app_name):
    """Dynamically register all ViewSets in the app's viewsets.py file."""
    try:
        # Import the viewsets module from the given app
        viewsets_module = __import__(f"{app_name}.views", fromlist=[""])

        # Iterate over all members (classes, functions, etc.) in the viewsets module
        for name, obj in inspect.getmembers(viewsets_module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, viewsets.ModelViewSet)
                and name != "BaseViewSet"
            ):
                viewset_name = obj.__name__
                viewset_name_lower = viewset_name.lower()
                base_name = viewset_name_lower.replace("viewset", "")
                url_name = p.plural(base_name)

                if obj.__module__.startswith("timbrel"):
                    basename = f"timbrel-{base_name}"
                else:
                    basename = base_name

                router.register(rf"{url_name}", obj, basename=basename)

    except ModuleNotFoundError:
        pass


def register_routers(exclude_apps=[]):
    basic_urls = []
    included_apps = [item for item in settings.MY_APPS if item not in exclude_apps]
    for app in included_apps:
        router = routers.DefaultRouter()
        register_viewsets(router, app)
        basic_urls.append(path(f"{get_route_prefix(app)}", include(router.urls)))
    return basic_urls


def include_routers(exclude_apps=[]):
    """Dynamically import routers from each installed app."""
    router_urls = register_routers(exclude_apps)
    for app in settings.MY_APPS:
        try:
            app_urls = importlib.import_module(f"{app}.urls")
            if hasattr(app_urls, "router"):
                router_urls.append(
                    path(f"{get_route_prefix(app)}", include(app_urls.router.urls))
                )
        except ModuleNotFoundError:
            pass
    return router_urls


def get_route_prefix(app_name):
    try:
        app_config = apps.get_app_config(app_name)
        if hasattr(app_config, "route_prefix"):
            prefix = app_config.route_prefix
        else:
            prefix = app_name
    except LookupError:
        print(f"App '{app_name}' not found. Using default prefix.")
        prefix = app_name
    except Exception as e:
        print(f"An error occurred while accessing the app config for '{app_name}': {e}")
        prefix = app_name
    return f"{prefix}/" if prefix else ""


def get_serializer_dict():
    serializer_dict = {}
    for app in settings.MY_APPS:
        try:
            viewsets_module = __import__(f"{app}.serializers", fromlist=[""])

            # Iterate over all members (classes, functions, etc.) in the serializers module
            for name, obj in inspect.getmembers(viewsets_module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, serializers.ModelSerializer)
                    and name != "BaseSerializer"
                ):
                    serializer_name = obj.__name__
                    serializer_name_lower = serializer_name.lower()
                    base_name = serializer_name_lower.replace("serializer", "")
                    serializer_dict[base_name] = obj
        except ModuleNotFoundError:
            pass

    return serializer_dict


def is_relationship(model, field_name):
    try:
        field = model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return False
    return isinstance(field, (ForeignKey, OneToOneField, ManyToManyField))


def generate_random_string(length=4, digits_only=False):
    if digits_only:
        return "".join(random.choices(string.digits, k=length))
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def basic_auth(username, password):
    token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def command_log(command, message, status=None):
    command.stdout.write(
        (
            command.style.ERROR
            if status == "error"
            else command.style.SUCCESS if status == "success" else lambda x: x
        )(message)
    )


def encode_data(key, secret, timestamp="", separator=""):
    if timestamp:
        data = f"{key}{separator}{secret}{separator}{timestamp}"
    else:
        data = f"{key}{separator}{secret}"
    data_bytes = data.encode("utf-8")
    encoded_data = base64.b64encode(data_bytes)
    return encoded_data.decode("utf-8")


def mpesa_express(amount, phone, reference, description):
    access_token = authenticate()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = encode_data(
        key=settings.MPESA_SHORTCODE,
        secret=settings.MPESA_PASSKEY,
        timestamp=timestamp,
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    test_phones = settings.TEST_PHONES.split(",")
    if phone in test_phones:
        amount = 1

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": reference,
        "TransactionDesc": description,
    }

    response = requests.post(
        url=settings.MPESA_STK_ENDPOINT,
        headers=headers,
        json=payload,
    )

    return response.json()


def authenticate():
    base64_string = encode_data(
        key=settings.MPESA_CONSUMER_KEY,
        secret=settings.MPESA_CONSUMER_SECRET,
        separator=":",
    )

    response = requests.request(
        "GET",
        settings.MPESA_OAUTH_ENDPOINT,
        headers={"Authorization": f"Basic {base64_string}"},
    )

    json_response = response.json()
    return json_response["access_token"]
