from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Avg, Count, Sum
from django.shortcuts import render
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order
from common.exceptions import (
    DeliveryPartnerNotFoundError,
    InvalidBatchOperationError,
    SlotNotAvailableError,
    ZoneNotServiceableError,
)

from .models import DeliveryBatch, DeliveryEvent, DeliveryPartner, DeliveryZone, PooledOrder
from .serializers import (
    BatchReleaseSerializer,
    DeliveryBatchSerializer,
    DeliverySlotSerializer,
    OrderStatusUpdateSerializer,
    SlotReservationSerializer,
)
from .services.pooling_service import release_batch, run_batch_matching
from .services.pricing_service import calculate_delivery_quote
from .services.slot_service import get_available_slots, reserve_slot_capacity
from .services.zone_service import get_serviceable_zone


def delivery_check_view(request):
    postal_code = request.GET.get('postal_code', '411038').strip()
    subtotal_val = request.GET.get('subtotal', '150')
    try:
        subtotal = Decimal(str(subtotal_val))
    except (ValueError, TypeError):
        subtotal = Decimal('150.00')

    error_msg = None
    zone = None
    quote_express = None
    quote_pooled = None
    slots = []
    savings = 0.0

    try:
        zone = get_serviceable_zone(postal_code)
        quote_express = calculate_delivery_quote({'postal_code': postal_code}, subtotal, 'EXPRESS', user=request.user)
        quote_pooled = calculate_delivery_quote({'postal_code': postal_code}, subtotal, 'SCHEDULED_POOLED', user=request.user)
        savings = round(quote_express['final_fee'] - quote_pooled['final_fee'], 2)

        today = timezone.localdate()
        today_slots = list(get_available_slots(zone.id, target_date=today))
        if today_slots:
            slots = today_slots
        else:
            tomorrow = today + timedelta(days=1)
            slots = list(get_available_slots(zone.id, target_date=tomorrow))
    except ZoneNotServiceableError as e:
        error_msg = str(e)

    context = {
        'postal_code': postal_code,
        'subtotal': subtotal,
        'error_msg': error_msg,
        'zone': zone,
        'quote_express': quote_express,
        'quote_pooled': quote_pooled,
        'savings': savings,
        'slots': slots,
        'today': timezone.localdate(),
    }
    return render(request, 'delivery/check.html', context)


class DeliveryOptionsAPIView(APIView):
    # Returns fee quotes for express and pooled delivery
    def get(self, request):
        postal_code = request.query_params.get('postal_code') or request.query_params.get('address_id', '411038')
        subtotal = request.query_params.get('subtotal', 100)

        try:
            zone = get_serviceable_zone(str(postal_code))
        except ZoneNotServiceableError as e:
            return Response({'error': str(e), 'is_serviceable': False}, status=status.HTTP_404_NOT_FOUND)

        exp_quote = calculate_delivery_quote({'postal_code': postal_code}, subtotal, 'EXPRESS', user=request.user)
        pool_quote = calculate_delivery_quote({'postal_code': postal_code}, subtotal, 'SCHEDULED_POOLED', user=request.user)

        return Response({
            'zone': {'id': zone.id, 'name': zone.name, 'radius_km': float(zone.radius_km)},
            'options': {
                'express': exp_quote,
                'scheduled_pooled': pool_quote,
            },
            'savings_amount': round(exp_quote['final_fee'] - pool_quote['final_fee'], 2)
        })


class DeliverySlotsAPIView(APIView):
    # Returns available slots for a delivery zone
    def get(self, request):
        zone_id = request.query_params.get('zone_id')
        if not zone_id:
            zone = DeliveryZone.objects.filter(is_active=True).first()
            zone_id = zone.id if zone else None

        if not zone_id:
            return Response({'error': 'No active zone found'}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.localdate()
        target_date_param = request.query_params.get('date')
        if target_date_param:
            try:
                target_date = datetime.strptime(target_date_param, '%Y-%m-%d').date()
            except ValueError:
                target_date = today
            slots = list(get_available_slots(int(zone_id), target_date=target_date))
        else:
            # Prioritize today's remaining rolling 1-2 hour slots
            slots = list(get_available_slots(int(zone_id), target_date=today))
            if not slots:
                tomorrow = today + timedelta(days=1)
                slots = list(get_available_slots(int(zone_id), target_date=tomorrow))

        data = [{
            'id': s.id,
            'date': str(s.date),
            'start_time': s.start_time.strftime('%H:%M'),
            'end_time': s.end_time.strftime('%H:%M'),
            'max_capacity': s.max_capacity,
            'current_bookings': s.current_bookings,
            'status': s.status,
            'cutoff_time': s.cutoff_time.isoformat(),
        } for s in slots]

        return Response({'zone_id': int(zone_id), 'slots': data})


class DeliveryFeeQuoteAPIView(APIView):
    # Calculates delivery fee quote for a given cart and option
    def post(self, request):
        data = request.data
        postal_code = data.get('postal_code', '411038')
        subtotal = data.get('subtotal', 100)
        option = data.get('delivery_option', 'EXPRESS')
        slot_id = data.get('slot_id')

        quote = calculate_delivery_quote(
            {'postal_code': postal_code},
            cart_subtotal=subtotal,
            delivery_option=option,
            slot_id=slot_id,
            user=request.user
        )
        return Response(quote)


class IsDispatcherOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_dispatcher() or request.user.is_staff))


class IsDeliveryPartnerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_delivery_partner() or request.user.is_staff))


class SlotReservationAPIView(APIView):
    # Reserves slot capacity before order checkout
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SlotReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot_id = serializer.validated_data['slot_id']

        try:
            slot = reserve_slot_capacity(slot_id)
        except SlotNotAvailableError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': f"Slot #{slot_id} reserved successfully.",
            'slot': DeliverySlotSerializer(slot).data
        }, status=status.HTTP_200_OK)


class AdminDeliveryBatchListView(APIView):
    # List active and completed delivery batches
    permission_classes = [IsDispatcherOrAdmin]

    def get(self, request):
        queryset = DeliveryBatch.objects.select_related('zone', 'slot', 'delivery_partner').prefetch_related('pooled_orders__order__customer').all()

        status_param = request.query_params.get('status')
        zone_id = request.query_params.get('zone_id')
        slot_id = request.query_params.get('slot_id')

        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)
        if slot_id:
            queryset = queryset.filter(slot_id=slot_id)

        serializer = DeliveryBatchSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminRunBatchMatchingView(APIView):
    # Groups orders into batches for dispatch
    permission_classes = [IsDispatcherOrAdmin]

    def post(self, request):
        zone_id = request.data.get('zone_id')
        slot_id = request.data.get('slot_id')

        batches = run_batch_matching(
            zone_id=int(zone_id) if zone_id else None,
            slot_id=int(slot_id) if slot_id else None
        )

        serializer = DeliveryBatchSerializer(batches, many=True)
        return Response({
            'message': f"Batch matching complete. Processed {len(batches)} batches.",
            'batches': serializer.data
        }, status=status.HTTP_200_OK)


