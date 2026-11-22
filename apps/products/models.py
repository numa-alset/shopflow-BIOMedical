from django.db import models


class Product(models.Model):

    shopify_product_id = models.CharField(
        max_length=100,
        unique=True,
    )

    name = models.CharField(max_length=255)

    slug = models.SlugField(
        max_length=255,
        unique=True,
    )

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=30,
        default="ACTIVE",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        db_table = "products"

    def __str__(self):
        return self.name


class ProductVariant(models.Model):

    shopify_variant_id = models.CharField(
        max_length=100,
        unique=True,
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )

    title = models.CharField(max_length=255)

    sku = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    inventory_quantity = models.IntegerField(default=0)

    minimum_stock = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sku"]

    def __str__(self):
        return f"{self.product.name} - {self.title}"

    @property
    def stock_status(self):

        if self.minimum_stock is None:
            return "not_configured"

        if self.inventory_quantity < self.minimum_stock:
            return "low_stock"

        return "normal"