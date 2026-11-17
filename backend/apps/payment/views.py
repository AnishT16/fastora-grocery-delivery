import hashlib
import hmac

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.delivery.models import DeliveryZone
from apps.orders.models import Order
from .models import Payment, PaymentConfig
from .serializers import (
    CODCollectionInputSerializer,
    PaymentConfigSerializer,
    PaymentCreateInputSerializer,
    PaymentRefundInputSerializer,
    PaymentSerializer,
    PaymentVerificationInputSerializer,
)
from .services import (
    collect_cod_payment,
    get_payment_options_for_checkout,
    verify_online_payment,
)


class PaymentVerificationWebhookView(APIView):
    # Webhook callback for online payments to confirm an order
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PaymentVerificationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        order_id = data['order_id']
        txn_ref = data.get('transaction_reference') or f"GATEWAY_VERIFIED_{order_id}"
        payment_status = data.get('payment_status', 'SUCCESS')
        payload = data.get('gateway_payload', {})

        payment = verify_online_payment(
            order_id=order_id,
            transaction_reference=txn_ref,
            payment_status=payment_status,
            raw_gateway_payload=payload
        )

        return Response(
            {
                'message': f"Payment for Order #{order_id} recorded as {payment.status}.",
                'order_status': payment.order.status,
                'is_pooling_eligible': payment.order.is_pooling_eligible,
                'payment': PaymentSerializer(payment).data,
            },
            status=status.HTTP_200_OK
        )


class CODCollectionConfirmView(APIView):
    # Allows delivery partners to confirm cash collection
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CODCollectionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data['order_id']
        payment = collect_cod_payment(order_id=order_id, delivery_partner_user=request.user)

        return Response(
            {
                'message': f"Cash on Delivery of Rs. {payment.amount} successfully collected for Order #{order_id}.",
                'payment': PaymentSerializer(payment).data,
                'order_status': payment.order.status,
            },
            status=status.HTTP_200_OK
        )


class PaymentConfigView(APIView):
    # Returns available payment options and rules for checkout
    permission_classes = [AllowAny]

    def get(self, request):
        zone_id = request.query_params.get('zone_id')
        subtotal = request.query_params.get('subtotal')

        zone = None
        if zone_id:
            zone = DeliveryZone.objects.filter(id=zone_id).first()

        options = get_payment_options_for_checkout(zone=zone, subtotal=subtotal)
        config = PaymentConfig.get_config()

        return Response(
            {
                'options': options,
                'config': PaymentConfigSerializer(config).data,
            },
            status=status.HTTP_200_OK
        )


class PaymentCreateView(APIView):
    # Initializes online payment order for checkout
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data['order_id']

        try:
            if request.user.is_staff:
                order = Order.objects.get(id=order_id)
            else:
                order = Order.objects.get(id=order_id, customer=request.user)
        except Order.DoesNotExist:
            return Response({'error': f"Order #{order_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        payment, _ = Payment.objects.get_or_create(
            order=order,
            defaults={
                'amount': order.total,
                'payment_method': Payment.METHOD_ONLINE,
                'status': Payment.STATUS_PENDING,
                'transaction_reference': f"PAY_{order.id}_{order.created_at.strftime('%Y%m%d%H%M%S')}"
            }
        )

        gateway_order_id = f"rzp_order_{order.id}_{payment.id}"
        return Response({
            'message': 'Payment gateway order initialized.',
            'order_id': order.id,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'transaction_reference': payment.transaction_reference,
            'gateway_order_id': gateway_order_id,
            'payment_status': payment.status,
            'key_id': 'rzp_test_fastora_checkout',
        }, status=status.HTTP_200_OK)


class PaymentWebhookView(APIView):
    # Processes webhook callbacks from payment gateway
    permission_classes = [AllowAny]

    def post(self, request):
        signature = (
            request.headers.get('X-Razorpay-Signature')
            or request.headers.get('HTTP_X_SIGNATURE')
            or request.headers.get('X-Signature')
        )
        payload_data = request.data
        webhook_secret = getattr(settings, 'PAYMENT_WEBHOOK_SECRET', 'fastora_webhook_secret_key')

        if signature:
            body = request.body if hasattr(request, 'body') else b""
            expected_sig = hmac.new(webhook_secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
            if not getattr(settings, 'DEBUG', True) and not hmac.compare_digest(expected_sig, signature):
                return Response({'error': 'Invalid webhook signature'}, status=status.HTTP_400_BAD_REQUEST)

        order_id = payload_data.get('order_id')
        event_type = payload_data.get('event', 'payment.captured')
        txn_ref = payload_data.get('transaction_reference') or payload_data.get('payment_id') or f"WEBHOOK_{order_id}"

        if not order_id:
            entity = payload_data.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = entity.get('notes', {}).get('order_id') or entity.get('order_id')

        if not order_id:
            return Response({'error': 'Missing order_id in webhook payload.'}, status=status.HTTP_400_BAD_REQUEST)

        payment = verify_online_payment(
            order_id=int(order_id),
            transaction_reference=txn_ref,
            payment_status='SUCCESS' if 'captured' in event_type or 'paid' in event_type else 'FAILED',
            raw_gateway_payload=payload_data
        )

        return Response({
            'status': 'processed',
            'order_id': order_id,
            'payment_status': payment.status,
            'order_status': payment.order.status,
        }, status=status.HTTP_200_OK)


class PaymentRefundView(APIView):
    # Processes refunds for an order
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentRefundInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data['order_id']
        refund_amount = serializer.validated_data.get('amount')
        reason = serializer.validated_data.get('reason', 'Customer or Admin requested refund')

        try:
            payment = Payment.objects.select_related('order').get(order_id=order_id)
        except Payment.DoesNotExist:
            return Response({'error': f"Payment for order #{order_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)

        if not (request.user.is_staff or request.user == payment.order.customer):
            return Response({'error': "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        refund_ref = f"REFUND_{payment.order.id}_{hashlib.md5(f'{payment.id}_{reason}'.encode()).hexdigest()[:8].upper()}"
        payment.mark_refunded(refund_ref=refund_ref, refund_amount=refund_amount, reason=reason)

        return Response({
            'message': f"Payment of Rs. {payment.refund_amount} refunded successfully.",
            'refund_reference': payment.refund_reference,
            'payment_status': payment.status,
            'order_status': payment.order.status,
        }, status=status.HTTP_200_OK)
