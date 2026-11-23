from django.core.management.base import BaseCommand, CommandError

from apps.shopify.services.product_sync import sync_products


class Command(BaseCommand):
    help = "Synchronize products and variants from Shopify."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.NOTICE("Starting Shopify product synchronization...")
        )

        try:
            result = sync_products()

            if not result.get("success"):
                raise CommandError("Shopify synchronization failed.")

            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS("Synchronization completed successfully!")
            )

            self.stdout.write("-----------------------------------")
            self.stdout.write(
                f"Products created: {result['products_created']}"
            )
            self.stdout.write(
                f"Products updated: {result['products_updated']}"
            )
            self.stdout.write(
                f"Variants created: {result['variants_created']}"
            )
            self.stdout.write(
                f"Variants updated: {result['variants_updated']}"
            )
            self.stdout.write("-----------------------------------")

        except Exception as exc:
            raise CommandError(
                f"Shopify synchronization failed: {exc}"
            ) from exc