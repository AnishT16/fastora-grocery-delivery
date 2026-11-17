from django.db import models
from django.utils import timezone
from decimal import Decimal


class Inventory(models.Model):
    STATUS_IN_STOCK = 'IN_STOCK'
    STATUS_LOW_STOCK = 'LOW_STOCK'
    STATUS_OUT_OF_STOCK = 'OUT_OF_STOCK'

    STATUS_CHOICES = [
        (STATUS_IN_STOCK, 'In Stock'),
        (STATUS_LOW_STOCK, 'Low Stock'),
        (STATUS_OUT_OF_STOCK, 'Out of Stock'),
    ]

    product = models.OneToOneField(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    location_id = models.CharField(
        max_length=100,
        default='DARK_STORE_01',
        help_text="Dark store or fulfillment hub code"
    )
    quantity_available = models.PositiveIntegerField(
        default=0,
        help_text="Stock currently available for customers to order"
    )
    reserved_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Stock temporarily reserved by pending/processing orders"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Selling price per unit from this inventory hub"
    )
    low_stock_threshold = models.PositiveIntegerField(default=5)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_IN_STOCK
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Inventories'
        indexes = [
            models.Index(fields=['location_id', 'status']),
        ]

    @property
    def total_stock(self):
        return self.quantity_available + self.reserved_quantity

    def sync_status(self):
        if self.quantity_available <= 0:
            self.status = self.STATUS_OUT_OF_STOCK
        elif self.quantity_available <= self.low_stock_threshold:
            self.status = self.STATUS_LOW_STOCK
        else:
            self.status = self.STATUS_IN_STOCK

    def save(self, *args, **kwargs):
        self.sync_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} @ {self.location_id} (Avail: {self.quantity_available}, Reserved: {self.reserved_quantity}, Price: ₹{self.price})"
