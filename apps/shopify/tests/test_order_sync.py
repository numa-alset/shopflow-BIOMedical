from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.orders.models import Order
from apps.products.models import Product, ProductVariant
from apps.shopify.services.order_sync import OrderSyncService


class OrderSyncServiceTests(TestCase):

    def setUp(self):
        self.service = OrderSyncService()
        self.payload = {
            "id": 456,
            "admin_graphql_api_id": "gid://shopify/Order/456",
            "email": "buyer@example.com",
            "currency": "CAD",
            "total_price": "25.00",
            "line_items": [
                {
                    "variant_id": 111,
                    "sku": "ORDER-SKU",
                    "title": "Purchased product",
                    "quantity": 2,
                    "price": "12.50",
                }
            ],
        }

    def test_syncs_order_and_matches_local_variant(self):
        product = Product.objects.create(
            shopify_product_id="gid://shopify/Product/1",
            name="Current product name",
            slug="current-product",
        )
        variant = ProductVariant.objects.create(
            shopify_variant_id="gid://shopify/ProductVariant/111",
            product=product,
            title="Default",
            sku="CURRENT-SKU",
            price=Decimal("15.00"),
        )

        order = self.service.sync_order(self.payload)
        item = order.items.get()

        self.assertEqual(order.shopify_order_id, "gid://shopify/Order/456")
        self.assertEqual(order.customer_email, "buyer@example.com")
        self.assertEqual(order.currency, "CAD")
        self.assertEqual(order.total, Decimal("25.00"))
        self.assertEqual(item.variant, variant)
        self.assertEqual(
            item.shopify_variant_id,
            "gid://shopify/ProductVariant/111",
        )
        self.assertEqual(item.sku_snapshot, "ORDER-SKU")
        self.assertEqual(item.product_title_snapshot, "Purchased product")
        self.assertEqual(item.unit_price, Decimal("12.50"))

    def test_syncs_line_item_without_local_variant(self):
        with self.assertLogs(
            "apps.shopify.services.order_sync",
            level="WARNING",
        ) as logs:
            order = self.service.sync_order(self.payload)

        item = order.items.get()

        self.assertIsNone(item.variant)
        self.assertEqual(item.shopify_variant_id, "gid://shopify/ProductVariant/111")
        self.assertIn("variant_id=gid://shopify/ProductVariant/111", logs.output[0])

    def test_rejects_negative_order_total(self):
        payload = {**self.payload, "total_price": "-1.00"}

        with self.assertRaises(ValidationError):
            self.service.sync_order(payload)

    def test_rejects_negative_line_item_price(self):
        payload = {
            **self.payload,
            "line_items": [
                {**self.payload["line_items"][0], "price": "-1.00"}
            ],
        }

        with self.assertRaises(ValidationError):
            self.service.sync_order(payload)

    def test_validates_customer_email_with_django_field(self):
        payload = {**self.payload, "email": "not-an-email"}

        with self.assertRaises(ValidationError):
            self.service.sync_order(payload)

    def test_repeated_sync_does_not_duplicate_order_or_items(self):
        first_order = self.service.sync_order(self.payload)
        second_order = self.service.sync_order(self.payload)

        self.assertEqual(first_order.pk, second_order.pk)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(first_order.items.count(), 1)
