from apps.products.models import Product


def get_active_products():
    """
    Return all active products.
    """
    return Product.objects.filter(is_active=True)


def get_product_by_id(product_id: int):
    """
    Return a product by its ID.

    Returns None if the product does not exist.
    """
    return Product.objects.filter(id=product_id).first()


def get_product_by_sku(sku: str):
    """
    Return a product by its SKU.
    """
    return Product.objects.filter(sku=sku).first()