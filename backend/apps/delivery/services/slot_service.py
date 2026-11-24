from datetime import datetime, time, timedelta
from django.db import transaction, models
from django.utils import timezone
from ..models import DeliveryZone, DeliverySlot
from common.exceptions import SlotNotAvailableError


def ensure_rolling_slots(zone_id):
    # Generates rolling 1-2 hour quick-commerce delivery slots for today and tomorrow
    zone = DeliveryZone.objects.filter(id=zone_id).first()
    if not zone:
        return

    now = timezone.now()
    local_now = timezone.localtime(now)
    today = local_now.date()

    for day_offset in [0, 1]:
        slot_date = today + timedelta(days=day_offset)
        # Generate 1-hour micro-delivery windows from 07:00 to 22:00
        for start_hour in range(7, 22):
            end_hour = start_hour + 1
            start_t = time(start_hour, 0)
            end_t = time(end_hour, 0)

            slot_start_dt = timezone.make_aware(
                datetime.combine(slot_date, start_t),
                timezone.get_current_timezone()
            )
            # Cutoff is 15 minutes before the delivery window starts
            cutoff_dt = slot_start_dt - timedelta(minutes=15)

            if cutoff_dt > now:
                slot, created = DeliverySlot.objects.get_or_create(
                    zone=zone,
                    date=slot_date,
                    start_time=start_t,
                    end_time=end_t,
                    defaults={
                        'max_capacity': 15,
                        'current_bookings': 0,
                        'cutoff_time': cutoff_dt,
                        'status': DeliverySlot.STATUS_OPEN
                    }
                )
                if not created and (slot.cutoff_time != cutoff_dt or (slot.status == DeliverySlot.STATUS_CLOSED and slot.current_bookings < slot.max_capacity)):
                    slot.cutoff_time = cutoff_dt
                    slot.status = DeliverySlot.STATUS_OPEN
                    slot.save(update_fields=['cutoff_time', 'status'])


def get_available_slots(zone_id, target_date=None):
    # Returns open slots for a zone where time hasn't passed cutoff and capacity remains
    ensure_rolling_slots(zone_id)

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
