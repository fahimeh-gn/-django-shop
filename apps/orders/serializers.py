from rest_framework import serializers
from apps.orders.models import Order, OrderItem, OrderAddress
from apps.products.serializers import SimpleProductSerializer


# --------------------------------------------------------------
# Order Item Serializer (Read-only)
# --------------------------------------------------------------
class OrderItemSerializer(serializers.ModelSerializer):
    """
    Represents a single product within an order.
    Items are never edited directly from Order API.
    """
    product = SimpleProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "quantity",
            "price_at_purchase",
        ]
        read_only_fields = fields


# --------------------------------------------------------------
# Order Address Serializer
# --------------------------------------------------------------
class OrderAddressSerializer(serializers.ModelSerializer):
    """
    Shipping address for an order.
    The 'order' field is read-only because it is assigned internally.
    """

    class Meta:
        model = OrderAddress
        fields = [
            "id",
            "full_name",
            "phone",
            "province",
            "city",
            "street",
            "postal_code",
            "order",
        ]
        read_only_fields = ["id", "order"]

# --------------------------------------------------------------
# Full Order Serializer (GET only)
# --------------------------------------------------------------
class OrderSerializer(serializers.ModelSerializer):
    """
    Full representation of an order including items and address.
    Used ONLY for responses, not updates.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    address = OrderAddressSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "total_price",
            "total_items",
            "tracking_code",
            "items",
            "address",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


