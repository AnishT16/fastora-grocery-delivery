from django.db import transaction

from .models import Payment, PaymentConfig
from apps.orders.models import Order
from common.exceptions import FastoraException


class PaymentNotFoundError(FastoraException):
    default_detail = 'The payment record for this order does not exist.'
    default_code = 'payment_not_found'


class OrderNotFoundError(FastoraException):
    default_detail = 'The specified order was not found.'
    default_code = 'order_not_found'


def verify_online_payment(order_id, transaction_reference=None, payment_status='SUCCESS', raw_gateway_payload=None):
    # Updates payment record and confirms order on gateway verification
    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(order_id=order_id)
        except Payment.DoesNotExist:
            raise PaymentNotFoundError(f"No payment record found for Order #{order_id}.")

        status_norm = str(payment_status).upper()
        if status_norm == 'SUCCESS':
            payment.mark_success(ref=transaction_reference, raw_response=raw_gateway_payload)
        else:
            payment.mark_failed(error_details=raw_gateway_payload or {'error': 'Transaction rejected by gateway.'})

        return payment


def collect_cod_payment(order_id, delivery_partner_user):
    # Confirms cash collection by delivery partner on doorstep delivery
    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(order_id=order_id)
        except Payment.DoesNotExist:
            raise PaymentNotFoundError(f"No payment record found for Order #{order_id}.")

        partner_name = getattr(delivery_partner_user, 'username', 'delivery_partner')
        payment.mark_cod_collected(collected_by=partner_name)

        order = payment.order
        if order.status in [Order.STATUS_DISPATCHED, 'in_transit']:
            order.status = Order.STATUS_DELIVERED
            order.save(update_fields=['status', 'updated_at'])

        return payment


def get_payment_options_for_checkout(zone=None, subtotal=None):
    # Evaluates COD eligibility based on zone and cart subtotal
    config = PaymentConfig.get_config()
    cod_allowed, reason = config.is_cod_allowed_for(zone=zone, subtotal=subtotal)

    return {
        'online_enabled': True,
        'cod_enabled': cod_allowed,
        'cod_restriction_reason': reason if not cod_allowed else "",
        'min_order_for_cod': float(config.min_order_for_cod),
        'max_order_for_cod': float(config.max_order_for_cod),
    }
