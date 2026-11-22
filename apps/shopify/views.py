from django.core.exceptions import ImproperlyConfigured
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .client import ShopifyAPIError, ShopifyClient


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
