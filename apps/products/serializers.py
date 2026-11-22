from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product

        fields = [
            'id',
            'name',
            'slug',
            'description',
            'sku',
            'price',
            'stock',
            'is_active',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]

class UpdateStockSerializer(serializers.Serializer):
    stock = serializers.IntegerField(min_value=0)