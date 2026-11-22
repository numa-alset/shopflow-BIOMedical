from django.db import transaction

from apps.products.models import Product
# from apps.products.selectors.product_selector import get_product_by_id


class ProductNotFoundError(Exception):
    pass


class InvalidStockError(Exception):
    pass


@transaction.atomic
def update_product_stock(product_id: int, new_stock: int) -> Product:
    """
    Update the stock quantity of a product.

    Business rules:
    - The product must exist.
    - Stock cannot be negative.
    """

    if new_stock < 0:
        raise InvalidStockError("Stock cannot be negative.")

    product = (
        Product.objects
        .select_for_update()
        .filter(id=product_id)
        .first()
    )

    if product is None:
        raise ProductNotFoundError("Product not found.")

    product.stock = new_stock
    product.save(update_fields=["stock", "updated_at"])

    return product