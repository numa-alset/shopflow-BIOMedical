from django.contrib import admin

from .models import Product, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0

    fields = (
        "shopify_variant_id",
        "title",
        "sku",
        "price",
        "inventory_quantity",
        "minimum_stock",
        "stock_status_display",
    )

    readonly_fields = (
        "shopify_variant_id",
        "stock_status_display",
    )

    show_change_link = True

    @admin.display(description="Stock Status")
    def stock_status_display(self, obj):
        if not obj:
            return "-"

        return obj.stock_status


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "shopify_product_id",
        "status",
        "variants_count",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "name",
        "shopify_product_id",
        "slug",
    )

    readonly_fields = (
        "shopify_product_id",
        "created_at",
        "updated_at",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    inlines = [
        ProductVariantInline,
    ]

    @admin.display(description="Variants")
    def variants_count(self, obj):
        return obj.variants.count()


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):

    list_display = (
        "sku",
        "product",
        "title",
        "price",
        "inventory_quantity",
        "minimum_stock",
        "stock_status_display",
    )

    list_filter = (
        "product",
    )

    search_fields = (
        "sku",
        "title",
        "product__name",
        "shopify_variant_id",
    )

    readonly_fields = (
        "shopify_variant_id",
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "product",
    )

    @admin.display(description="Stock Status")
    def stock_status_display(self, obj):
        return obj.stock_status