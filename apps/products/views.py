from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Product
from .serializers import ProductSerializer, UpdateStockSerializer
from rest_framework.permissions import AllowAny, IsAdminUser

from .services.product_service import (
    update_product_stock,
    ProductNotFoundError,
    InvalidStockError,
)


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    filterset_fields = ["is_active", "price"]
    search_fields = ["name", "description", "sku"]
    ordering_fields = ["price", "created_at", "name"]
    ordering = ["-created_at"]

    def get_permissions(self):
     if self.action in ["list", "retrieve"]:
        return [AllowAny()]

     return [IsAdminUser()]

    @action(detail=True, methods=["patch"], url_path="stock")
    def update_stock(self, request, pk=None):
        serializer = UpdateStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            product = update_product_stock(
                product_id=int(pk),
                new_stock=serializer.validated_data["stock"],
            )
        except ProductNotFoundError:
            raise NotFound("Product not found.")
        except InvalidStockError as error:
            raise ValidationError({"stock": str(error)})

        return Response(
            {
                "message": "Product stock updated successfully.",
                "data": ProductSerializer(product).data,
            },
            status=status.HTTP_200_OK,
        )