from django.db import models
from django.utils import timezone
from apps.orders.models import Order   

class PaymentTransaction(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    gateway = models.CharField(max_length=50, default="vandar")

    token = models.CharField(max_length=255, unique=True)

    amount = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    response_data = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.gateway} | {self.order.id} | {self.status}"
