from rest_framework import serializers
from .models import PaymentTransaction


class CreatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()


class PaymentResponseSerializer(serializers.Serializer):
    payment_url = serializers.URLField()
    token = serializers.CharField()


class VerifyPaymentSerializer(serializers.Serializer):
    token = serializers.CharField()
    status = serializers.IntegerField()


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = "__all__"
