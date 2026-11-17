from django.contrib import admin
from .models import Inventory


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'location_id',
        'quantity_available',
        'reserved_quantity',
        'price',
        'status',
        'updated_at',
    )
    list_filter = ('status', 'location_id')
    search_fields = ('product__name', 'location_id')
    readonly_fields = ('status', 'created_at', 'updated_at')
