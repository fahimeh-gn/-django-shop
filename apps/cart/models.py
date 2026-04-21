from django.db import models
from apps.accounts.models import Profile
from apps.products.models import Product


class Cart(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return sum(item.total() for item in self.items.all())

    def __str__(self):
        return f"Cart({self.profile.user.email})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"
