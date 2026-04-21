from rest_framework import viewsets, filters
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from rest_framework.permissions import AllowAny


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'head', 'options']


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["price"]

    http_method_names = ['get', 'head', 'options']



