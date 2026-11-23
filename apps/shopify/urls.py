from django.urls import path

from .views import ShopifyConnectionTestView, shopify_webhook_receiver


urlpatterns = [
    path(
        "test-connection/",
        ShopifyConnectionTestView.as_view(),
        name="shopify-test-connection",
    ),
     path(
        "webhooks/",
        shopify_webhook_receiver,
        name="shopify-webhook-receiver",
    ),
]
