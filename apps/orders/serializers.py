from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):

    product_name = serializers.SerializerMethodField()

    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "variant",
            "shopify_variant_id",
            "sku_snapshot",
            "product_title_snapshot",
            "product_name",
            "quantity",
            "unit_price",
            "subtotal",
        ]

        read_only_fields = [
            "id",
            "variant",
            "shopify_variant_id",
            "sku_snapshot",
            "product_title_snapshot",
            "unit_price",
            "subtotal",
        ]

    def get_product_name(self, obj):
        return obj.product_title_snapshot or (
            obj.variant.product.name if obj.variant_id else ""
        )


class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_email",
            "status",
            "total",
            "items",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "total",
            "created_at",
        ]
