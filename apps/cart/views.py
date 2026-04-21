from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from .models import Cart, CartItem
from apps.products.models import Product
from .serializers import CartSerializer, AddToCartSerializer
from .serializers import UpdateCartItemSerializer


class CartView(GenericAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=CartSerializer,
        summary="Get current user's cart"
    )
    def get(self, request):
        profile = request.user.profile
        cart, _ = Cart.objects.get_or_create(profile=profile)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)


class AddToCartView(GenericAPIView):
    serializer_class = AddToCartSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AddToCartSerializer,
        responses={200: None},
    )
    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        profile = request.user.profile
        cart, _ = Cart.objects.get_or_create(profile=profile)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "product not found"}, status=404)

        if product.stock < quantity:
            return Response(
                {"error": "stock not available", "available_stock": product.stock},
                status=400,
            )

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )

        if not created:
            new_quantity = item.quantity + quantity
            if new_quantity > product.stock:
                return Response(
                    {"error": "not enough stock for update", "available_stock": product.stock},
                    status=400,
                )
            item.quantity = new_quantity
            item.save()

        return Response({"message": "added to cart"}, status=200)






class UpdateCartItemView(GenericAPIView):
    serializer_class = UpdateCartItemSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=UpdateCartItemSerializer,
        responses={200: None},
        summary="Update quantity of a product in cart"
    )
    def patch(self, request, product_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]

        profile = request.user.profile
        cart = Cart.objects.filter(profile=profile).first()
        if not cart:
            return Response({"error": "cart is empty"}, status=404)

        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
        except CartItem.DoesNotExist:
            return Response({"error": "item not found in cart"}, status=404)

        product = item.product

        # چک موجودی
        if quantity > product.stock:
            return Response(
                {
                    "error": "not enough stock",
                    "available_stock": product.stock
                },
                status=400
            )

        item.quantity = quantity
        item.save()

        return Response({"message": "quantity updated"}, status=200)
    

class RemoveFromCartView(GenericAPIView):
    serializer_class = CartSerializer   
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={204: None},
        summary="Remove a product from user's cart"
    )
    def delete(self, request, product_id):
        profile = request.user.profile
        cart = get_object_or_404(Cart, profile=profile)
        item = get_object_or_404(CartItem, cart=cart, product__id=product_id)
        item.delete()
        return Response({"message": "Removed"}, status=status.HTTP_204_NO_CONTENT)
