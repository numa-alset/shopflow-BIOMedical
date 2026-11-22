from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    fields = (
        "variant",
        "quantity",
        "unit_price",
        "subtotal_display",
    )

    readonly_fields = (
        "subtotal_display",
    )

    autocomplete_fields = (
        "variant",
    )

    @admin.display(description="Subtotal")
    def subtotal_display(self, obj):
        if not obj or not obj.pk:
            return "-"

        return obj.subtotal


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "shopify_order_id",
        "customer_email",
        "status",
        "total",
        "items_count",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "shopify_order_id",
        "customer_email",
    )

    readonly_fields = (
        "shopify_order_id",
        "created_at",
        "updated_at",
    )

    inlines = [
        OrderItemInline,
    ]

    list_select_related = (
        "user",
    )

    @admin.display(description="Items")
    def items_count(self, obj):
        return obj.items.count()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "variant",
        "quantity",
        "unit_price",
        "subtotal_display",
    )

    search_fields = (
        "order__shopify_order_id",
        "variant__sku",
        "variant__product__name",
    )

    list_select_related = (
        "order",
        "variant",
        "variant__product",
    )

    @admin.display(description="Subtotal")
    def subtotal_display(self, obj):
        return obj.subtotal