from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.serializers import ProductSerializer
from decimal import Decimal
from drf_spectacular.utils import extend_schema_field



class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total']

    def get_total(self, obj):
        return obj.total()
    
class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']

    @extend_schema_field(Decimal)
    def get_total_price(self, obj):
        if obj is None:
            return Decimal("0.00")

        return sum(
            (item.total() for item in obj.items.all()),
            Decimal("0.00")
        )

class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1)


