from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .serializers import OrderSerializer


class OrderListView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        orders = (
            Order.objects
            .all()
            .prefetch_related("items__variant__product")
        )

        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)