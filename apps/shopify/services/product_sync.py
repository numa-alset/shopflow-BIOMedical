from apps.shopify.client import ShopifyClient, ShopifyAPIError


PRODUCTS_QUERY = """
query GetProducts($first: Int!, $after: String) {

    products(first: $first, after: $after) {

        edges {

            cursor

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

                        cursor

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

                cursor

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


class ShopifyProductService:
    """
    Responsible for retrieving products and variants from Shopify.

    This service does not save anything to our database yet.
    """

    def __init__(self, client=None):

        self.client = client or ShopifyClient()

    # --------------------------------------------------
    # RETRIEVE ALL VARIANTS FOR ONE PRODUCT
    # --------------------------------------------------

    def _get_all_variants(self, product):

        variants_connection = product.get("variants", {})

        variants = [
            edge["node"]
            for edge in variants_connection.get("edges", [])
        ]

        page_info = variants_connection.get("pageInfo", {})

        while page_info.get("hasNextPage"):

            data = self.client.graphql(
                PRODUCT_VARIANTS_QUERY,
                {
                    "productId": product["id"],
                    "first": 100,
                    "after": page_info["endCursor"],
                },
            )

            product_data = data.get("product")

            if not product_data:
                raise ShopifyAPIError(
                    f"Could not retrieve variants for product {product['id']}."
                )

            connection = product_data.get("variants", {})

            variants.extend(
                edge["node"]
                for edge in connection.get("edges", [])
            )

            page_info = connection.get("pageInfo", {})

        return variants

    # --------------------------------------------------
    # RETRIEVE ALL PRODUCTS
    # --------------------------------------------------

    def get_products(self):

        products = []

        has_next_page = True
        cursor = None

        while has_next_page:

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
                    "Shopify did not return a valid products connection."
                )

            edges = connection.get("edges", [])

            for edge in edges:

                product = edge["node"]

                product["variants"] = self._get_all_variants(product)

                products.append(product)

            page_info = connection.get("pageInfo", {})

            has_next_page = page_info.get("hasNextPage", False)

            cursor = page_info.get("endCursor")

            if has_next_page and not cursor:
                raise ShopifyAPIError(
                    "Shopify pagination returned no cursor."
                )

        return products

    # --------------------------------------------------
    # RETRIEVE ONE PRODUCT
    # --------------------------------------------------

    def get_product(self, product_id):

        query = """
        query GetProduct($id: ID!) {

            product(id: $id) {

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
        """

        data = self.client.graphql(
            query,
            {"id": product_id},
        )

        product = data.get("product")

        if not product:
            return None

        product["variants"] = self._get_all_variants(product)

        return product


# --------------------------------------------------
# PUBLIC SERVICE FUNCTIONS
# --------------------------------------------------

def get_shopify_products():

    service = ShopifyProductService()

    return service.get_products()


def get_shopify_product(product_id):

    service = ShopifyProductService()

    return service.get_product(product_id)