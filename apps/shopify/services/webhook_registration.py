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
        "ORDERS_CREATE",
    ]
    
    GET_WEBHOOK_SUBSCRIPTIONS_QUERY = """
        query GetWebhookSubscriptions {
            webhookSubscriptions(first: 100) {
                nodes {
                    id
                    topic
                    uri
                }
            }
        }
    """

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

    def get_existing_webhooks(self):
        data = self.client.graphql(
            self.GET_WEBHOOK_SUBSCRIPTIONS_QUERY
        )

        result = data.get("webhookSubscriptions")

        if not isinstance(result, dict):
            raise ShopifyAPIError(
                "Shopify returned invalid webhook subscriptions."
            )

        subscriptions = result.get("nodes")

        if not isinstance(subscriptions, list):
            raise ShopifyAPIError(
                "Shopify returned an invalid subscription list."
            )

        return subscriptions

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
        existing_webhooks = self.get_existing_webhooks()

        existing_subscriptions = {
            (webhook["topic"], webhook["uri"])
            for webhook in existing_webhooks
        }

        results = []

        for topic in self.WEBHOOK_TOPICS:

            if (topic, self.webhook_url) in existing_subscriptions:

                print(f"{topic}: Already registered - Skipped")
                continue

            subscription = self.register_webhook(topic)

            results.append(subscription)

            print(f"{topic}: Registered successfully")

        return results