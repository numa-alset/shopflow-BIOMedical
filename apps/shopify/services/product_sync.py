from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.utils.text import slugify

from apps.products.models import Product, ProductVariant

from apps.shopify.client import ShopifyClient, ShopifyAPIError


# ==================================================
# GRAPHQL QUERIES
# ==================================================

PRODUCTS_QUERY = """
query GetProducts($first: Int!, $after: String) {

    products(first: $first, after: $after) {

        edges {

            node {

                id
                title
                handle
                descriptionHtml

                vendor
                productType
                status

                createdAt
                updatedAt

                variants(first: 100) {

                    edges {

                        node {

                            id
                            title
                            sku
                            price

                            inventoryQuantity

                            inventoryItem {
                                id
                                tracked
                            }

                        }
                    }

                    pageInfo {
                        hasNextPage
                        endCursor
                    }

                }

            }
        }

        pageInfo {
            hasNextPage
            endCursor
        }

    }
}
"""


PRODUCT_VARIANTS_QUERY = """
query GetProductVariants(
    $productId: ID!,
    $first: Int!,
    $after: String
) {

    product(id: $productId) {

        variants(first: $first, after: $after) {

            edges {

                node {

                    id
                    title
                    sku
                    price

                    inventoryQuantity

                    inventoryItem {
                        id
                        tracked
                    }

                }
            }

            pageInfo {
                hasNextPage
                endCursor
            }

        }
    }
}
"""


# ==================================================
# SHOPIFY PRODUCT RETRIEVAL
# ==================================================

class ShopifyProductService:

    def __init__(self, client=None):

        self.client = client or ShopifyClient()

    def _get_all_variants(self, product):

        connection = product.get("variants", {})

        variants = [
            edge["node"]
            for edge in connection.get("edges", [])
        ]

        page_info = connection.get("pageInfo", {})

        while page_info.get("hasNextPage"):

            cursor = page_info.get("endCursor")

            if not cursor:
                raise ShopifyAPIError(
                    "Variant pagination returned no cursor."
                )

            data = self.client.graphql(
                PRODUCT_VARIANTS_QUERY,
                {
                    "productId": product["id"],
                    "first": 100,
                    "after": cursor,
                },
            )

            product_data = data.get("product")

            if not product_data:
                raise ShopifyAPIError(
                    f"Product {product['id']} was not found."
                )

            connection = product_data.get("variants", {})

            variants.extend(
                edge["node"]
                for edge in connection.get("edges", [])
            )

            page_info = connection.get("pageInfo", {})

        return variants

    def get_products(self):

        products = []

        cursor = None

        while True:

            data = self.client.graphql(
                PRODUCTS_QUERY,
                {
                    "first": 50,
                    "after": cursor,
                },
            )

            connection = data.get("products")

            if not isinstance(connection, dict):
                raise ShopifyAPIError(
                    "Invalid Shopify products response."
                )

            for edge in connection.get("edges", []):

                product = edge["node"]

                product["variants"] = self._get_all_variants(
                    product
                )

                products.append(product)

            page_info = connection.get("pageInfo", {})

            if not page_info.get("hasNextPage"):
                break

            cursor = page_info.get("endCursor")

            if not cursor:
                raise ShopifyAPIError(
                    "Product pagination returned no cursor."
                )

        return products

    def get_product(self, product_id):

        query = """
        query GetProduct($id: ID!) {

            product(id: $id) {

                id
                title
                handle
                descriptionHtml
                status

                variants(first: 100) {

                    edges {

                        node {
                            id
                            title
                            sku
                            price
                            inventoryQuantity

                            inventoryItem {
                                id
                                tracked
                            }
                        }
                    }

                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        }
        """

        data = self.client.graphql(
            query,
            {"id": product_id},
        )

        product = data.get("product")

        if product:
            product["variants"] = self._get_all_variants(
                product
            )

        return product


# ==================================================
# PRODUCT SYNCHRONIZATION
# ==================================================

