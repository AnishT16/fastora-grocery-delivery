from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Order
from .serializers import (
    OrderCheckoutInputSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
)
from .services import create_order_from_cart, cancel_order
from apps.carts.services import get_or_create_cart
from common.exceptions import OrderNotFoundError, InvalidOrderOperationError


class OrderListCreateView(APIView):
    # List user orders or create a new order from cart
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_dispatcher() or request.user.is_staff:
            orders = Order.objects.all().prefetch_related('items').select_related('delivery_zone', 'delivery_slot')
            status_param = request.query_params.get('status')
            if status_param:
                orders = orders.filter(status=status_param)
        else:
            orders = Order.objects.filter(customer=request.user).prefetch_related('items').select_related('delivery_zone', 'delivery_slot')

        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        input_serializer = OrderCheckoutInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        data = input_serializer.validated_data
        address_param = data.get('address_id') or data.get('address')
        delivery_option = data.get('delivery_option')
        payment_method = data.get('payment_method', 'COD')
        slot_id = data.get('slot_id')

        cart = get_or_create_cart(request)

        order = create_order_from_cart(
            user=request.user,
            cart=cart,
            address_id=address_param,
            delivery_option=delivery_option,
            slot_id=slot_id,
            payment_method=payment_method
        )

        output_serializer = OrderDetailSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    # View details of a specific order
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            if request.user.is_dispatcher() or request.user.is_staff:
                order = Order.objects.select_related(
                    'delivery_zone', 'delivery_slot', 'customer'
                ).prefetch_related('items', 'pooled_order__batch__delivery_partner').get(id=pk)
            else:
                order = Order.objects.select_related(
                    'delivery_zone', 'delivery_slot', 'customer'
                ).prefetch_related('items', 'pooled_order__batch__delivery_partner').get(id=pk, customer=request.user)
        except Order.DoesNotExist:
            return Response(
                {'detail': f'Order #{pk} does not exist or you do not have permission to view it.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderCancelView(APIView):
    # Cancel an existing order
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        reason = request.data.get('reason', 'Customer requested cancellation')
        try:
            order = cancel_order(order_id=pk, user=request.user, reason=reason)
        except (OrderNotFoundError, InvalidOrderOperationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST))

        serializer = OrderDetailSerializer(order)
        return Response({
            'message': f"Order #{pk} has been successfully cancelled.",
            'order': serializer.data
        }, status=status.HTTP_200_OK)
