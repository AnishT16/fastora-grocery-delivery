from django.db import transaction, models
from django.utils import timezone
from apps.delivery.models import DeliverySlot
from common.exceptions import SlotNotAvailableError


def get_available_slots(zone_id, target_date=None):
    # Returns open slots for a zone where time hasn't passed cutoff and capacity remains
    now = timezone.now()

    DeliverySlot.objects.filter(
        zone_id=zone_id,
        status=DeliverySlot.STATUS_OPEN,
        cutoff_time__lte=now
    ).update(status=DeliverySlot.STATUS_CLOSED)

    queryset = DeliverySlot.objects.filter(
        zone_id=zone_id,
        status=DeliverySlot.STATUS_OPEN,
        cutoff_time__gt=now,
        current_bookings__lt=models.F('max_capacity')
    )

    if target_date:
        queryset = queryset.filter(date=target_date)

    return queryset.order_by('date', 'start_time')


def reserve_slot_capacity(slot_id):
    # Reserves 1 slot capacity atomically and marks full if capacity reached
    with transaction.atomic():
        try:
            slot = DeliverySlot.objects.select_for_update().get(id=slot_id)
        except DeliverySlot.DoesNotExist:
            raise SlotNotAvailableError(f"Delivery slot #{slot_id} does not exist.")

        now = timezone.now()

        if now >= slot.cutoff_time:
            if slot.status != DeliverySlot.STATUS_CLOSED:
                slot.status = DeliverySlot.STATUS_CLOSED
                slot.save(update_fields=['status'])
            raise SlotNotAvailableError(
                f"Booking closed: slot cutoff was {slot.cutoff_time.strftime('%H:%M, %d %b')}."
            )

        if slot.current_bookings >= slot.max_capacity or slot.status == DeliverySlot.STATUS_FULL:
            if slot.status != DeliverySlot.STATUS_FULL:
                slot.status = DeliverySlot.STATUS_FULL
                slot.save(update_fields=['status'])
            raise SlotNotAvailableError(
                f"Slot is full ({slot.current_bookings}/{slot.max_capacity} orders booked)."
            )

        slot.current_bookings += 1
        if slot.current_bookings >= slot.max_capacity:
            slot.status = DeliverySlot.STATUS_FULL

        slot.save(update_fields=['current_bookings', 'status'])
        return slot


def release_slot_capacity(slot_id):
    # Releases 1 slot capacity on order cancellation
    with transaction.atomic():
        try:
            slot = DeliverySlot.objects.select_for_update().get(id=slot_id)
        except DeliverySlot.DoesNotExist:
            raise SlotNotAvailableError(f"Delivery slot #{slot_id} does not exist.")

        slot.current_bookings = max(0, slot.current_bookings - 1)

        now = timezone.now()
        if slot.status == DeliverySlot.STATUS_FULL and now < slot.cutoff_time:
            slot.status = DeliverySlot.STATUS_OPEN

        slot.save(update_fields=['current_bookings', 'status'])
        return slot
