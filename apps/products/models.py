from django.db import models
from django.db.models import Sum, Case, When, F, IntegerField


class Category(models.Model):
    title = models.CharField(max_length=200)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.title


class Product(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")

    @property
    def stock(self):

        result = self.stock_transactions.aggregate(
            total=Sum(
                Case(
                    When(transaction_type="IN", then=F("quantity")),
                    When(transaction_type="OUT", then=-F("quantity")),
                    default=0,
                    output_field=IntegerField()
                )
            )
        )
        return result["total"] or 0


    def __str__(self):
        return self.title


class StockTransaction(models.Model):
    IN = "IN"
    OUT = "OUT"

    TYPES = (
        (IN, "Stock In"),
        (OUT, "Stock Out"),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_transactions")
    transaction_type = models.CharField(max_length=3, choices=TYPES)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.product.title} - {self.transaction_type} - {self.quantity}"
