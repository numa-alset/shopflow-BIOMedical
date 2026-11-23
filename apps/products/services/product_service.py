from django.db import transaction

from apps.products.models import ProductVariant


class ProductVariantNotFoundError(Exception):
    pass


class InvalidMinimumStockError(Exception):
    pass


@transaction.atomic
def update_variant_minimum_stock(
    variant_id: int,
    minimum_stock: int | None,
) -> ProductVariant:
    """
    Update the ERP-managed minimum stock for a Shopify variant.
    """

    if minimum_stock is not None and minimum_stock < 0:
        raise InvalidMinimumStockError("Minimum stock cannot be negative.")

    variant = (
        ProductVariant.objects
        .select_for_update()
        .filter(id=variant_id)
        .first()
    )

    if variant is None:
        raise ProductVariantNotFoundError("Product variant not found.")

    variant.minimum_stock = minimum_stock
    variant.save(update_fields=["minimum_stock", "updated_at"])

    return variant