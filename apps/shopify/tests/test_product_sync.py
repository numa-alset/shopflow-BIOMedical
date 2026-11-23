from django.test import TestCase

from apps.products.models import Product, ProductVariant

from apps.shopify.services.product_sync import ProductSyncService

from decimal import Decimal


# ==================================================
# MOCK SHOPIFY PRODUCT SERVICE
# ==================================================

class MockShopifyProductService:
    """
    Mock Shopify API responses.

    This prevents tests from making real HTTP requests.
    """

    def __init__(self, products=None):

        self.products = products or []

    def get_products(self):

        return self.products


# ==================================================
# PRODUCT SYNC TESTS
# ==================================================

class ProductSyncServiceTests(TestCase):

    def setUp(self):

        self.shopify_product = {
            "id": "gid://shopify/Product/123456",

            "title": "Zelt Fjell 2P",

            "handle": "zelt-fjell-2p",

            "descriptionHtml": "<p>Outdoor tent</p>",

            "status": "ACTIVE",

            "variants": [

                {
                    "id": "gid://shopify/ProductVariant/111",

                    "title": "L / Gray",

                    "sku": "NL-ZELT-2P-1",

                    "price": "50.00",

                    "inventoryQuantity": 10,

                    "inventoryItem": {
                        "id": "gid://shopify/InventoryItem/111",
                        "tracked": True,
                    },
                },

                {
                    "id": "gid://shopify/ProductVariant/222",

                    "title": "L / Gold",

                    "sku": "NL-ZELT-2P-2",

                    "price": "50.00",

                    "inventoryQuantity": 5,

                    "inventoryItem": {
                        "id": "gid://shopify/InventoryItem/222",
                        "tracked": True,
                    },
                },
            ],
        }

        self.mock_product_service = MockShopifyProductService(
            products=[self.shopify_product]
        )

        self.service = ProductSyncService(
            product_service=self.mock_product_service
        )

    # --------------------------------------------------
    # TEST 1: CREATE PRODUCT
    # --------------------------------------------------

    def test_create_product(self):

        result = self.service.sync_product(
            self.shopify_product
        )

        self.assertTrue(result["product_created"])

        self.assertEqual(Product.objects.count(), 1)

        product = Product.objects.get(
            shopify_product_id="gid://shopify/Product/123456"
        )

        self.assertEqual(product.name, "Zelt Fjell 2P")

        self.assertEqual(product.slug, "zelt-fjell-2p")

        self.assertEqual(product.status, "ACTIVE")

    # --------------------------------------------------
    # TEST 2: CREATE VARIANTS
    # --------------------------------------------------

    def test_create_product_variants(self):

        result = self.service.sync_product(
            self.shopify_product
        )

        self.assertEqual(
            result["variants_created"],
            2,
        )

        self.assertEqual(
            result["variants_updated"],
            0,
        )

        self.assertEqual(
            ProductVariant.objects.count(),
            2,
        )

        variant = ProductVariant.objects.get(
            shopify_variant_id="gid://shopify/ProductVariant/111"
        )

        self.assertEqual(variant.sku, "NL-ZELT-2P-1")

        self.assertEqual(variant.price, Decimal("50.00"))

        self.assertEqual(variant.inventory_quantity, 10)

        self.assertEqual(
            variant.shopify_inventory_item_id,
            "gid://shopify/InventoryItem/111",
        )

    # --------------------------------------------------
    # TEST 3: UPDATE EXISTING PRODUCT
    # --------------------------------------------------

    def test_update_existing_product(self):

        self.service.sync_product(
            self.shopify_product
        )

        updated_product = {
            **self.shopify_product,

            "title": "Zelt Fjell 2P Updated",

            "status": "DRAFT",
        }

        result = self.service.sync_product(
            updated_product
        )

        self.assertFalse(result["product_created"])

        self.assertEqual(Product.objects.count(), 1)

        product = Product.objects.get(
            shopify_product_id="gid://shopify/Product/123456"
        )

        self.assertEqual(
            product.name,
            "Zelt Fjell 2P Updated",
        )

        self.assertEqual(product.status, "DRAFT")

    # --------------------------------------------------
    # TEST 4: UPDATE EXISTING VARIANTS
    # --------------------------------------------------

    def test_update_existing_variants(self):

        self.service.sync_product(
            self.shopify_product
        )

        updated_product = {
            **self.shopify_product,

            "variants": [
                {
                    **self.shopify_product["variants"][0],

                    "price": "60.00",

                    "inventoryQuantity": 3,
                },
                self.shopify_product["variants"][1],
            ],
        }

        result = self.service.sync_product(
            updated_product
        )

        self.assertEqual(
            result["variants_created"],
            0,
        )

        self.assertEqual(
            result["variants_updated"],
            2,
        )

        variant = ProductVariant.objects.get(
            shopify_variant_id="gid://shopify/ProductVariant/111"
        )

        self.assertEqual(variant.price, Decimal("60.00"))

        self.assertEqual(variant.inventory_quantity, 3)

    # --------------------------------------------------
    # TEST 5: PREVENT DUPLICATE PRODUCTS AND VARIANTS
    # --------------------------------------------------

    def test_sync_does_not_create_duplicates(self):

        self.service.sync_product(
            self.shopify_product
        )

        self.service.sync_product(
            self.shopify_product
        )

        self.assertEqual(Product.objects.count(), 1)

        self.assertEqual(ProductVariant.objects.count(), 2)

    # --------------------------------------------------
    # TEST 6: HANDLE MISSING SKU
    # --------------------------------------------------

    def test_variant_without_sku(self):

        product = {
            **self.shopify_product,

            "variants": [
                {
                    "id": "gid://shopify/ProductVariant/333",

                    "title": "Green / 13",

                    "sku": None,

                    "price": "40.00",

                    "inventoryQuantity": 0,

                    "inventoryItem": {
                        "id": "gid://shopify/InventoryItem/333",
                        "tracked": True,
                    },
                }
            ],
        }

        result = self.service.sync_product(product)

        self.assertEqual(result["variants_created"], 1)

        variant = ProductVariant.objects.get(
            shopify_variant_id="gid://shopify/ProductVariant/333"
        )

        self.assertEqual(variant.sku, "")

        self.assertEqual(variant.inventory_quantity, 0)

    # --------------------------------------------------
    # TEST 7: HANDLE MISSING INVENTORY ITEM
    # --------------------------------------------------

    def test_variant_without_inventory_item(self):

        product = {
            **self.shopify_product,

            "variants": [
                {
                    "id": "gid://shopify/ProductVariant/444",

                    "title": "Default",

                    "sku": None,

                    "price": "40.00",

                    "inventoryQuantity": 0,

                    "inventoryItem": None,
                }
            ],
        }

        self.service.sync_product(product)

        variant = ProductVariant.objects.get(
            shopify_variant_id="gid://shopify/ProductVariant/444"
        )

        self.assertIsNone(
            variant.shopify_inventory_item_id
        )

    # --------------------------------------------------
    # TEST 8: PRESERVE MINIMUM STOCK
    # --------------------------------------------------

    def test_sync_preserves_minimum_stock(self):

        self.service.sync_product(
            self.shopify_product
        )

        variant = ProductVariant.objects.get(
            shopify_variant_id="gid://shopify/ProductVariant/111"
        )

        variant.minimum_stock = 5

        variant.save()

        updated_product = {
            **self.shopify_product,

            "variants": [
                {
                    **self.shopify_product["variants"][0],

                    "inventoryQuantity": 2,
                },
                self.shopify_product["variants"][1],
            ],
        }

        self.service.sync_product(
            updated_product
        )

        variant.refresh_from_db()

        self.assertEqual(
            variant.inventory_quantity,
            2,
        )

        self.assertEqual(
            variant.minimum_stock,
            5,
        )

        self.assertEqual(
            variant.stock_status,
            "low_stock",
        )

    # --------------------------------------------------
    # TEST 9: ROLLBACK ON INVALID VARIANT DATA
    # --------------------------------------------------

    def test_invalid_variant_rolls_back_product_creation(self):

        invalid_product = {
            **self.shopify_product,

            "variants": [
                self.shopify_product["variants"][0],

                {
                    **self.shopify_product["variants"][1],

                    "price": "invalid-price",
                },
            ],
        }

        with self.assertRaises(ValueError):

            self.service.sync_product(
                invalid_product
            )

        self.assertEqual(Product.objects.count(), 0)

        self.assertEqual(ProductVariant.objects.count(), 0)

    # --------------------------------------------------
    # TEST 10: SYNC ALL PRODUCTS AND RETURN STATISTICS
    # --------------------------------------------------

    def test_sync_products_returns_correct_statistics(self):

        result = self.service.sync_products()

        self.assertEqual(
            result,
            {
                "success": True,
                "products_created": 1,
                "products_updated": 0,
                "variants_created": 2,
                "variants_updated": 0,
            },
        )

    # --------------------------------------------------
    # TEST 11: SECOND SYNC UPDATES EXISTING RECORDS
    # --------------------------------------------------

    def test_second_sync_updates_without_creating_duplicates(self):

        self.service.sync_products()

        result = self.service.sync_products()

        self.assertEqual(
            result["products_created"],
            0,
        )

        self.assertEqual(
            result["products_updated"],
            1,
        )

        self.assertEqual(
            result["variants_created"],
            0,
        )

        self.assertEqual(
            result["variants_updated"],
            2,
        )

        self.assertEqual(Product.objects.count(), 1)

        self.assertEqual(ProductVariant.objects.count(), 2)