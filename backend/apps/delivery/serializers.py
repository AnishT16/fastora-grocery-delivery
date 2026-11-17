from rest_framework import serializers
from .models import (
    DeliveryZone,
    DeliverySlot,
    DeliveryBatch,
    PooledOrder,
    DeliveryPartner,
    DeliveryEvent,
)


class DeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryZone
        fields = ['id', 'name', 'postal_codes', 'center_lat', 'center_lng', 'radius_km', 'is_active']


class DeliverySlotSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = DeliverySlot
        fields = [
            'id',
            'zone',
            'zone_name',
            'date',
            'start_time',
            'end_time',
            'max_capacity',
            'current_bookings',
            'cutoff_time',
            'status',
            'is_available',
        ]


class SlotReservationSerializer(serializers.Serializer):
    slot_id = serializers.IntegerField(required=True)


class PooledOrderSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    customer_name = serializers.CharField(source='order.customer.get_full_name', read_only=True)
    customer_phone = serializers.CharField(source='order.customer.phone', read_only=True)
    address_snapshot = serializers.JSONField(source='order.address_snapshot', read_only=True)
    order_total = serializers.DecimalField(source='order.total', max_digits=10, decimal_places=2, read_only=True)
    payment_method = serializers.CharField(source='order.payment_method', read_only=True)
    payment_status = serializers.CharField(source='order.payment.status', read_only=True)

    class Meta:
        model = PooledOrder
        fields = [
            'id',
            'order_id',
            'customer_name',
            'customer_phone',
            'sequence',
            'status',
            'address_snapshot',
            'order_total',
            'payment_method',
            'payment_status',
            'delivered_at',
        ]


class DeliveryBatchSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    slot_window = serializers.SerializerMethodField()
    partner_name = serializers.CharField(source='delivery_partner.username', read_only=True)
    pooled_orders = PooledOrderSerializer(many=True, read_only=True)
    total_orders = serializers.IntegerField(source='order_count', read_only=True)

    class Meta:
        model = DeliveryBatch
        fields = [
            'id',
            'zone',
            'zone_name',
            'slot',
            'slot_window',
            'delivery_partner',
            'partner_name',
            'status',
            'max_orders',
            'total_orders',
            'released_at',
            'created_at',
            'pooled_orders',
        ]

    def get_slot_window(self, obj):
        if obj.slot:
            return f"{obj.slot.date} {obj.slot.start_time.strftime('%H:%M')}-{obj.slot.end_time.strftime('%H:%M')}"
        return ""


class BatchReleaseSerializer(serializers.Serializer):
    delivery_partner_id = serializers.IntegerField(required=True)


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            PooledOrder.STATUS_PICKED_UP,
            PooledOrder.STATUS_DELIVERED,
            PooledOrder.STATUS_FAILED,
        ]
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    current_lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    current_lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)


class DeliveryPartnerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = DeliveryPartner
        fields = [
            'id',
            'user',
            'username',
            'email',
            'phone',
            'availability_status',
            'vehicle_type',
            'current_lat',
            'current_lng',
            'updated_at',
        ]


class DeliveryEventSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = DeliveryEvent
        fields = ['id', 'order', 'batch', 'status', 'actor_username', 'notes', 'timestamp']
