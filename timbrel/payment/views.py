import json

from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView

from .filters import OrderFilter
from .models import Order, Transaction, PaymentMethod, Coupon
from timbrel.tasks import calculate_popular_products

from timbrel.permissions import IsOwnerOnly
from timbrel.base import BaseViewSet
from .serializers import (
    OrderSerializer,
    TransactionSerializer,
    PaymentMethodSerializer,
    CouponSerializer,
)


class MpesaCallbackView(APIView):
    permission_classes = (permissions.AllowAny,)

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
            try:
                transaction = Transaction.objects.get(reference=merchant_request_id)
            except Transaction.DoesNotExist:
                raise ValueError(
                    f"No transaction found with reference: {merchant_request_id}"
                )
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

    def create(self, request, *args, **kwargs):
        print("CREATINMG")
        serializer = self.get_serializer(data=request.data, required=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=True, methods=["post"])
    def cart(self, request, pk=None):
        serializer = OrderSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        order = serializer.cart(serializer.validated_data, pk)
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
