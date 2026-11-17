from django.db import models
from django.conf import settings
from decimal import Decimal


class Order(models.Model):
    STATUS_PENDING_PAYMENT = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PREPARING = 'packing'
    STATUS_READY_FOR_POOLING = 'ready_for_pickup'
    STATUS_DISPATCHED = 'in_transit'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_PENDING = STATUS_PENDING_PAYMENT
    STATUS_PACKING = STATUS_PREPARING
    STATUS_READY = STATUS_READY_FOR_POOLING
    STATUS_IN_TRANSIT = STATUS_DISPATCHED

    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, 'Pending Payment'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_READY_FOR_POOLING, 'Ready for Dispatch'),
        (STATUS_DISPATCHED, 'In Transit'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    DELIVERY_EXPRESS = 'express'
    DELIVERY_SCHEDULED_POOLED = 'scheduled_pooled'

    OPTION_EXPRESS = DELIVERY_EXPRESS
    OPTION_SCHEDULED_POOLED = DELIVERY_SCHEDULED_POOLED

    DELIVERY_CHOICES = [
        (DELIVERY_EXPRESS, 'Express Delivery (15-20 Mins)'),
        (DELIVERY_SCHEDULED_POOLED, 'Scheduled Micro-Delivery (Neighbourhood Pooled)'),
    ]

    PAYMENT_METHOD_ONLINE = 'ONLINE'
    PAYMENT_METHOD_COD = 'COD'

    METHOD_ONLINE = PAYMENT_METHOD_ONLINE
    METHOD_COD = PAYMENT_METHOD_COD

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_ONLINE, 'Online Payment'),
        (PAYMENT_METHOD_COD, 'Cash on Delivery'),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2)

    delivery_option = models.CharField(max_length=30, choices=DELIVERY_CHOICES, default=DELIVERY_EXPRESS)
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_COD
    )
    delivery_zone = models.ForeignKey('delivery.DeliveryZone', on_delete=models.SET_NULL, null=True, blank=True)
    delivery_slot = models.ForeignKey('delivery.DeliverySlot', on_delete=models.SET_NULL, null=True, blank=True)

    address_snapshot = models.JSONField()
    pricing_rule_snapshot = models.JSONField(default=dict, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    cancellation_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def selected_slot(self):
        return self.delivery_slot

    @selected_slot.setter
    def selected_slot(self, slot):
        self.delivery_slot = slot

    @property
    def is_pooling_eligible(self):
        # check if order can be pooled into a delivery batch
        opt = str(self.delivery_option).lower()
        return (
            (opt == self.DELIVERY_SCHEDULED_POOLED or 'pooled' in opt)
            and self.delivery_zone is not None
            and self.delivery_slot is not None
            and self.status in [self.STATUS_CONFIRMED, self.STATUS_PREPARING, self.STATUS_READY_FOR_POOLING]
            and not hasattr(self, 'pooled_order')
        )

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username} (₹{self.total}) [{self.get_status_display()}]"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    product_name_snapshot = models.CharField(max_length=200)
    unit_snapshot = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.unit_price_snapshot * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product_name_snapshot} in Order #{self.order.id} @ ₹{self.unit_price_snapshot}"
