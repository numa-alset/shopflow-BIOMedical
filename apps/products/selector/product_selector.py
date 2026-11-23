from django.db.models import F

from apps.products.models import Product, ProductVariant


def get_active_products():
    """
    Return products with an active Shopify status.
    """
    return Product.objects.filter(status="ACTIVE")


def get_product_by_id(product_id: int):
    """
    Return a product by its ID.

    Returns None if the product does not exist.
    """
    return Product.objects.filter(id=product_id).first()


def get_product_by_sku(sku: str):
    """
    Return a product variant by its SKU.
    """
    return ProductVariant.objects.filter(sku=sku).first()


def get_low_stock_variants():
    """
    Return variants with configured minimum stock below their threshold.
    """
    return ProductVariant.objects.filter(
        inventory_quantity__gt=0,
        minimum_stock__isnull=False,
        inventory_quantity__lt=F("minimum_stock"),
    )


def get_out_of_stock_variants():
    """
    Return variants with zero or negative inventory.
    """
    return ProductVariant.objects.filter(inventory_quantity__lte=0)