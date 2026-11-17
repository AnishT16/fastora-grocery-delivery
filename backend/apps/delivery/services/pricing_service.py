from decimal import Decimal
from django.utils import timezone
from django.db.models import F

from apps.delivery.models import DeliverySlot, DeliveryFeeRule
from apps.delivery.services.zone_service import get_serviceable_zone
from apps.memberships.services import is_member_active, apply_membership_benefits
from common.exceptions import ZoneNotServiceableError


def calculate_delivery_quote(address, cart_subtotal, delivery_option, slot_id=None, user=None):
    # Calculates base fee, distance fee, pooled discount, and membership discount
    subtotal = Decimal(str(cart_subtotal))
    option_normalized = str(delivery_option).upper()
    if 'POOLED' in option_normalized or 'SCHEDULED' in option_normalized:
        option = DeliveryFeeRule.OPTION_SCHEDULED_POOLED
    else:
        option = DeliveryFeeRule.OPTION_EXPRESS

    # Identify delivery zone
    try:
        zone = get_serviceable_zone(address)
    except ZoneNotServiceableError as e:
        return {
            'base_fee': 0.00,
            'distance_fee': 0.00,
            'pooled_discount': 0.00,
            'membership_discount': 0.00,
            'final_fee': 0.00,
            'applied_rule_id': None,
            'distance_km': 0.00,
            'is_serviceable': False,
            'delivery_option': option,
            'zone_id': None,
            'explanation_message': str(e),
        }

    # Compute distance from dark store
    lat = None
    lng = None
    if hasattr(address, 'latitude') and address.latitude is not None:
        lat = address.latitude
        lng = address.longitude
    elif isinstance(address, dict):
        lat = address.get('latitude') or address.get('lat')
        lng = address.get('longitude') or address.get('lng')

    if lat is not None and lng is not None and zone.center_lat is not None and zone.center_lng is not None:
        distance_km = zone.calculate_distance_km(float(lat), float(lng))
    else:
        distance_km = 2.0

    dist_dec = Decimal(str(round(distance_km, 2)))

    # Check slot availability
    explanation_message = ""
    if option == DeliveryFeeRule.OPTION_SCHEDULED_POOLED:
        now = timezone.now()
        if slot_id:
            slot = DeliverySlot.objects.filter(id=slot_id, zone=zone).first()
            if not slot:
                explanation_message = f"Selected slot #{slot_id} does not exist in this zone. Express delivery is available."
            elif slot.status == DeliverySlot.STATUS_FULL or slot.current_bookings >= slot.max_capacity:
                explanation_message = f"Selected scheduled window ({slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}) is fully booked. Express delivery is available as an alternative."
            elif now >= slot.cutoff_time:
                explanation_message = f"Order cutoff for this window passed at {slot.cutoff_time.strftime('%H:%M')}. Later slots or express delivery are available."
        else:
            has_open_slots = DeliverySlot.objects.filter(
                zone=zone,
                status=DeliverySlot.STATUS_OPEN,
                cutoff_time__gt=now,
                current_bookings__lt=F('max_capacity')
            ).exists()
            if not has_open_slots:
                explanation_message = "No scheduled pooling windows are currently open for this zone. Express delivery is recommended."

    # Look up delivery fee rule
    rule = DeliveryFeeRule.objects.filter(
        zone=zone,
        delivery_option=option,
        is_active=True
    ).first()

    if not rule:
        rule = DeliveryFeeRule.objects.filter(
            zone__isnull=True,
            delivery_option=option,
            is_active=True
        ).first()

    if rule:
        base_fee = rule.base_fee
        per_km_fee = rule.per_km_fee
        min_order_discount = rule.min_order_for_discount
        rule_pooled_discount = rule.pooled_discount_amount
        rule_id = rule.id
    else:
        base_fee = Decimal('35.00') if option == DeliveryFeeRule.OPTION_EXPRESS else Decimal('25.00')
        per_km_fee = Decimal('5.00')
        min_order_discount = Decimal('499.00')
        rule_pooled_discount = Decimal('15.00')
        rule_id = None

    distance_fee = round(dist_dec * per_km_fee, 2)
    nominal_fee = base_fee + distance_fee

    has_membership = is_member_active(user)
    pooled_discount = Decimal('0.00')
    membership_discount = Decimal('0.00')

    if option == DeliveryFeeRule.OPTION_SCHEDULED_POOLED:
        pooled_discount = min(rule_pooled_discount, nominal_fee)

    fee_after_pooling = max(Decimal('0.00'), nominal_fee - pooled_discount)

    if has_membership:
        final_fee = apply_membership_benefits(user, subtotal, fee_after_pooling)
        membership_discount = max(Decimal('0.00'), fee_after_pooling - final_fee)
    elif min_order_discount and subtotal >= min_order_discount:
        membership_discount = fee_after_pooling
        final_fee = Decimal('0.00')
    else:
        floor_fee = Decimal('10.00') if option == DeliveryFeeRule.OPTION_SCHEDULED_POOLED else Decimal('20.00')
        final_fee = max(floor_fee, fee_after_pooling)
        pooled_discount = max(Decimal('0.00'), nominal_fee - final_fee)

    return {
        'base_fee': float(base_fee),
        'distance_fee': float(distance_fee),
        'pooled_discount': float(pooled_discount),
        'membership_discount': float(membership_discount),
        'final_fee': float(final_fee),
        'applied_rule_id': rule_id,
        'distance_km': float(distance_km),
        'is_serviceable': True,
        'is_free': final_fee == Decimal('0.00'),
        'delivery_option': option,
        'zone_id': zone.id,
        'has_membership': has_membership,
        'explanation_message': explanation_message,
    }
