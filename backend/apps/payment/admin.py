from django.contrib import admin
from .models import Payment, PaymentConfig


@admin.register(PaymentConfig)
class PaymentConfigAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_cod_enabled_globally', 'min_order_for_cod', 'max_order_for_cod', 'updated_at')
    filter_horizontal = ('disabled_cod_zones',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'payment_method', 'amount', 'currency', 'status', 'transaction_reference', 'collected_at', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('transaction_reference', 'order__id', 'order__customer__username')
