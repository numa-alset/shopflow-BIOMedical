import logging
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.orders.models import Order, OrderItem
from apps.products.models import ProductVariant


logger = logging.getLogger(__name__)


class OrderSyncService:

    @transaction.atomic
    def sync_order(self, shopify_order):
        if not isinstance(shopify_order, dict):
            raise ValidationError("Shopify order payload must be an object.")

        shopify_order_id = self._shopify_gid(
            shopify_order.get("admin_graphql_api_id")
            or shopify_order.get("id"),
            "Order",
        )

        line_items = shopify_order.get("line_items")
        if not isinstance(line_items, list):
            raise ValidationError(
                "Shopify order payload must contain a line_items list."
            )

        total = self._decimal(shopify_order.get("total_price"), "total_price")
        currency = self._currency(shopify_order.get("currency", "EUR"))
        customer_email = self._customer_email(shopify_order)
        normalized_items = [
            self._normalize_line_item(item)
            for item in line_items
        ]

        order, created = Order.objects.get_or_create(
            shopify_order_id=shopify_order_id,
            defaults={
                "customer_email": customer_email,
                "currency": currency,
                "total": total,
            },
        )

        if not created:
            return order

        variant_ids = {
            item["shopify_variant_id"]
            for item in normalized_items
            if item["shopify_variant_id"]
        }
        variants = {
            variant.shopify_variant_id: variant
            for variant in ProductVariant.objects.filter(
                shopify_variant_id__in=variant_ids
            )
        }
        for variant_id in sorted(variant_ids - variants.keys()):
            logger.warning(
                "No local product variant matches Shopify order: "
                "order_id=%s variant_id=%s",
                shopify_order_id,
                variant_id,
            )

        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    variant=variants.get(item["shopify_variant_id"]),
                    **item,
                )
                for item in normalized_items
            ]
        )

        return order


# utility methods for validation and normalization of Shopify order data

    @staticmethod
    def _normalize_line_item(item):
        if not isinstance(item, dict):
            raise ValidationError("Each Shopify line item must be an object.")

        try:
            quantity = item["quantity"]
        except KeyError as error:
            raise ValidationError(
                "Shopify line item is missing quantity."
            ) from error

        if isinstance(quantity, bool) or not (
            isinstance(quantity, int)
            or isinstance(quantity, str) and quantity.isdecimal()
        ):
            raise ValidationError(
                "Shopify line item quantity must be a positive integer."
            )
        quantity = int(quantity)
        if quantity <= 0:
            raise ValidationError(
                "Shopify line item quantity must be a positive integer."
            )

        variant_id = item.get("variant_id")
        shopify_variant_id = (
            OrderSyncService._shopify_gid(variant_id, "ProductVariant")
            if variant_id not in (None, "")
            else ""
        )

        return {
            "shopify_variant_id": shopify_variant_id,
            "sku_snapshot": str(item.get("sku") or ""),
            "product_title_snapshot": str(
                item.get("title") or item.get("name") or ""
            ),
            "quantity": quantity,
            "unit_price": OrderSyncService._decimal(
                item.get("price"),
                "line item price",
            ),
        }

    @staticmethod
    def _shopify_gid(value, resource):
        if value is None or value == "":
            raise ValidationError(
                f"Shopify {resource.lower()} ID is missing."
            )

        value = str(value).strip()
        if not value:
            raise ValidationError(
                f"Shopify {resource.lower()} ID is missing."
            )

        prefix = f"gid://shopify/{resource}/"
        if value.startswith(prefix):
            if not value[len(prefix):] or "/" in value[len(prefix):]:
                raise ValidationError(
                    f"Shopify {resource.lower()} ID is invalid."
                )
            return value
        if value.isdecimal():
            return f"{prefix}{value}"
        raise ValidationError(
            f"Shopify {resource.lower()} ID is invalid."
        )

    @staticmethod
    def _decimal(value, field_name):
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValidationError(
                f"Shopify {field_name} must be a valid decimal amount."
            ) from error

        if not amount.is_finite():
            raise ValidationError(
                f"Shopify {field_name} must be a finite decimal amount."
            )
        if amount < 0:
            raise ValidationError(
                f"Shopify {field_name} cannot be negative."
            )
        return amount

    @staticmethod
    def _currency(value):
        if (
            not isinstance(value, str)
            or len(value) != 3
            or not value.isascii()
            or not value.isalpha()
        ):
            raise ValidationError("Shopify currency must be a three-letter code.")
        return value.upper()

    @staticmethod
    def _customer_email(shopify_order):
        email = shopify_order.get("email")
        if not email:
            customer = shopify_order.get("customer")
            if isinstance(customer, dict):
                email = customer.get("email")
        if email is None:
            return ""
        if not isinstance(email, str):
            raise ValidationError("Shopify customer email is invalid.")
        return Order._meta.get_field("customer_email").clean(email, None)