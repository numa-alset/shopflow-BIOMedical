from django.core.management.base import BaseCommand, CommandError

from apps.shopify.services.webhook_registration import (
    ShopifyWebhookRegistrationService,
)


class Command(BaseCommand):

    help = "Register Shopify webhook subscriptions."

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.NOTICE(
                "Registering Shopify webhook subscriptions..."
            )
        )

        try:
            service = ShopifyWebhookRegistrationService()

            subscriptions = service.register_all_webhooks()

            for subscription in subscriptions:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Registered: {subscription['topic']} "
                        f"({subscription['id']})"
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully registered {len(subscriptions)} webhooks."
                )
            )

        except Exception as exc:
            raise CommandError(
                f"Webhook registration failed: {exc}"
            ) from exc