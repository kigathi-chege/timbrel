from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from timbrel.admin import BaseAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin, BaseAdmin):
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    ("first_name", "last_name"),
                    "email",
                    "description",
                    "url",
                    "newsletter",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Important dates",
            {
                "fields": ("last_login", "date_joined"),
                "classes": ("tab",),
            },
        ),
    )
    list_display = ("name", "email", "phone", "is_staff")
    readonly_fields = ("phone", "last_login", "date_joined")


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, BaseAdmin):
    pass
