from django.urls import path

from .views import ShopifyConnectionTestView


urlpatterns = [
    path(
        "test-connection/",
        ShopifyConnectionTestView.as_view(),
        name="shopify-test-connection",
    ),
]
