from django.db import transaction
from django.core.exceptions import PermissionDenied

from apps.orders.models import Order, OrderItem
from apps.cart.models import Cart


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order(profile):

        try:
            cart = Cart.objects.get(profile=profile)
        except Cart.DoesNotExist:
            raise PermissionDenied("Cart not found")

        cart_items = cart.items.all()

        if not cart_items.exists():
            raise PermissionDenied("Cart is empty")

        order = Order.objects.create(profile=profile)

        total_price = 0
        total_items = 0

        for item in cart_items:
            price = item.product.price

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_purchase=price
            )

            total_price += price * item.quantity
            total_items += item.quantity

        order.total_price = total_price
        order.total_items = total_items
        order.save()

        cart_items.delete()

        return order

    @staticmethod
    def ensure_order_is_editable(order):
        if order.status != Order.Status.PENDING:
            raise PermissionDenied("Only pending orders can be edited.")
