from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from .services import create_order

class OrderListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = (
            Order.objects
            .filter(user=request.user)
            .prefetch_related("items__variant__product")
        )

        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)

    def post(self, request):
        input_serializer = OrderCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            order = create_order(
                user=request.user,
                items=input_serializer.validated_data["items"],
            )

        except DjangoValidationError as error:
            raise ValidationError(error.messages)

        output_serializer = OrderSerializer(order)

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )