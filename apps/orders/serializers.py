from rest_framework import serializers

from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="variant.product.name",
        read_only=True,
    )

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
            "product_name",
            "quantity",
            "unit_price",
            "subtotal",
        ]

        read_only_fields = [
            "id",
            "unit_price",
            "subtotal",
        ]

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
        
class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1, required=False)
    variant_id = serializers.IntegerField(min_value=1, required=False)
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        if bool(attrs.get("product_id")) == bool(attrs.get("variant_id")):
            raise serializers.ValidationError(
                "Provide exactly one of product_id or variant_id."
            )
        return attrs

class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemCreateSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "An order must contain at least one item."
            )

        item_keys = [
            ("variant", item["variant_id"])
            if item.get("variant_id") is not None
            else ("product", item["product_id"])
            for item in value
        ]

        if len(item_keys) != len(set(item_keys)):
            raise serializers.ValidationError(
                "A product or variant cannot appear more than once in an order."
            )

        return value