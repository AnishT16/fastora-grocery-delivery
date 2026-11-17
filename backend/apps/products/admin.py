from django.contrib import admin
from .models import Category, Product
from apps.inventory.models import Inventory


class InventoryInline(admin.StackedInline):
    model = Inventory
    can_delete = False
    extra = 0
    fields = ('location_id', 'quantity_available', 'reserved_quantity', 'price', 'low_stock_threshold', 'status')
    readonly_fields = ('status',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'get_price', 'get_available_stock', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    inlines = [InventoryInline]

    @admin.display(description='Price (₹)')
    def get_price(self, obj):
        return obj.price if obj.price is not None else '-'

    @admin.display(description='Available Stock')
    def get_available_stock(self, obj):
        return obj.quantity_available
