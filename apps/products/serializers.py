from rest_framework import serializers

from .models import Product, ProductVariant


class ProductVariantSerializer(serializers.ModelSerializer):
    stock_status = serializers.CharField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "shopify_variant_id",
            "title",
            "sku",
            "price",
            "inventory_quantity",
            "minimum_stock",
            "stock_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "shopify_variant_id",
            "inventory_quantity",
            "stock_status",
            "created_at",
            "updated_at",
        ]


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "shopify_product_id",
            "name",
            "slug",
            "description",
            "status",
            "variants",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "shopify_product_id",
            "variants",
            "created_at",
            "updated_at",
        ]


class UpdateMinimumStockSerializer(serializers.Serializer):
    minimum_stock = serializers.IntegerField(
        min_value=0,
        allow_null=True,
        required=True,
    )