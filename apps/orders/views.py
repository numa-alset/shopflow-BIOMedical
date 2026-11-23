from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .serializers import OrderSerializer


class OrderListView(APIView):

    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]  # Temporarily allow any user for testing purposes

    def get(self, request):
        orders = (
            Order.objects
            .filter(user=request.user)
            .prefetch_related("items__variant__product")
        )

        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)