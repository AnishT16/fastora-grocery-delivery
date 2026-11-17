from rest_framework import serializers
from .models import Inventory


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_unit = serializers.CharField(source='product.unit', read_only=True)
    product_category = serializers.CharField(source='product.category.name', read_only=True)
    total_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id',
            'product',
            'product_name',
            'product_unit',
            'product_category',
            'location_id',
            'quantity_available',
            'reserved_quantity',
            'total_stock',
            'price',
            'low_stock_threshold',
            'status',
            'updated_at',
        ]
        read_only_fields = ['id', 'reserved_quantity', 'total_stock', 'status', 'updated_at']


class InventoryStockUpdateSerializer(serializers.Serializer):
    quantity_delta = serializers.IntegerField(
        required=True,
        help_text="Positive to restock, negative to deduct stock"
    )
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
