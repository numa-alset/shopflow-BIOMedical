from django.db import models
from django.conf import settings

from apps.products.models import ProductVariant


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        SHIPPED = "shipped", "Shipped"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    shopify_order_id = models.CharField(
        max_length=100,
        unique=True,
    )

    customer_email = models.EmailField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Shopify Order {self.shopify_order_id}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )

    shopify_variant_id = models.CharField(max_length=100, blank=True)

    sku_snapshot = models.CharField(max_length=100, blank=True)

    product_title_snapshot = models.CharField(max_length=255, blank=True)

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    def __str__(self):
        sku = self.sku_snapshot or (self.variant.sku if self.variant_id else "")
        title = self.product_title_snapshot or (
            self.variant.product.name if self.variant_id else "Order item"
        )
        return f"{sku or title} x {self.quantity}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity