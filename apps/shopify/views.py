from django.core.exceptions import ImproperlyConfigured
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from apps.shopify.models import ShopifyWebhookEvent
from .client import ShopifyAPIError, ShopifyClient

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.shopify.services.webhook_security import (
    verify_shopify_webhook,
)


logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def shopify_webhook_receiver(request):
    """
    Receive and verify Shopify webhook requests.
    """

    # 1. Verify Shopify's HMAC signature.
    try:
        is_valid = verify_shopify_webhook(request)

    except Exception:
        logger.exception("Webhook signature verification failed.")
        return JsonResponse(
            {"error": "Webhook verification unavailable"},
            status=500,
        )

    if not is_valid:
        logger.warning("Rejected webhook with invalid HMAC.")
        return JsonResponse(
            {"error": "Invalid webhook signature"},
            status=401,
        )

    # 2. Read Shopify webhook metadata.
    topic = request.headers.get("X-Shopify-Topic")
    shop_domain = request.headers.get("X-Shopify-Shop-Domain")
    webhook_id = request.headers.get("X-Shopify-Webhook-Id")

    # 3. Parse the JSON payload only after verification.
    try:
        payload = json.loads(request.body)

    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "Invalid JSON payload"},
            status=400,
        )

    print(f"Received Shopify webhook: topic={topic}, shop={shop_domain}, webhook_id={webhook_id}")
    # 4. Log the received event.
    logger.info(
        "Shopify webhook received: topic=%s shop=%s webhook_id=%s",
        topic,
        shop_domain,
        webhook_id,
    )

    if not webhook_id or not topic or not shop_domain:
        return JsonResponse(
            {"error": "Missing Shopify webhook headers"},
            status=400,
        )

    event, created = ShopifyWebhookEvent.objects.get_or_create(
        webhook_id=webhook_id,
        defaults={
            "topic": topic,
            "shop_domain": shop_domain,
            "payload": payload,
        },
        )

    if not created:
        logger.info(
            "Duplicate Shopify webhook ignored: %s",
            webhook_id,
        )

    return JsonResponse(
        {
            "success": True,
            "received": True,
            "duplicate": not created,
        },
        status=200,
    )


class ShopifyConnectionTestView(APIView):
    permission_classes = [AllowAny]
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            shop = ShopifyClient().test_connection()
        except ImproperlyConfigured as error:
            return Response(
                {"connected": False, "error": str(error)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ShopifyAPIError as error:
            return Response(
                {"connected": False, "error": str(error)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"connected": True, "shop": shop})
