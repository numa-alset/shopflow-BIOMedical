from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Order, OrderItem


class OrderModelTests(TestCase):
    def test_shopify_order_id_has_no_generated_default(self):
        field = Order._meta.get_field("shopify_order_id")

        self.assertFalse(field.has_default())

    def test_line_item_can_preserve_shopify_data_without_local_variant(self):
        order = Order.objects.create(shopify_order_id="shopify-order-123")
        item = OrderItem.objects.create(
            order=order,
            shopify_variant_id="shopify-variant-456",
            sku_snapshot="SKU-123",
            product_title_snapshot="Test product",
            quantity=2,
            unit_price=Decimal("12.50"),
        )

        self.assertIsNone(item.variant)
        self.assertEqual(item.shopify_variant_id, "shopify-variant-456")
        self.assertEqual(item.sku_snapshot, "SKU-123")
        self.assertEqual(item.product_title_snapshot, "Test product")
        self.assertEqual(item.subtotal, Decimal("25.00"))

    def test_shopify_order_id_must_be_unique(self):
        Order.objects.create(shopify_order_id="123456")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Order.objects.create(shopify_order_id="123456")
