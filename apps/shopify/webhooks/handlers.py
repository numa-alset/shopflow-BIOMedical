import logging

from apps.shopify.constants import (
    INVENTORY_LEVELS_UPDATE_TOPIC,
    ORDERS_CREATE_TOPIC,
    PRODUCT_CREATE_TOPIC,
    PRODUCT_DELETE_TOPIC,
    PRODUCT_UPDATE_TOPIC,
    SHOPIFY_PRODUCT_GID_PREFIX,
)
from apps.shopify.services.product_sync import (
    get_shopify_product,
    sync_product,
    sync_products,
)

from apps.shopify.services.order_sync import OrderSyncService

logger = logging.getLogger(__name__)


class ShopifyWebhookProcessingError(Exception):
    """Raised when a Shopify webhook cannot be processed."""


def get_shopify_product_gid(payload):
    """
    Extract the Shopify product ID from a webhook payload
    and return it in GraphQL GID format.
    """

    # Shopify webhook payloads can include the GraphQL ID.
    graphql_id = payload.get("admin_graphql_api_id")

    if graphql_id:
        return graphql_id

    # Otherwise, convert the numeric REST ID into a GraphQL GID.
    product_id = payload.get("id")

    if not product_id:
        raise ShopifyWebhookProcessingError(
            "Product ID is missing from webhook payload."
        )

    return f"{SHOPIFY_PRODUCT_GID_PREFIX}{product_id}"


def process_webhook_event(event):
    """
    Central dispatcher for Shopify webhook events.
    """

    logger.info(
        "Processing Shopify webhook: event_id=%s topic=%s",
        event.id,
        event.topic,
    )

    try:
        if event.topic in (PRODUCT_CREATE_TOPIC, PRODUCT_UPDATE_TOPIC):
            return handle_product_change(event)

        elif event.topic == PRODUCT_DELETE_TOPIC:
            return handle_product_delete(event)

        elif event.topic == INVENTORY_LEVELS_UPDATE_TOPIC:
            return handle_inventory_update(event)

        elif event.topic == ORDERS_CREATE_TOPIC:
            return handle_order_create(event)

        else:
            raise ShopifyWebhookProcessingError(
                f"Unsupported Shopify webhook topic: {event.topic}"
            )

    except Exception as error:
        logger.exception(
            "Failed to process Shopify webhook event %s",
            event.id,
        )

        raise ShopifyWebhookProcessingError(
            f"Event {event.id} failed: {error}"
        ) from error


def handle_order_create(event):
    """
    Handle a newly created Shopify order.
    """

    logger.info(
        "Synchronizing Shopify order from webhook event %s",
        event.id,
    )

    service = OrderSyncService()

    order = service.sync_order(event.payload)

    logger.info(
        "Shopify order synchronized successfully: %s",
        order.shopify_order_id,
    )

    return order


def handle_product_change(event):
    """
    Handle product creation and updates.

    Also handles variant changes because Shopify sends
    products/update when a product's variants are changed.
    """

    product_gid = get_shopify_product_gid(event.payload)

    logger.info(
        "Retrieving latest Shopify product: %s",
        product_gid,
    )

    # Retrieve the latest product, including its variants.
    shopify_product = get_shopify_product(product_gid)

    if not shopify_product:
        raise ShopifyWebhookProcessingError(
            f"Shopify product {product_gid} was not found."
        )

    # Reuse the existing synchronization service.
    result = sync_product(shopify_product)

    logger.info(
        "Product synchronized successfully: %s",
        result,
    )

    return result


def handle_product_delete(event):
    """
    Handle product deletion.

    Implementation will be added after inspecting
    the local Product model and its relationships.
    """

    raise NotImplementedError(
        "Product deletion handling is not implemented yet."
    )


def handle_inventory_update(event):
    """
    Temporarily synchronize all products after an inventory update.
    """

    logger.info(
        "Inventory update received. Synchronizing all Shopify products."
    )

    result = sync_products()

    logger.info(
        "Product synchronization completed: %s",
        result,
    )

    return result