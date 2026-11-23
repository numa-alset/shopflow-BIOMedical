from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from apps.products.models import Product, ProductVariant
from apps.products.selector.product_selector import (
    get_active_products,
    get_low_stock_variants,
    get_out_of_stock_variants,
    get_product_by_sku,
)


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


class ProductSelectorTests(TestCase):

    def setUp(self):
        self.active_product = Product.objects.create(
            shopify_product_id="gid://shopify/Product/200",
            name="Active Product",
            slug="active-product",
            status="ACTIVE",
        )
        self.inactive_product = Product.objects.create(
            shopify_product_id="gid://shopify/Product/201",
            name="Draft Product",
            slug="draft-product",
            status="DRAFT",
        )

    def create_variant(self, product, sku, inventory, minimum=None):
        return ProductVariant.objects.create(
            shopify_variant_id=f"variant-{sku}",
            product=product,
            title=sku,
            sku=sku,
            price="10.00",
            inventory_quantity=inventory,
            minimum_stock=minimum,
        )

    def test_get_active_products_filters_by_status(self):
        self.assertQuerySetEqual(
            get_active_products(),
            [self.active_product],
        )

    def test_get_product_by_sku_returns_matching_variant(self):
        variant = self.create_variant(self.active_product, "SKU-1", 10)

        self.assertEqual(get_product_by_sku("SKU-1"), variant)

    def test_get_low_stock_variants_excludes_out_of_stock_and_unconfigured(self):
        low_stock = self.create_variant(self.active_product, "LOW", 4, minimum=5)
        self.create_variant(self.active_product, "OUT", 0, minimum=5)
        self.create_variant(self.active_product, "NO-MINIMUM", 4)
        self.create_variant(self.active_product, "NORMAL", 5, minimum=5)

        self.assertQuerySetEqual(get_low_stock_variants(), [low_stock])

    def test_get_out_of_stock_variants_includes_zero_and_negative_inventory(self):
        zero_stock = self.create_variant(self.active_product, "ZERO", 0)
        negative_stock = self.create_variant(self.active_product, "NEGATIVE", -1)
        self.create_variant(self.active_product, "IN-STOCK", 1)

        self.assertQuerySetEqual(
            get_out_of_stock_variants(),
            [negative_stock, zero_stock],
        )


class ProductInventoryAPITests(APITestCase):

    def setUp(self):
        self.product = Product.objects.create(
            shopify_product_id="gid://shopify/Product/300",
            name="Inventory Product",
            slug="inventory-product",
            status="ACTIVE",
        )
        self.normal_variant = ProductVariant.objects.create(
            shopify_variant_id="variant-normal",
            product=self.product,
            title="Normal",
            sku="NORMAL-SKU",
            price="25.00",
            inventory_quantity=20,
            minimum_stock=10,
        )
        self.low_variant = ProductVariant.objects.create(
            shopify_variant_id="variant-low",
            product=self.product,
            title="Low",
            sku="LOW-SKU",
            price="15.00",
            inventory_quantity=5,
            minimum_stock=10,
        )
        self.out_variant = ProductVariant.objects.create(
            shopify_variant_id="variant-out",
            product=self.product,
            title="Out",
            sku="OUT-SKU",
            price="12.00",
            inventory_quantity=0,
            minimum_stock=10,
        )

    def test_product_detail_includes_variants_and_stock_status(self):
        url = reverse("product-detail", args=[self.product.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Inventory Product")
        self.assertEqual(len(response.data["variants"]), 3)
        statuses = {
            variant["sku"]: variant["stock_status"]
            for variant in response.data["variants"]
        }
        self.assertEqual(statuses["NORMAL-SKU"], "normal")
        self.assertEqual(statuses["LOW-SKU"], "low_stock")
        self.assertEqual(statuses["OUT-SKU"], "out_of_stock")

    def test_inventory_list_returns_variant_quantities(self):
        url = reverse("product-variant-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inventory = {
            variant["sku"]: variant["inventory_quantity"]
            for variant in response.data
        }
        self.assertEqual(inventory["NORMAL-SKU"], 20)
        self.assertEqual(inventory["LOW-SKU"], 5)
        self.assertEqual(inventory["OUT-SKU"], 0)

    def test_low_stock_filter(self):
        url = reverse("product-variant-low-stock")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [variant["sku"] for variant in response.data],
            ["LOW-SKU"],
        )

    def test_out_of_stock_filter(self):
        url = reverse("product-variant-out-of-stock")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [variant["sku"] for variant in response.data],
            ["OUT-SKU"],
        )

    def test_admin_can_update_minimum_stock(self):
        user = get_user_model().objects.create_superuser(
            username="inventory-admin",
            email="inventory-admin@example.com",
            password="test-password",
        )
        self.client.force_authenticate(user=user)
        url = reverse(
            "product-variant-update-minimum-stock",
            args=[self.low_variant.id],
        )

        response = self.client.patch(
            url,
            {"minimum_stock": 15},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.low_variant.refresh_from_db()
        self.assertEqual(self.low_variant.minimum_stock, 15)
        self.assertEqual(self.low_variant.stock_status, "low_stock")