import base64
import hashlib
import hmac
import json

from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(SHOPIFY_CLIENT_SECRET="test-secret")
class ShopifyWebhookSecurityTests(TestCase):

    def generate_signature(self, body):
        digest = hmac.new(
            key=b"test-secret",
            msg=body,
            digestmod=hashlib.sha256,
        ).digest()

        return base64.b64encode(digest).decode("utf-8")

    def test_valid_webhook_is_accepted(self):
        body = json.dumps(
            {"id": 123, "title": "Test Product"}
        ).encode("utf-8")

        signature = self.generate_signature(body)

        response = self.client.post(
            reverse("shopify-webhook-receiver"),
            data=body,
            content_type="application/json",
            HTTP_X_SHOPIFY_HMAC_SHA256=signature,
            HTTP_X_SHOPIFY_TOPIC="products/create",
            HTTP_X_SHOPIFY_SHOP_DOMAIN="example.myshopify.com",
            HTTP_X_SHOPIFY_WEBHOOK_ID="test-webhook-123",
        )

        self.assertEqual(response.status_code, 200)

    def test_invalid_signature_is_rejected(self):
        body = json.dumps(
            {"id": 123, "title": "Fake Product"}
        ).encode("utf-8")

        response = self.client.post(
            reverse("shopify-webhook-receiver"),
            data=body,
            content_type="application/json",
            HTTP_X_SHOPIFY_HMAC_SHA256="invalid-signature",
        )

        self.assertEqual(response.status_code, 401)

    def test_missing_signature_is_rejected(self):
        body = json.dumps(
            {"id": 123}
        ).encode("utf-8")

        response = self.client.post(
            reverse("shopify-webhook-receiver"),
            data=body,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_get_request_is_not_allowed(self):
        response = self.client.get(
            reverse("shopify-webhook-receiver")
        )

        self.assertEqual(response.status_code, 405)
