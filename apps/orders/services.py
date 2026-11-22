from decimal import Decimal

from django.db import transaction
from django.core.exceptions import ValidationError

from apps.products.models import Product, ProductVariant

from .models import Order, OrderItem

@transaction.atomic
def create_order(user, items: list) -> Order:

    if not items:
        raise ValidationError("An order must contain at least one item.")

    order = Order.objects.create(
    user=user,
    customer_email=user.email,
    )

    total = Decimal("0.00")

    for item in items:

        product_id = item["product_id"]
        quantity = item["quantity"]

        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

        product = (
            Product.objects
            .select_for_update()
            .filter(id=product_id)
            .first()
        )

        if product is None:
            raise ValidationError(
                f"Product {product_id} does not exist or is inactive."
            )

        if not product.is_active and product.status.upper() != "ACTIVE":
            raise ValidationError(
                f"Product {product_id} does not exist or is inactive."
            )

        if product.stock < quantity:
            raise ValidationError(
                f"Not enough stock for {product.name}."
            )

        unit_price = product.price

        variant = product.variants.first()
        if variant is None:
            variant = ProductVariant.objects.create(
                shopify_variant_id=f"local-{product.id}",
                product=product,
                title="Default",
                sku=product.sku,
                price=product.price,
                inventory_quantity=product.stock,
            )
        elif variant.price != product.price:
            variant.price = product.price
            variant.save(update_fields=["price", "updated_at"])

        OrderItem.objects.create(
            order=order,
            variant=variant,
            quantity=quantity,
            unit_price=unit_price,
        )

        product.stock -= quantity
        product.save(update_fields=["stock", "updated_at"])

        total += unit_price * quantity

    order.total = total
    order.save(update_fields=["total", "updated_at"])

    return order