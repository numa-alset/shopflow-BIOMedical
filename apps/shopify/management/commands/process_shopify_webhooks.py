# python manage.py process_shopify_webhooks --watch
import time

from django.core.management.base import BaseCommand

from apps.shopify.models import ShopifyWebhookEvent
from apps.shopify.webhooks.handlers import process_webhook_event


class Command(BaseCommand):
    help = "Process pending Shopify webhook events."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of events to process per cycle.",
        )

        parser.add_argument(
            "--watch",
            action="store_true",
            help="Keep running and check for new events continuously.",
        )

        parser.add_argument(
            "--interval",
            type=int,
            default=5,
            help="Seconds to wait between checks.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        watch = options["watch"]
        interval = options["interval"]

        self.stdout.write(
            self.style.SUCCESS("Shopify webhook processor started.")
        )

        try:
            while True:
                pending_events = list(
                    ShopifyWebhookEvent.objects.filter(
                        processed=False
                    ).order_by("received_at")[:limit]
                )

                if pending_events:
                    self.stdout.write(
                        f"Found {len(pending_events)} pending webhook events."
                    )

                for event in pending_events:
                    try:
                        process_webhook_event(event)

                        event.processed = True
                        event.processing_error = ""

                        event.save(
                            update_fields=[
                                "processed",
                                "processing_error",
                            ]
                        )

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Successfully processed event #{event.id}"
                            )
                        )

                    except Exception as error:
                        event.processing_error = str(error)
                        event.save(update_fields=["processing_error"])

                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed to process event #{event.id}: {error}"
                            )
                        )

                if not watch:
                    break

                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("Webhook processor stopped.")
            )