class ProductSyncService:

    def __init__(self, product_service=None):

        self.product_service = (
            product_service or ShopifyProductService()
        )

    @staticmethod
    def _validate_product(shopify_product):

        if not shopify_product.get("id"):
            raise ValueError("Shopify product ID is missing.")

        if not shopify_product.get("title"):
            raise ValueError("Shopify product title is missing.")

        if not shopify_product.get("handle"):
            raise ValueError("Shopify product handle is missing.")

    @staticmethod
    def _validate_variant(shopify_variant):

        if not shopify_variant.get("id"):
            raise ValueError("Shopify variant ID is missing.")

        if shopify_variant.get("price") is None:
            raise ValueError("Shopify variant price is missing.")

        try:
            price = Decimal(str(shopify_variant["price"]))

        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValueError("Invalid Shopify variant price.") from error

        if not price.is_finite() or price < 0:
            raise ValueError("Shopify variant price must be non-negative.")

        return price

    @staticmethod
    def _get_product_defaults(shopify_product):

        return {
            "name": shopify_product["title"],
            "slug": slugify(shopify_product["handle"]),
            "description": shopify_product.get(
                "descriptionHtml"
            ) or "",
            "status": shopify_product.get("status", "ACTIVE"),
        }

    @staticmethod
    def _get_variant_defaults(shopify_variant, product):

        price = ProductSyncService._validate_variant(
            shopify_variant
        )

        inventory_item = shopify_variant.get("inventoryItem") or {}

        inventory_quantity = (
            shopify_variant.get("inventoryQuantity")
        )

        if inventory_quantity is None:
            inventory_quantity = 0

        inventory_quantity = int(inventory_quantity)

        if inventory_quantity < 0:
            raise ValueError(
                "Shopify inventory quantity cannot be negative."
            )

        return {
            "product": product,
            "title": shopify_variant.get("title") or "Default",
            "sku": shopify_variant.get("sku") or "",
            "price": price,
            "inventory_quantity": inventory_quantity,
            "shopify_inventory_item_id": inventory_item.get("id"),
        }

    # --------------------------------------------------
    # SYNC ONE PRODUCT
    # --------------------------------------------------

    @transaction.atomic
    def sync_product(self, shopify_product):

        self._validate_product(shopify_product)

        product_defaults = self._get_product_defaults(
            shopify_product
        )

        try:

            product, product_created = (
                Product.objects.update_or_create(
                    shopify_product_id=shopify_product["id"],
                    defaults=product_defaults,
                )
            )

            variants_created = 0
            variants_updated = 0

            for shopify_variant in shopify_product.get(
                "variants", []
            ):

                variant_defaults = self._get_variant_defaults(
                    shopify_variant,
                    product,
                )

                variant, variant_created = (
                    ProductVariant.objects.update_or_create(
                        shopify_variant_id=shopify_variant["id"],
                        defaults=variant_defaults,
                    )
                )

                if variant_created:
                    variants_created += 1
                else:
                    variants_updated += 1

        except IntegrityError as error:

            raise ValueError(
                "Database integrity error while synchronizing "
                f"Shopify product {shopify_product['id']}. "
                "Check duplicate slugs or inventory item IDs."
            ) from error

        return {
            "product_created": product_created,
            "variants_created": variants_created,
            "variants_updated": variants_updated,
        }

    # --------------------------------------------------
    # SYNC ALL PRODUCTS
    # --------------------------------------------------

    def sync_products(self):

        shopify_products = self.product_service.get_products()

        stats = {
            "success": True,
            "products_created": 0,
            "products_updated": 0,
            "variants_created": 0,
            "variants_updated": 0,
        }

        for shopify_product in shopify_products:

            result = self.sync_product(shopify_product)

            if result["product_created"]:
                stats["products_created"] += 1
            else:
                stats["products_updated"] += 1

            stats["variants_created"] += (
                result["variants_created"]
            )

            stats["variants_updated"] += (
                result["variants_updated"]
            )

        return stats


# ==================================================
# PUBLIC FUNCTIONS
# ==================================================

def get_shopify_products():

    service = ShopifyProductService()

    return service.get_products()


def get_shopify_product(product_id):

    service = ShopifyProductService()

    return service.get_product(product_id)


def sync_products():

    service = ProductSyncService()

    return service.sync_products()


def sync_product(shopify_product):

    service = ProductSyncService()

    return service.sync_product(shopify_product)