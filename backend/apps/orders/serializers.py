from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product_id',
            'product_name_snapshot',
            'unit_snapshot',
            'quantity',
            'unit_price_snapshot',
            'total_price',
        ]
        read_only_fields = fields


class OrderCheckoutInputSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=False, allow_null=True)
    address = serializers.DictField(required=False, allow_null=True)
    delivery_option = serializers.ChoiceField(
        choices=[
            'EXPRESS', 'SCHEDULED_POOLED',
            'express', 'scheduled_pooled',
        ],
        default='SCHEDULED_POOLED'
    )
    payment_method = serializers.ChoiceField(
        choices=[
            'ONLINE', 'COD',
            'online', 'cod',
        ],
        default='COD'
    )
    slot_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs.get('address_id') and not attrs.get('address'):
            raise serializers.ValidationError("Either 'address_id' or a raw 'address' object must be provided.")
        opt = attrs.get('delivery_option', '').upper()
        if ('POOLED' in opt or 'SCHEDULED' in opt) and not attrs.get('slot_id'):
            raise serializers.ValidationError(
                {'slot_id': "A valid 'slot_id' is required when selecting Scheduled Micro-Delivery."}
            )
        return attrs


class OrderListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    delivery_option_display = serializers.CharField(source='get_delivery_option_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    total_items = serializers.SerializerMethodField()
    delivery_zone_name = serializers.CharField(source='delivery_zone.name', default=None, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'status',
            'status_display',
            'delivery_option',
            'delivery_option_display',
            'payment_method',
            'payment_method_display',
            'subtotal',
            'delivery_fee',
            'discount_amount',
            'total',
            'total_items',
            'delivery_zone_name',
            'created_at',
            'updated_at',
        ]

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    delivery_option_display = serializers.CharField(source='get_delivery_option_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    delivery_zone_name = serializers.CharField(source='delivery_zone.name', default=None, read_only=True)
    slot_details = serializers.SerializerMethodField()
    batch_tracking = serializers.SerializerMethodField()
    payment_details = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'customer_username',
            'status',
            'status_display',
            'delivery_option',
            'delivery_option_display',
            'payment_method',
            'payment_method_display',
            'subtotal',
            'delivery_fee',
            'discount_amount',
            'total',
            'delivery_zone_name',
            'slot_details',
            'batch_tracking',
            'payment_details',
            'address_snapshot',
            'pricing_rule_snapshot',
            'is_pooling_eligible',
            'items',
            'created_at',
            'updated_at',
        ]

    def get_payment_details(self, obj):
        if hasattr(obj, 'payment') and obj.payment:
            p = obj.payment
            return {
                'id': p.id,
                'payment_method': p.payment_method,
                'status': p.status,
                'status_display': p.get_status_display(),
                'amount': float(p.amount),
                'transaction_reference': p.transaction_reference,
                'collected_at': p.collected_at.isoformat() if p.collected_at else None,
            }
        return None

    def get_slot_details(self, obj):
        slot = obj.delivery_slot
        if not slot:
            return None
        return {
            'id': slot.id,
            'date': str(slot.date),
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'cutoff_time': slot.cutoff_time.isoformat(),
            'status': slot.status,
        }

    def get_batch_tracking(self, obj):
        if hasattr(obj, 'pooled_order') and obj.pooled_order:
            po = obj.pooled_order
            batch = po.batch
            return {
                'batch_id': batch.id,
                'batch_status': batch.status,
                'stop_sequence': po.sequence,
                'pooled_order_status': po.status,
                'delivery_partner': batch.delivery_partner.username if batch.delivery_partner else None,
                'released_at': batch.released_at.isoformat() if batch.released_at else None,
            }
        return None
