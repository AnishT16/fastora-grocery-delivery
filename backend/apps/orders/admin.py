from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name_snapshot', 'unit_snapshot', 'quantity', 'unit_price_snapshot', 'total_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'delivery_option', 'subtotal', 'delivery_fee', 'discount_amount', 'total', 'status', 'created_at')
    list_filter = ('status', 'delivery_option', 'delivery_zone', 'created_at')
    search_fields = ('id', 'customer__username', 'customer__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]
