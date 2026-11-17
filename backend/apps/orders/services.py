from decimal import Decimal
from django.db import transaction
from django.utils import timezone
import uuid

from .models import Order, OrderItem
from apps.accounts.models import Address
from apps.delivery.models import DeliveryZone
from apps.delivery.services.pricing_service import calculate_delivery_quote
from apps.delivery.services.slot_service import reserve_slot_capacity, release_slot_capacity
from apps.inventory.services import reserve_stock, release_stock
from apps.payment.models import Payment, PaymentConfig
from common.exceptions import (
    EmptyCartError,
    AddressNotFoundError,
    ProductNotFoundError,
    ZoneNotServiceableError,
    SlotNotAvailableError,
    CODNotAllowedError,
    OrderNotFoundError,
    InvalidOrderOperationError,
)
from rest_framework.exceptions import PermissionDenied


def create_order_from_cart(user, cart, address_id, delivery_option, slot_id=None, payment_method='COD'):
    # places an order from cart items, checks stock and calculates delivery fee
    if cart is None:
        raise EmptyCartError("Shopping cart does not exist.")

    # resolve delivery address
    address = None
    if isinstance(address_id, Address):
        address = address_id
    elif isinstance(address_id, int):
        try:
            address = Address.objects.get(id=address_id, customer=user)
        except Address.DoesNotExist:
            raise AddressNotFoundError(f"Delivery address #{address_id} does not exist for this user.")
    elif isinstance(address_id, dict):
        address = address_id
    else:
        raise AddressNotFoundError("A valid delivery address must be specified for checkout.")

    # delivery option and payment method
    opt_str = str(delivery_option).upper()
    if 'POOLED' in opt_str or 'SCHEDULED' in opt_str:
        norm_delivery_option = Order.DELIVERY_SCHEDULED_POOLED
    else:
        norm_delivery_option = Order.DELIVERY_EXPRESS

    pm_str = str(payment_method).upper()
    if 'ONLINE' in pm_str:
        norm_payment_method = Order.PAYMENT_METHOD_ONLINE
    else:
        norm_payment_method = Order.PAYMENT_METHOD_COD

    with transaction.atomic():
        cart_items = list(cart.items.select_related('product', 'product__inventory').all())
        if not cart_items:
            raise EmptyCartError("Cannot place order: your shopping cart is empty.")

        # calculate subtotal
        subtotal = Decimal('0.00')
        for item in cart_items:
            product = item.product
            price = getattr(product, 'current_price', None) or getattr(product, 'price', None)
            if price is None:
                raise ProductNotFoundError(f"Product '{product.name}' has no active price or inventory record.")
            subtotal += price * item.quantity

        # reserve inventory for all items
        for item in cart_items:
            reserve_stock(product_id=item.product.id, quantity=item.quantity)

        # reserve slot capacity if scheduled delivery
        slot = None
        if norm_delivery_option == Order.DELIVERY_SCHEDULED_POOLED:
            if not slot_id:
                raise SlotNotAvailableError("Please select a delivery slot for scheduled delivery.")
            slot = reserve_slot_capacity(slot_id=slot_id)

        # calculate delivery quote
        quote = calculate_delivery_quote(
            address=address,
            cart_subtotal=subtotal,
            delivery_option=norm_delivery_option,
            slot_id=slot.id if slot else None,
            user=user
        )

        if not quote.get('is_serviceable', False):
            raise ZoneNotServiceableError(
                quote.get('explanation_message') or "Your address is outside all active delivery zones."
            )

        zone_id = quote.get('zone_id')
        zone = DeliveryZone.objects.filter(id=zone_id).first() if zone_id else None
        delivery_fee = Decimal(str(quote.get('final_fee', '0.00')))
        discount_amount = Decimal(str(quote.get('pooled_discount', '0.00'))) + Decimal(str(quote.get('membership_discount', '0.00')))
        total = subtotal + delivery_fee

        # validate COD availability
        if norm_payment_method == Order.PAYMENT_METHOD_COD:
            payment_config = PaymentConfig.get_config()
            cod_allowed, cod_block_reason = payment_config.is_cod_allowed_for(zone=zone, subtotal=subtotal)
            if not cod_allowed:
                raise CODNotAllowedError(cod_block_reason)

        if norm_payment_method == Order.PAYMENT_METHOD_ONLINE:
            initial_order_status = Order.STATUS_PENDING_PAYMENT
            initial_payment_status = Payment.STATUS_PENDING
        else:
            initial_order_status = Order.STATUS_CONFIRMED
            initial_payment_status = Payment.STATUS_COD_PENDING

        # snapshot delivery address
        if hasattr(address, 'postal_code'):
            address_snapshot = {
                'id': getattr(address, 'id', None),
                'title': getattr(address, 'title', 'Home'),
                'street_address': getattr(address, 'street_address', ''),
                'landmark': getattr(address, 'landmark', ''),
                'city': getattr(address, 'city', 'Pune'),
                'state': getattr(address, 'state', 'Maharashtra'),
                'postal_code': getattr(address, 'postal_code', ''),
                'latitude': float(address.latitude) if getattr(address, 'latitude', None) is not None else None,
                'longitude': float(address.longitude) if getattr(address, 'longitude', None) is not None else None,
            }
        else:
            address_snapshot = dict(address)

        order = Order.objects.create(
            customer=user,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            discount_amount=discount_amount,
            total=total,
            delivery_option=norm_delivery_option,
            payment_method=norm_payment_method,
            delivery_zone=zone,
            delivery_slot=slot,
            address_snapshot=address_snapshot,
            pricing_rule_snapshot=quote,
            status=initial_order_status
        )

        order_items = []
        for item in cart_items:
            unit_price = getattr(item.product, 'current_price', None) or getattr(item.product, 'price', None)
            order_items.append(
                OrderItem(
                    order=order,
                    product=item.product,
                    product_name_snapshot=item.product.name,
                    unit_snapshot=item.product.unit,
                    quantity=item.quantity,
                    unit_price_snapshot=unit_price,
                    total_price=unit_price * item.quantity,
                )
            )
        OrderItem.objects.bulk_create(order_items)

        # payment record
        prefix = 'PAY' if norm_payment_method == Order.PAYMENT_METHOD_ONLINE else 'COD'
        txn_ref = f"{prefix}_{order.id}_{uuid.uuid4().hex[:8].upper()}"

        Payment.objects.create(
            order=order,
            payment_method=norm_payment_method,
            amount=total,
            status=initial_payment_status,
            transaction_reference=txn_ref,
            gateway_response={'created_at': timezone.now().isoformat()}
        )

        # clear cart after order placement
        cart.clear()
        return order


