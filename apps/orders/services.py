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

        variant_id = item.get("variant_id")
        product_id = item.get("product_id")
        quantity = item["quantity"]

        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

        if variant_id is not None:
            variant = (
                ProductVariant.objects
                .select_for_update()
                .select_related("product")
                .filter(id=variant_id)
                .first()
            )
        else:
            product = (
                Product.objects
                .select_for_update()
                .prefetch_related("variants")
                .filter(id=product_id)
                .first()
            )
            if product is None:
                raise ValidationError(
                    f"Product {product_id} does not exist or is inactive."
                )
            variant = product.variants.first()

        if variant is None:
            raise ValidationError("Product variant does not exist.")

        if variant.product.status.upper() != "ACTIVE":
            raise ValidationError(
                f"Product {variant.product.id} does not exist or is inactive."
            )

        if variant.inventory_quantity < quantity:
            raise ValidationError(
                f"Not enough stock for {variant.product.name}."
            )

        unit_price = variant.price

        OrderItem.objects.create(
            order=order,
            variant=variant,
            quantity=quantity,
            unit_price=unit_price,
        )

        total += unit_price * quantity

    order.total = total
    order.save(update_fields=["total", "updated_at"])

    return order