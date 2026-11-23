# python manage.py register_shopify_webhooks

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from apps.shopify.client import ShopifyClient, ShopifyAPIError


class ShopifyWebhookRegistrationService:

    WEBHOOK_TOPICS = [
        "PRODUCTS_CREATE",
        "PRODUCTS_UPDATE",
        "PRODUCTS_DELETE",
        "INVENTORY_LEVELS_UPDATE",
    ]

    CREATE_WEBHOOK_MUTATION = """
        mutation webhookSubscriptionCreate(
            $topic: WebhookSubscriptionTopic!,
            $webhookSubscription: WebhookSubscriptionInput!
        ) {
            webhookSubscriptionCreate(
                topic: $topic,
                webhookSubscription: $webhookSubscription
            ) {
                webhookSubscription {
                    id
                    topic
                    uri
                }
                userErrors {
                    field
                    message
                }
            }
        }
    """

    def __init__(self, client=None):
        self.client = client or ShopifyClient()

        base_url = getattr(
            settings,
            "SHOPIFY_WEBHOOK_BASE_URL",
            "",
        ).rstrip("/")

        if not base_url.startswith("https://"):
            raise ImproperlyConfigured(
                "SHOPIFY_WEBHOOK_BASE_URL must be a public HTTPS URL."
            )

        self.webhook_url = (
            f"{base_url}/api/shopify/webhooks/"
        )

    def register_webhook(self, topic):

        if topic not in self.WEBHOOK_TOPICS:
            raise ValueError(
                f"Unsupported webhook topic: {topic}"
            )

        variables = {
            "topic": topic,
            "webhookSubscription": {
                "uri": self.webhook_url,
                "format": "JSON",
            },
        }

        data = self.client.graphql(
            self.CREATE_WEBHOOK_MUTATION,
            variables=variables,
        )

        result = data["webhookSubscriptionCreate"]

        errors = result.get("userErrors", [])

        if errors:
            raise ShopifyAPIError(
                f"Could not register {topic}: {errors}"
            )

        subscription = result.get("webhookSubscription")

        if not subscription:
            raise ShopifyAPIError(
                f"Shopify did not return a subscription for {topic}."
            )

        return subscription

    def register_all_webhooks(self):

        results = []

        for topic in self.WEBHOOK_TOPICS:
            subscription = self.register_webhook(topic)

            results.append(subscription)

        return results