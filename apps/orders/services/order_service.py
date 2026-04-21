from django.core.exceptions import PermissionDenied
from apps.orders.models import Order


class OrderService:
    """
    Business logic for creating and modifying orders.
    Keeps views thin and maintainable.
    """

    @staticmethod
    def create_order(profile):
        """
        Create a new pending order for the user.
        You can extend this logic: load cart, calculate totals, etc.
        """
        return Order.objects.create(profile=profile, status="pending")

    @staticmethod
    def ensure_order_is_editable(order):
        """
        Ensures only pending orders can be modified.
        Prevents users from editing paid or shipped orders.
        """
        if order.status != "pending":
            raise PermissionDenied(
                "Only pending orders can be edited."
            )
        return True
