from django.db import models


class ShopifyWebhookEvent(models.Model):

    webhook_id = models.CharField(
        max_length=255,
        unique=True,
    )

    topic = models.CharField(
        max_length=100,
    )

    shop_domain = models.CharField(
        max_length=255,
    )

    payload = models.JSONField()

    processed = models.BooleanField(
        default=False,
    )

    processing_error = models.TextField(
        blank=True,
        default="",
    )

    received_at = models.DateTimeField(
        auto_now_add=True,
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.topic} - {self.webhook_id}"