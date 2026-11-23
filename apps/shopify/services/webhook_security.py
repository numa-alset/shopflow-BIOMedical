import base64
import hashlib
import hmac

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def verify_shopify_webhook(request):
    """
    Verify that an incoming webhook request was signed by Shopify.

    Shopify signs the raw request body using HMAC-SHA256.
    """

    secret = getattr(settings, "SHOPIFY_CLIENT_SECRET", None)

    if not secret:
        raise ImproperlyConfigured(
            "SHOPIFY_CLIENT_SECRET is not configured."
        )

    received_signature = request.headers.get(
        "X-Shopify-Hmac-Sha256"
    )

    if not received_signature:
        return False

    # Calculate HMAC using the original request body.
    calculated_digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=request.body,
        digestmod=hashlib.sha256,
    ).digest()

    # Shopify expects a Base64-encoded signature.
    calculated_signature = base64.b64encode(
        calculated_digest
    ).decode("utf-8")

    # Constant-time comparison to prevent timing attacks.
    return hmac.compare_digest(
        calculated_signature,
        received_signature,
    )
