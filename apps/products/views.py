from django.db.models import F
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .models import Product, ProductVariant
from .serializers import (
    ProductSerializer,
    ProductVariantSerializer,
    UpdateMinimumStockSerializer,
)
from .services.product_service import (
    InvalidMinimumStockError,
    ProductVariantNotFoundError,
    update_variant_minimum_stock,
)


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.prefetch_related("variants").all()
    serializer_class = ProductSerializer

    filterset_fields = ["status"]
    search_fields = ["name", "description", "slug", "shopify_product_id"]
    ordering_fields = ["created_at", "name", "status"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]


class ProductVariantViewSet(ReadOnlyModelViewSet):
    queryset = ProductVariant.objects.select_related("product").all()
    serializer_class = ProductVariantSerializer
    filterset_fields = ["product", "sku"]
    search_fields = ["sku", "title", "product__name"]
    ordering_fields = [
        "inventory_quantity",
        "minimum_stock",
        "sku",
        "created_at",
    ]
    ordering = ["sku"]

    def get_permissions(self):
        if self.action in ["list", "retrieve", "low_stock", "out_of_stock"]:
            return [AllowAny()]
        return [IsAdminUser()]

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        variants = self.filter_queryset(
            ProductVariant.objects.select_related("product").filter(
                inventory_quantity__gt=0,
                minimum_stock__isnull=False,
                inventory_quantity__lt=F("minimum_stock"),
            )
        )
        page = self.paginate_queryset(variants)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(variants, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="out-of-stock")
    def out_of_stock(self, request):
        variants = self.filter_queryset(
            ProductVariant.objects.select_related("product").filter(
                inventory_quantity__lte=0
            )
        )
        page = self.paginate_queryset(variants)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(variants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"], url_path="minimum-stock")
    def update_minimum_stock(self, request, pk=None):
        serializer = UpdateMinimumStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            variant = update_variant_minimum_stock(
                variant_id=int(pk),
                minimum_stock=serializer.validated_data["minimum_stock"],
            )
        except ProductVariantNotFoundError:
            return Response(
                {"detail": "Product variant not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except InvalidMinimumStockError as error:
            return Response(
                {"minimum_stock": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ProductVariantSerializer(variant).data,
            status=status.HTTP_200_OK,
        )