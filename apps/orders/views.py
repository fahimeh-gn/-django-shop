from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.orders.models import Order
from apps.orders.serializers import (
    OrderSerializer,
    OrderAddressSerializer,
   
)
from apps.orders.services.order_service import OrderService
from rest_framework.permissions import IsAuthenticated


class OrderViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch"]

    serializer_class = OrderSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()

        if not self.request.user.is_authenticated:
            return Order.objects.none()

        return Order.objects.filter(profile=self.request.user.profile)

    def get_serializer_class(self):
        # Only for address action
        if self.action == "set_address":
            return OrderAddressSerializer

        # Default
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        order = OrderService.create_order(profile=request.user.profile)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def set_address(self, request, pk=None):
        order = self.get_object()
        OrderService.ensure_order_is_editable(order)

        serializer = OrderAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(order=order)

        return Response(OrderSerializer(order).data)
