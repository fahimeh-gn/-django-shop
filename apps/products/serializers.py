from rest_framework import serializers
from .models import Product, Category


# -------------------------------
#  Child serializer (minimal)
# -------------------------------
class CategoryChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title"]


# -------------------------------
#  Full Category Tree Serializer
# -------------------------------
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "title", "parent", "children"]
        extra_kwargs = {
            "parent": {"write_only": True}
        }

    def get_children(self, obj):
        return CategoryChildSerializer(obj.children.all(), many=True).data


# -------------------------------
#  Simple category for product (NO CHILDREN)
# -------------------------------
class SimpleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title"]


# -------------------------------
#  Product Serializer (SAFE)
# -------------------------------
class ProductSerializer(serializers.ModelSerializer):
    # Only show minimal category info → avoids recursion & 500
    category = SimpleCategorySerializer(read_only=True)

    # Required for POST/PUT
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "description",
            "price",
            "stock",
            "category",
            "category_id",
        ]
        read_only_fields = ["stock"]
# -------------------------------------------------
# Simple Product Serializer (FOR ORDER ITEMS)
# -------------------------------------------------
class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "title", "price", "stock"]