def cancel_order(order_id, user, reason="Customer requested cancellation"):
    # cancel order and roll back stock and slot capacity
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            raise OrderNotFoundError(f"Order #{order_id} does not exist.")

        is_owner = (order.customer == user)
        is_staff = bool(user and (user.is_staff or user.is_dispatcher()))
        if not (is_owner or is_staff):
            raise PermissionDenied("You do not have permission to cancel this order.")

        if order.status in [Order.STATUS_DISPATCHED, Order.STATUS_DELIVERED]:
            raise InvalidOrderOperationError(
                f"Cannot cancel Order #{order_id}: order is already {order.get_status_display()}."
            )
        if order.status == Order.STATUS_CANCELLED:
            return order

        # return reserved inventory
        for item in order.items.select_related('product').all():
            release_stock(product_id=item.product.id, quantity=item.quantity)

        # return slot booking capacity
        if order.delivery_slot:
            release_slot_capacity(order.delivery_slot.id)

        # remove from delivery batch if already assigned
        if hasattr(order, 'pooled_order') and order.pooled_order:
            batch = order.pooled_order.batch
            order.pooled_order.delete()

            remaining_pooled = batch.pooled_orders.order_by('sequence').all()
            for idx, p in enumerate(remaining_pooled, start=1):
                if p.sequence != idx:
                    p.sequence = idx
                    p.save(update_fields=['sequence'])

        # update payment status to refunded if online
        if hasattr(order, 'payment') and order.payment:
            payment = order.payment
            if payment.status == Payment.STATUS_SUCCESS:
                refund_ref = f"REFUND_{order.id}_{uuid.uuid4().hex[:8].upper()}"
                payment.mark_refunded(refund_ref=refund_ref, reason=reason)
            elif payment.status in [Payment.STATUS_PENDING, Payment.STATUS_COD_PENDING]:
                payment.status = Payment.STATUS_REFUNDED
                payment.save(update_fields=['status', 'updated_at'])

        order.status = Order.STATUS_CANCELLED
        order.cancellation_reason = reason
        order.save(update_fields=['status', 'cancellation_reason', 'updated_at'])

        # record delivery event
        from apps.delivery.models import DeliveryEvent
        DeliveryEvent.objects.create(
            order=order,
            status=Order.STATUS_CANCELLED,
            actor=user if user.is_authenticated else None,
            notes=reason
        )

        return order
