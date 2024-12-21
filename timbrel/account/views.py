from django.contrib.auth.models import Group, Permission
from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from timbrel.permissions import IsNotAuthenticated
from timbrel.base import BaseViewSet
from .serializers import UserSerializer, GroupSerializer, PermissionSerializer
from .models import User

"""ACCOUNT VIEWS"""


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated(),)

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(BaseViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    search_fields = ["email", "phone", "username", "slug"]
    filterset_fields = [
        "email",
        "phone",
        "username",
        "is_staff",
        "newsletter",
    ]

    def get_permissions(self):
        """
        Override to allow different permissions for register vs other actions.
        """
        if self.action == "register" or self.action == "otp":
            return [IsNotAuthenticated()]
        elif self.action == "me":
            return [permissions.IsAuthenticated()]
        else:
            return super().get_permissions()

    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.register(serializer.validated_data)
            return Response(user_id, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="verify-otp")
    def verify_otp(self, request, pk=None):
        user = self.get_object()
        serializer = UserSerializer(instance=user)
        if user.verify_otp(request.data):
            token = serializer.token(user)
            return Response(token, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = UserSerializer(instance=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GroupViewSet(BaseViewSet):
    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer


class PermissionViewSet(BaseViewSet):
    queryset = Permission.objects.all().order_by("name")
    serializer_class = PermissionSerializer
