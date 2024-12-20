import json

from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

from django.utils import timezone
from django.http import StreamingHttpResponse
from django.core.files.storage import default_storage
from django.contrib.auth.models import Group, Permission
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import OrderFilter
from .models import Order, Transaction, PaymentMethod, Coupon
from .tasks import calculate_popular_products

from .permissions import IsNotAuthenticated, IsOwnerOnly
from .base import BaseViewSet
from .serializers import (
    TagSerializer,
    FileSerializer,
    AdvertisementSerializer,
    ArticleSerializer,
    FacetSerializer,
    FacetValueSerializer,
    TextSerializer,
    DataSerializer,
    SectionSerializer,
    PageSerializer,
    UserSerializer, 
    GroupSerializer, 
    PermissionSerializer, 
    StoreSerializer, 
    ProductSerializer,
    OrderSerializer,
    TransactionSerializer,
    PaymentMethodSerializer,
    CouponSerializer,
)
from .models import Tag, File, Advertisement, Article, Facet, FacetValue, Text, Data, Section, Page, User, Store, Product
from .filters import AdvertisementFilter, ProductFilter

"""ACCOUNT VIEWS"""

class LogoutView(APIView):
    permission_classes = (IsAuthenticated(),)

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
            return [IsAuthenticated()]
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


"""INVENTORY VIEWS"""

class StoreViewSet(BaseViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    filterset_fields = ["name", "phone", "email"]
    search_fields = ["name", "url", "description", "slug"]


class ProductViewSet(BaseViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    filterset_class = ProductFilter
    search_fields = [
        "name",
        "price",
        "sku",
        "brand",
        "category",
        "conditions",
        "url",
        "description",
        "slug",
    ]

    @action(detail=True, methods=["get"])
    def favorite(self, request, pk=None):
        user = request.user
        product = self.get_object()
        favorite, created = FavoriteProduct.objects.get_or_create(
            user=user, product=product
        )

        if not created:
            favorite.delete()

        return Response({"success": True})


"""PAYMENT VIEWS"""

class MpesaCallbackView(APIView):
    permission_classes = (permissions.AllowAny(),)

    def post(self, request):
        mpesa_callback = request.data

        merchant_request_id = (
            mpesa_callback.get("Body", {})
            .get("stkCallback", {})
            .get("MerchantRequestID", None)
        )
        result_code = (
            mpesa_callback.get("Body", {})
            .get("stkCallback", {})
            .get("ResultCode", None)
        )

        if merchant_request_id:
            transaction = Transaction.objects.filter(
                reference=merchant_request_id
            ).first()
            transaction.transaction_status = "success" if result_code == 0 else "failed"
            transaction.description = json.dumps(request.data)
            transaction.save()
        else:
            print("No merchant request id or result code")

        return Response(status=status.HTTP_200_OK)


class CouponViewSet(BaseViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer


class OrderViewSet(BaseViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOnly]
    search_fields = ["reference", "url", "description"]
    filterset_class = OrderFilter

    def get_permissions(self):
        """
        Override to allow different permissions for register vs other actions.
        """
        if self.action == "pay":
            return [permissions.AllowAny()]
        else:
            return super().get_permissions()

    @action(detail=True, methods=["post"])
    def operate(self, request, pk=None):
        serializer = OrderSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        order = serializer.operate(serializer.validated_data, pk)
        serializer.instance = order
        serializer.context["with"] = "products"
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        order = self.get_object()

        # TODO: Kigathi - December 9 2024 - If user is not authenticated, we must expect the whole order together will all products, and the user details
        # We need a pay serializer

        try:
            payment_details = request.data.get("payment_details")
            order.pay(payment_details=payment_details)
            calculate_popular_products.delay_on_commit()
            return Response(
                {"status": "success", "message": "Order paid successfully."},
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            print("EXCEPTION", e)
            return Response(
                {"status": "error", "message": "Payment failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TransactionViewSet(BaseViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class PaymentMethodViewSet(BaseViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer



"""COMMON VIEWS"""

class TagViewSet(BaseViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["name", "url", "description"]
    filterset_fields = ["name", "url", "description"]


class FacetViewSet(BaseViewSet):
    queryset = Facet.objects.all()
    serializer_class = FacetSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["name", "url", "description"]
    filterset_fields = ["name", "url", "description"]


class FacetValueViewSet(BaseViewSet):
    queryset = FacetValue.objects.all()
    serializer_class = FacetValueSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["name", "url", "description"]
    filterset_fields = ["name", "url", "description", "facet"]


class FileViewSet(BaseViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["name", "url", "description"]
    filterset_fields = [
        "name",
        "url",
        "description",
        "size",
        "extension",
        "mimetype",
        "usagecount",
        "viewed_at",
    ]

    @action(detail=True, methods=["get"], url_name="view")
    def view(self, request, pk=None):
        file = self.get_object()
        file.viewed_at = timezone.now()
        file.save()
        if not default_storage.exists(file.path):
            return Response(
                {"error": "File not found"}, status=status.HTTP_404_NOT_FOUND
            )

        file_stream = default_storage.open(file.path, "rb")

        response = StreamingHttpResponse(
            file_stream, content_type=file.mimetype or "application/octet-stream"
        )
        response["Content-Disposition"] = f'inline; filename="{file.name}"'
        return response


class AdvertisementViewSet(BaseViewSet):
    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["ad_type", "title", "description", "url"]
    filterset_class = AdvertisementFilter


class ArticleViewSet(BaseViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["title", "content", "description", "url"]


"""UICOPY VIEWS"""


class TextViewSet(BaseViewSet):
    queryset = Text.objects.all()
    serializer_class = TextSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["title", "content", "slug"]


class DataViewSet(BaseViewSet):
    queryset = Data.objects.all()
    serializer_class = DataSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class SectionViewSet(BaseViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["title", "description", "slug"]


class PageViewSet(BaseViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ["email", "phone", "username", "slug"]
