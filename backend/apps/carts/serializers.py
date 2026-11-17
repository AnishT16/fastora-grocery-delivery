from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.models import Product


class CartProductSummarySerializer(serializers.ModelSerializer):
    """Compact product details embedded inside cart items"""
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    stock_status = serializers.CharField(read_only=True)
    quantity_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'unit',
            'pack_size',
            'price',
            'stock_status',
            'quantity_available',
            'image_url',
        ]


class CartItemSerializer(serializers.ModelSerializer):
    """Detailed CartItem representation"""
    product = CartProductSummarySerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
        source='product',
        write_only=True
    )
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_id',
            'quantity',
            'unit_price_snapshot',
            'total_price',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'unit_price_snapshot', 'total_price', 'created_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    """Full shopping cart representation"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id',
            'total_items',
            'subtotal',
            'items',
            'created_at',
            'updated_at',
        ]


class AddToCartSerializer(serializers.Serializer):
    """Input payload validation for adding an item to the cart"""
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=False, default=1, min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    """Input payload validation for modifying item quantity"""
    quantity = serializers.IntegerField(required=True, min_value=0)
