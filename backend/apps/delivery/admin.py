from django.contrib import admin
from .models import (
    DeliveryZone,
    DeliverySlot,
    DeliveryFeeRule,
    DeliveryBatch,
    PooledOrder,
    DeliveryPartner,
    DeliveryEvent,
)


class PooledOrderInline(admin.TabularInline):
    model = PooledOrder
    extra = 0
    fields = ('sequence', 'order', 'status', 'delivered_at')


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'radius_km', 'center_lat', 'center_lng', 'postal_codes_count', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)

    @admin.display(description='Serviced Codes')
    def postal_codes_count(self, obj):
        return len(obj.postal_codes) if isinstance(obj.postal_codes, list) else 0


@admin.register(DeliverySlot)
class DeliverySlotAdmin(admin.ModelAdmin):
    list_display = ('zone', 'date', 'start_time', 'end_time', 'max_capacity', 'current_bookings', 'status', 'cutoff_time')
    list_filter = ('zone', 'date', 'status')
    ordering = ('-date', 'start_time')


@admin.register(DeliveryFeeRule)
class DeliveryFeeRuleAdmin(admin.ModelAdmin):
    list_display = ('zone', 'delivery_option', 'base_fee', 'per_km_fee', 'min_order_for_discount', 'pooled_discount_amount', 'is_active')
    list_filter = ('delivery_option', 'is_active', 'zone')


@admin.register(DeliveryBatch)
class DeliveryBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'zone', 'slot', 'delivery_partner', 'status', 'max_orders', 'released_at', 'created_at')
    list_filter = ('status', 'zone')
    inlines = [PooledOrderInline]


@admin.register(PooledOrder)
class PooledOrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'batch', 'sequence', 'status', 'delivered_at')
    list_filter = ('status', 'batch__zone')


@admin.register(DeliveryPartner)
class DeliveryPartnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'availability_status', 'vehicle_type', 'created_at')
    list_filter = ('availability_status', 'vehicle_type')
    search_fields = ('user__username', 'user__email', 'vehicle_type')


@admin.register(DeliveryEvent)
class DeliveryEventAdmin(admin.ModelAdmin):
    list_display = ('order', 'batch', 'status', 'actor', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('order__id', 'status', 'notes')
    ordering = ('-timestamp',)
