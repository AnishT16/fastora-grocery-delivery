from rest_framework import serializers
from .models import Payment, PaymentConfig


class PaymentSerializer(serializers.ModelSerializer):
    """Full representation of a payment transaction"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'order_id',
            'payment_method',
            'payment_method_display',
            'transaction_reference',
            'amount',
            'currency',
            'status',
            'status_display',
            'collected_at',
            'gateway_response',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class PaymentVerificationInputSerializer(serializers.Serializer):
    """Input validation for gateway webhook / transaction verification"""
    order_id = serializers.IntegerField(required=True)
    transaction_reference = serializers.CharField(required=False, allow_blank=True, default="")
    payment_status = serializers.ChoiceField(choices=['SUCCESS', 'FAILED', 'success', 'failed'], default='SUCCESS')
    gateway_payload = serializers.DictField(required=False, default=dict)


class CODCollectionInputSerializer(serializers.Serializer):
    """Input validation for delivery partner cash collection confirmation"""
    order_id = serializers.IntegerField(required=True)


class PaymentConfigSerializer(serializers.ModelSerializer):
    """Admin configuration state representation"""
    disabled_zones_count = serializers.IntegerField(source='disabled_cod_zones.count', read_only=True)

    class Meta:
        model = PaymentConfig
        fields = [
            'is_cod_enabled_globally',
            'min_order_for_cod',
            'max_order_for_cod',
            'disabled_zones_count',
            'updated_at',
        ]


class PaymentCreateInputSerializer(serializers.Serializer):
    """Input validation for creating a payment gateway intent"""
    order_id = serializers.IntegerField(required=True)


class PaymentRefundInputSerializer(serializers.Serializer):
    """Input validation for processing a refund"""
    order_id = serializers.IntegerField(required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    reason = serializers.CharField(required=False, default="Requested by customer/admin")