class AdminReleaseBatchView(APIView):
    # Assigns partner and releases a batch for delivery
    permission_classes = [IsDispatcherOrAdmin]

    def post(self, request, pk):
        serializer = BatchReleaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        partner_id = serializer.validated_data['delivery_partner_id']

        try:
            batch = release_batch(batch_id=pk, delivery_partner_id=partner_id)
        except (InvalidBatchOperationError, DeliveryPartnerNotFoundError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        for pooled in batch.pooled_orders.all():
            DeliveryEvent.objects.create(
                order=pooled.order,
                batch=batch,
                status='BATCH_RELEASED',
                actor=request.user,
                notes=f"Assigned to Delivery Partner #{partner_id}"
            )

        return Response({
            'message': f"Batch #{batch.id} released and assigned to partner #{partner_id}.",
            'batch': DeliveryBatchSerializer(batch).data
        }, status=status.HTTP_200_OK)


class DeliveryMyBatchesView(APIView):
    # Returns batches assigned to the current delivery partner
    permission_classes = [IsDeliveryPartnerUser]

    def get(self, request):
        batches = DeliveryBatch.objects.filter(
            delivery_partner=request.user
        ).exclude(
            status=DeliveryBatch.STATUS_COMPLETED
        ).select_related('zone', 'slot').prefetch_related('pooled_orders__order__customer')

        serializer = DeliveryBatchSerializer(batches, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeliveryOrderStatusUpdateView(APIView):
    # Updates order status during delivery
    permission_classes = [IsDeliveryPartnerUser]

    def patch(self, request, pk):
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        cur_lat = serializer.validated_data.get('current_lat')
        cur_lng = serializer.validated_data.get('current_lng')

        with transaction.atomic():
            try:
                pooled_order = PooledOrder.objects.select_for_update().select_related(
                    'order', 'batch'
                ).get(order_id=pk)
            except PooledOrder.DoesNotExist:
                return Response(
                    {'error': f"Order #{pk} is not part of any pooled batch."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not request.user.is_staff and pooled_order.batch.delivery_partner != request.user:
                return Response(
                    {'error': "You are not assigned to deliver this order."},
                    status=status.HTTP_403_FORBIDDEN
                )

            order = pooled_order.order
            pooled_order.status = new_status

            if new_status == PooledOrder.STATUS_PICKED_UP:
                order.status = Order.STATUS_DISPATCHED
                pooled_order.batch.status = DeliveryBatch.STATUS_IN_TRANSIT
                pooled_order.batch.save(update_fields=['status', 'updated_at'])

            elif new_status == PooledOrder.STATUS_DELIVERED:
                pooled_order.delivered_at = timezone.now()
                order.status = Order.STATUS_DELIVERED

                if order.payment_method == Order.PAYMENT_METHOD_COD and hasattr(order, 'payment'):
                    order.payment.mark_cod_collected(collected_by=request.user.username)

            elif new_status == PooledOrder.STATUS_FAILED:
                order.cancellation_reason = notes or "Delivery attempt failed."

            pooled_order.save(update_fields=['status', 'delivered_at'] if new_status == PooledOrder.STATUS_DELIVERED else ['status'])
            order.save(update_fields=['status', 'cancellation_reason', 'updated_at'])

            DeliveryEvent.objects.create(
                order=order,
                batch=pooled_order.batch,
                status=new_status,
                actor=request.user,
                notes=notes
            )

            if cur_lat and cur_lng and hasattr(request.user, 'delivery_partner_profile'):
                profile = request.user.delivery_partner_profile
                profile.current_lat = cur_lat
                profile.current_lng = cur_lng
                profile.save(update_fields=['current_lat', 'current_lng', 'updated_at'])

            remaining = pooled_order.batch.pooled_orders.exclude(status=PooledOrder.STATUS_DELIVERED).count()
            if remaining == 0:
                pooled_order.batch.status = DeliveryBatch.STATUS_COMPLETED
                pooled_order.batch.save(update_fields=['status', 'updated_at'])

        return Response({
            'message': f"Order #{pk} status updated to {new_status}.",
            'order_id': order.id,
            'order_status': order.status,
            'pooled_status': pooled_order.status,
            'batch_status': pooled_order.batch.status,
        }, status=status.HTTP_200_OK)


class AdminMetricsReportView(APIView):
    # Returns summary report of orders, batches, and delivery fees
    permission_classes = [IsDispatcherOrAdmin]

    def get(self, request):
        total_orders = Order.objects.count()
        delivered_orders = Order.objects.filter(status=Order.STATUS_DELIVERED).count()
        cancelled_orders = Order.objects.filter(status=Order.STATUS_CANCELLED).count()

        pooled_orders_count = Order.objects.filter(
            delivery_option__in=['scheduled_pooled', 'SCHEDULED_POOLED']
        ).count()

        pooled_rate_pct = round((pooled_orders_count / total_orders * 100), 2) if total_orders > 0 else 0.0
        cancellation_rate_pct = round((cancelled_orders / total_orders * 100), 2) if total_orders > 0 else 0.0

        finance_stats = Order.objects.aggregate(
            total_gmv=Sum('total'),
            total_delivery_fee=Sum('delivery_fee'),
            avg_delivery_fee=Avg('delivery_fee'),
            total_discounts=Sum('discount_amount'),
        )

        total_batches = DeliveryBatch.objects.count()
        completed_batches = DeliveryBatch.objects.filter(status=DeliveryBatch.STATUS_COMPLETED).count()
        active_batches = DeliveryBatch.objects.filter(
            status__in=[DeliveryBatch.STATUS_RELEASED, DeliveryBatch.STATUS_IN_TRANSIT]
        ).count()

        batch_counts = DeliveryBatch.objects.annotate(orders_cnt=Count('pooled_orders')).aggregate(
            avg_orders_per_batch=Avg('orders_cnt')
        )
        avg_batch_density = round(float(batch_counts['avg_orders_per_batch'] or 0.0), 1)

        rider_count = DeliveryPartner.objects.count()
        available_riders = DeliveryPartner.objects.filter(availability_status=DeliveryPartner.STATUS_AVAILABLE).count()

        return Response({
            'overview': {
                'total_order_volume': total_orders,
                'delivered_orders': delivered_orders,
                'cancelled_orders': cancelled_orders,
                'cancellation_rate_pct': cancellation_rate_pct,
            },
            'smart_delivery_economics': {
                'pooled_orders_count': pooled_orders_count,
                'pooled_order_rate_pct': pooled_rate_pct,
                'total_delivery_batches': total_batches,
                'active_batches': active_batches,
                'completed_batches': completed_batches,
                'average_orders_per_batch': avg_batch_density,
                'estimated_delivery_cost_savings_pct': round(min(50.0, avg_batch_density * 8.5), 1) if avg_batch_density > 1 else 0.0,
            },
            'revenue_and_fees': {
                'total_gmv': float(finance_stats['total_gmv'] or 0.0),
                'total_delivery_fees_collected': float(finance_stats['total_delivery_fee'] or 0.0),
                'average_delivery_fee_per_order': round(float(finance_stats['avg_delivery_fee'] or 0.0), 2),
                'total_promotional_discounts': float(finance_stats['total_discounts'] or 0.0),
            },
            'fleet_operations': {
                'total_delivery_partners': rider_count,
                'available_riders': available_riders,
            }
        }, status=status.HTTP_200_OK)
