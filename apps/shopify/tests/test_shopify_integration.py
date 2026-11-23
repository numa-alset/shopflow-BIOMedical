#Command to run the integration tests:
# $env:RUN_SHOPIFY_INTEGRATION_TESTS="1"

# python manage.py test apps.shopify.tests.test_shopify_integration --verbosity 2

import os
import unittest

from django.test import TestCase

from apps.products.models import Product, ProductVariant
from apps.shopify.client import ShopifyClient
from apps.shopify.services.product_sync import (
    ShopifyProductService,
    ProductSyncService,
)


RUN_SHOPIFY_INTEGRATION_TESTS = (
    os.getenv("RUN_SHOPIFY_INTEGRATION_TESTS") == "1"
)


@unittest.skipUnless(
    RUN_SHOPIFY_INTEGRATION_TESTS,
    "Set RUN_SHOPIFY_INTEGRATION_TESTS=1 to run Shopify integration tests.",
)
class ShopifyConnectionIntegrationTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Use a separate name to avoid Django's self.client.
        cls.shopify_client = ShopifyClient()

    def test_real_shopify_connection(self):
        shop = self.shopify_client.test_connection()

        self.assertTrue(shop["name"])
        self.assertTrue(shop["myshopifyDomain"])

    def test_retrieve_real_products(self):
        service = ShopifyProductService(
            client=self.shopify_client
        )

        products = service.get_products()

        self.assertGreater(len(products), 0)

        for product in products:
            self.assertTrue(product["id"])
            self.assertTrue(product["title"])
            self.assertIn("variants", product)

            for variant in product["variants"]:
                self.assertTrue(variant["id"])
                self.assertIsNotNone(variant["price"])
                self.assertIn("inventoryQuantity", variant)

    def test_real_shopify_product_sync(self):
        product_service = ShopifyProductService(
            client=self.shopify_client
        )

        sync_service = ProductSyncService(
            product_service=product_service
        )

        result = sync_service.sync_products()

        self.assertTrue(result["success"])

        total_synced = (
            result["products_created"]
            + result["products_updated"]
        )

        self.assertGreater(total_synced, 0)

        # Verify Shopify products against the test database.
        shopify_products = product_service.get_products()

        for shopify_product in shopify_products:
            database_product = Product.objects.get(
                shopify_product_id=shopify_product["id"]
            )

            self.assertEqual(
                database_product.name,
                shopify_product["title"],
            )

            for shopify_variant in shopify_product["variants"]:
                database_variant = ProductVariant.objects.get(
                    shopify_variant_id=shopify_variant["id"]
                )

                self.assertEqual(
                    database_variant.inventory_quantity,
                    shopify_variant["inventoryQuantity"],
                )

                expected_inventory_item_id = (
                    shopify_variant.get("inventoryItem") or {}
                ).get("id")

                self.assertEqual(
                    database_variant.shopify_inventory_item_id,
                    expected_inventory_item_id,
                )
