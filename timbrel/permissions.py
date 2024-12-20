from rest_framework.permissions import DjangoObjectPermissions
from rest_framework.permissions import BasePermission
from rest_framework.permissions import SAFE_METHODS


def get_full_app_permissions(app):
    return [f"delete_{app}", f"add_{app}", f"change_{app}", f"view_{app}"]


def retrieve_permission_keys(role):
    full_permissions = [
        get_full_app_permissions(include) for include in role["include"]
    ]
    print("FULL PERMISSIONS", full_permissions)
    pass



def create_role(role):
    include_keys = retrieve_permission_keys(role)
    # permissions = Permission.objects.filter(codename__in=include_keys).all()
    # role, created = Group.objects.get_or_create(
    #     name=role,
    # )
    # role.permissions.set(permissions)
    # role.save()
    return role


class StrictDjangoObjectPermissions(DjangoObjectPermissions):
    """
    Custom permissions class that restricts all access unless the user
    explicitly has the necessary permissions.
    """

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class IsOwnerOnly(StrictDjangoObjectPermissions):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has a `user` attribute.
    """

    def has_permission(self, request, view):
        if view.action == "list" and not request.user.is_superuser:
            view.queryset = view.queryset.filter(user=request.user)
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if not hasattr(obj, "user"):
            return super().has_object_permission(request, view, obj)

        return obj.user == request.user or request.user.is_superuser


class IsOwnerOrReadOnly(StrictDjangoObjectPermissions):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS or not hasattr(obj, "user"):
            return True

        return (
            super().has_object_permission(request, view, obj)
            and obj.user == request.user
        )


class IsNotAuthenticated(BasePermission):
    """
    Allows access only to unauthenticated users.
    """

    def has_permission(self, request, view):
        return bool(not request.user or not request.user.is_authenticated)
