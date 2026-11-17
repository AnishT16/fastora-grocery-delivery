import math
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.orders.models import Order
from apps.delivery.models import DeliveryZone, DeliveryBatch, PooledOrder
from common.exceptions import InvalidBatchOperationError, DeliveryPartnerNotFoundError


def _calculate_distance(lat1, lng1, lat2, lng2):
    # Calculates Haversine distance between two coordinates in km
    lat1, lon1 = math.radians(lat1), math.radians(lng1)
    lat2, lon2 = math.radians(lat2), math.radians(lng2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return 6371.0 * c


def _nearest_neighbor_sort(orders, start_lat, start_lng):
    # Sorts orders sequentially by nearest delivery point
    remaining = list(orders)
    sorted_route = []
    current_lat = float(start_lat)
    current_lng = float(start_lng)

    while remaining:
        best_idx = 0
        min_dist = float('inf')

        for i, order in enumerate(remaining):
            addr = order.address_snapshot or {}
            o_lat = float(addr.get('latitude') or current_lat)
            o_lng = float(addr.get('longitude') or current_lng)

            dist = _calculate_distance(current_lat, current_lng, o_lat, o_lng)
            if dist < min_dist:
                min_dist = dist
                best_idx = i

        chosen_order = remaining.pop(best_idx)
        sorted_route.append(chosen_order)

        chosen_addr = chosen_order.address_snapshot or {}
        current_lat = float(chosen_addr.get('latitude') or current_lat)
        current_lng = float(chosen_addr.get('longitude') or current_lng)

    return sorted_route


def run_batch_matching(zone_id=None, slot_id=None):
    # Groups eligible pooled orders into batches by zone and slot
    eligible_orders = Order.objects.filter(
        delivery_option__in=['scheduled_pooled', 'SCHEDULED_POOLED'],
        status__in=[Order.STATUS_CONFIRMED, Order.STATUS_PACKING, Order.STATUS_READY],
        pooled_order__isnull=True
    ).select_related('delivery_zone', 'delivery_slot')

    if zone_id:
        eligible_orders = eligible_orders.filter(delivery_zone_id=zone_id)
    if slot_id:
        eligible_orders = eligible_orders.filter(delivery_slot_id=slot_id)

    if not eligible_orders.exists():
        return []

    grouped_orders = {}
    for order in eligible_orders:
        if not order.delivery_zone_id or not order.delivery_slot_id:
            continue
        key = (order.delivery_zone_id, order.delivery_slot_id)
        grouped_orders.setdefault(key, []).append(order)

    processed_batches = []

    for (curr_zone_id, curr_slot_id), orders_for_slot in grouped_orders.items():
        zone = DeliveryZone.objects.get(id=curr_zone_id)
        center_lat = float(zone.center_lat or 23.0365)
        center_lng = float(zone.center_lng or 72.5611)

        batches = list(DeliveryBatch.objects.filter(
            zone_id=curr_zone_id,
            slot_id=curr_slot_id,
            status=DeliveryBatch.STATUS_DRAFT
        ))

        active_batch = None
        for b in batches:
            if b.pooled_orders.count() < b.max_orders:
                active_batch = b
                break

        if not active_batch:
            active_batch = DeliveryBatch.objects.create(
                zone_id=curr_zone_id,
                slot_id=curr_slot_id,
                status=DeliveryBatch.STATUS_DRAFT,
                max_orders=15
            )

        with transaction.atomic():
            remaining_capacity = active_batch.max_orders - active_batch.pooled_orders.count()
            candidate_orders = orders_for_slot[:remaining_capacity]

            ordered_route = _nearest_neighbor_sort(candidate_orders, center_lat, center_lng)

            current_seq = active_batch.pooled_orders.count() + 1
            for order in ordered_route:
                PooledOrder.objects.create(
                    order=order,
                    batch=active_batch,
                    sequence=current_seq,
                    status=PooledOrder.STATUS_QUEUED
                )
                current_seq += 1

                if order.status == Order.STATUS_CONFIRMED:
                    order.status = Order.STATUS_PACKING
                    order.save(update_fields=['status', 'updated_at'])

        processed_batches.append(active_batch)

    return processed_batches


def release_batch(batch_id, delivery_partner_id):
    # Assigns partner and releases batch for delivery
    try:
        partner = User.objects.get(id=delivery_partner_id, role=User.ROLE_DELIVERY_PARTNER)
    except User.DoesNotExist:
        raise DeliveryPartnerNotFoundError(
            f"Delivery partner with User ID #{delivery_partner_id} not found or is not a delivery partner."
        )

    with transaction.atomic():
        try:
            batch = DeliveryBatch.objects.select_for_update().get(id=batch_id)
        except DeliveryBatch.DoesNotExist:
            raise InvalidBatchOperationError(f"Delivery batch #{batch_id} does not exist.")

        if batch.status not in [DeliveryBatch.STATUS_DRAFT, DeliveryBatch.STATUS_RELEASED]:
            raise InvalidBatchOperationError(
                f"Cannot release batch #{batch_id}: current status is '{batch.status}'."
            )

        if batch.pooled_orders.count() == 0:
            raise InvalidBatchOperationError(
                f"Cannot release batch #{batch_id}: no pooled orders in this batch."
            )

        batch.delivery_partner = partner
        batch.status = DeliveryBatch.STATUS_RELEASED
        batch.released_at = timezone.now()
        batch.save(update_fields=['delivery_partner', 'status', 'released_at', 'updated_at'])

        for pooled in batch.pooled_orders.select_related('order'):
            pooled.status = PooledOrder.STATUS_QUEUED
            pooled.save(update_fields=['status'])

            if pooled.order.status in [Order.STATUS_CONFIRMED, Order.STATUS_PACKING]:
                pooled.order.status = Order.STATUS_READY
                pooled.order.save(update_fields=['status', 'updated_at'])

        return batch
