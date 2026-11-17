from rest_framework import serializers
from decimal import Decimal
from .models import Category, Product
from apps.inventory.models import Inventory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_active']


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = [
            'id',
            'location_id',
            'quantity_available',
            'reserved_quantity',
            'price',
            'status',
            'updated_at',
        ]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    price = serializers.SerializerMethodField()
    quantity_available = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    pack_size = serializers.CharField(source='unit', required=False)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'unit',
            'pack_size',
            'category',
            'category_id',
            'image',
            'is_active',
            'price',
            'quantity_available',
            'stock_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_price(self, obj):
        if hasattr(obj, 'inventory') and obj.inventory:
            return str(obj.inventory.price)
        return None

    def get_quantity_available(self, obj):
        if hasattr(obj, 'inventory') and obj.inventory:
            return obj.inventory.quantity_available
        return 0

    def get_stock_status(self, obj):
        if hasattr(obj, 'inventory') and obj.inventory:
            return obj.inventory.status
        return Inventory.STATUS_OUT_OF_STOCK


class ProductAdminSerializer(ProductSerializer):
    """
    Extended serializer for Admin CRUD operations that allows
    setting initial price, stock quantity, and location atomically.
    """
    initial_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        write_only=True,
        required=False
    )
    initial_stock = serializers.IntegerField(
        min_value=0,
        write_only=True,
        required=False
    )
    location_id = serializers.CharField(
        max_length=100,
        default='DARK_STORE_01',
        write_only=True,
        required=False
    )

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['initial_price', 'initial_stock', 'location_id']

    def create(self, validated_data):
        price = validated_data.pop('initial_price', Decimal('0.00'))
        stock = validated_data.pop('initial_stock', 0)
        location = validated_data.pop('location_id', 'DARK_STORE_01')

        product = Product.objects.create(**validated_data)
        Inventory.objects.create(
            product=product,
            location_id=location,
            quantity_available=stock,
            reserved_quantity=0,
            price=price
        )
        return product

    def update(self, instance, validated_data):
        price = validated_data.pop('initial_price', None)
        stock = validated_data.pop('initial_stock', None)
        location = validated_data.pop('location_id', None)

        product = super().update(instance, validated_data)

        if price is not None or stock is not None or location is not None:
            inventory, _ = Inventory.objects.get_or_create(
                product=product,
                defaults={'price': Decimal('0.00'), 'quantity_available': 0}
            )
            if price is not None:
                inventory.price = price
            if stock is not None:
                inventory.quantity_available = stock
            if location is not None:
                inventory.location_id = location
            inventory.save()

        return product
