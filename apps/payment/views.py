from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import PaymentTransaction
from apps.orders.models import Order
from .serializers import (
    CreatePaymentSerializer,
    PaymentResponseSerializer,
    VerifyPaymentSerializer
)

from .services.vandar_gateway import VandarApi

class CreatePaymentView(APIView):

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = get_object_or_404(
            Order,
            id=serializer.validated_data["order_id"],
            user=request.user
        )

        if order.is_paid:
            return Response(
                {"detail": "order already paid"},
                status=status.HTTP_400_BAD_REQUEST
            )

        vandar = VandarApi()

        result = vandar.create_transaction(
            amount=order.total_price,
            callback_url=settings.VANDAR_CALLBACK_URL
        )

        token = result["token"]
        payment_url = result["payment_url"]

        PaymentTransaction.objects.create(
            order=order,
            token=token,
            amount=order.total_price,
            gateway="vandar"
        )

        return Response(
            {
                "payment_url": payment_url,
                "token": token
            }
        )


class VerifyPaymentView(APIView):

    def post(self, request):

        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        status_code = serializer.validated_data["status"]

        transaction = get_object_or_404(
            PaymentTransaction,
            token=token
        )

        vandar = VandarApi()

        result = vandar.verify_transaction(token)

        if result["status"] == 1:

            transaction.status = "success"
            transaction.save()

            order = transaction.order
            order.status = Order.Status.PAID
            order.save()

            return Response({
                "detail": "payment successful"
            })

        transaction.status = "failed"
        transaction.save()

        return Response({
            "detail": "payment failed"
        }, status=400)


class PaymentStatusView(APIView):

    def get(self, request, token):

        transaction = get_object_or_404(
            PaymentTransaction,
            token=token,
            order__user=request.user
        )

        return Response({
            "status": transaction.status,
            "amount": transaction.amount,
            "created_at": transaction.created_at
        })
