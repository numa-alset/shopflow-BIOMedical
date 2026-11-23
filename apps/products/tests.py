from django.test import TestCase

from apps.products.models import Product, ProductVariant


class ProductVariantStockStatusTests(TestCase):

    def setUp(self):
        self.product = Product.objects.create(
            shopify_product_id="gid://shopify/Product/100",
            name="Test Product",
            slug="test-product",
        )

    def create_variant(self, inventory, minimum):
        return ProductVariant.objects.create(
            shopify_variant_id=f"variant-{inventory}-{minimum}",
            product=self.product,
            title="Test Variant",
            price="10.00",
            inventory_quantity=inventory,
            minimum_stock=minimum,
        )

    def test_normal_stock(self):
        variant = self.create_variant(20, 10)

        self.assertEqual(variant.stock_status, "normal")

    def test_low_stock(self):
        variant = self.create_variant(5, 10)

        self.assertEqual(variant.stock_status, "low_stock")

    def test_out_of_stock(self):
        variant = self.create_variant(0, 5)

        self.assertEqual(variant.stock_status, "out_of_stock")

    def test_negative_inventory_is_out_of_stock(self):
        variant = self.create_variant(-1, 5)

        self.assertEqual(variant.stock_status, "out_of_stock")

    def test_minimum_stock_not_configured(self):
        variant = self.create_variant(10, None)

        self.assertEqual(variant.stock_status, "not_configured")

    def test_inventory_equal_to_minimum_is_normal(self):
        variant = self.create_variant(10, 10)

        self.assertEqual(variant.stock_status, "normal")