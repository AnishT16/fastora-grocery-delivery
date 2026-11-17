import math
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class DeliveryZone(models.Model):
    name = models.CharField(max_length=120, unique=True, help_text="e.g. Navrangpura Central Hub")
    postal_codes = models.JSONField(
        default=list,
        help_text="List of serviced postal codes as strings"
    )
    center_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude of zone dark store"
    )
    center_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude of zone dark store"
    )
    radius_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text="Service radius around dark store center in kilometers"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def is_postal_code_serviced(self, postal_code):
        clean = str(postal_code).strip()
        return clean in [str(code).strip() for code in self.postal_codes]

    def calculate_distance_km(self, target_lat, target_lng):
        # Haversine distance from zone center to target coordinates
        if self.center_lat is None or self.center_lng is None:
            return 0.0

        lat1, lon1 = math.radians(float(self.center_lat)), math.radians(float(self.center_lng))
        lat2, lon2 = math.radians(float(target_lat)), math.radians(float(target_lng))

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(6371.0 * c, 2)

    def is_within_radius(self, target_lat, target_lng):
        if self.center_lat is None or self.center_lng is None:
            return True
        return self.calculate_distance_km(target_lat, target_lng) <= float(self.radius_km)

    def __str__(self):
        return f"{self.name} (Codes: {len(self.postal_codes)}, Radius: {self.radius_km}km)"


class DeliverySlot(models.Model):
    STATUS_OPEN = 'OPEN'
    STATUS_FULL = 'FULL'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open for Booking'),
        (STATUS_FULL, 'Fully Booked'),
        (STATUS_CLOSED, 'Closed / Past Cutoff'),
    ]

    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.CASCADE,
        related_name='slots'
    )
    date = models.DateField(default=timezone.localdate)
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_capacity = models.PositiveIntegerField(
        default=15,
        help_text="Maximum pooled orders this time slot can service"
    )
    current_bookings = models.PositiveIntegerField(
        default=0,
        help_text="Number of confirmed orders booked into this slot"
    )
    cutoff_time = models.DateTimeField(
        help_text="Timestamp after which new reservations for this slot are blocked"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN
    )

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ('zone', 'date', 'start_time', 'end_time')

    @property
    def is_available(self):
        return (
            self.status == self.STATUS_OPEN
            and self.current_bookings < self.max_capacity
            and timezone.now() < self.cutoff_time
        )

    def sync_status(self):
        now = timezone.now()
        if now >= self.cutoff_time:
            self.status = self.STATUS_CLOSED
        elif self.current_bookings >= self.max_capacity:
            self.status = self.STATUS_FULL
        else:
            self.status = self.STATUS_OPEN

    def save(self, *args, **kwargs):
        self.sync_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.zone.name} | {self.date} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} [{self.current_bookings}/{self.max_capacity}] ({self.status})"


class DeliveryFeeRule(models.Model):
    OPTION_EXPRESS = 'EXPRESS'
    OPTION_SCHEDULED_POOLED = 'SCHEDULED_POOLED'

    OPTION_CHOICES = [
        (OPTION_EXPRESS, 'Express Delivery (15-20 min)'),
        (OPTION_SCHEDULED_POOLED, 'Scheduled Micro-Delivery (Neighbourhood Pooled)'),
    ]

    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.CASCADE,
        related_name='fee_rules',
        null=True,
        blank=True,
        help_text="Target zone. Leave empty for global fallback rule."
    )
    delivery_option = models.CharField(max_length=20, choices=OPTION_CHOICES)
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('30.00'))
    per_km_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('5.00'))
    min_order_for_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('500.00'),
        help_text="Order subtotal threshold to qualify for free or subsidized delivery"
    )
    pooled_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('20.00'),
        help_text="Subsidy discount applied when customer chooses scheduled micro-delivery"
    )
    active_from = models.DateTimeField(null=True, blank=True)
    active_to = models.DateTimeField(null=True, blank=True)
    rule_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configurable fee parameters"
    )
    is_active = models.BooleanField(default=True)

    def calculate_quote(self, order_subtotal, distance_km=2.0, has_membership=False):
        subtotal_dec = Decimal(str(order_subtotal))
        dist_dec = Decimal(str(distance_km))

        if has_membership or (self.min_order_for_discount and subtotal_dec >= self.min_order_for_discount):
            return {
                'base_fee': float(self.base_fee),
                'distance_fee': float(dist_dec * self.per_km_fee),
                'discount': float(self.base_fee + (dist_dec * self.per_km_fee)),
                'final_fee': 0.00,
                'is_free': True,
                'rule_id': self.id,
            }

        nominal_fee = self.base_fee + (dist_dec * self.per_km_fee)
        discount = Decimal('0.00')

        if self.delivery_option == self.OPTION_SCHEDULED_POOLED:
            discount = min(self.pooled_discount_amount, nominal_fee)
            final_fee = max(Decimal('10.00'), nominal_fee - discount)
        else:
            final_fee = max(Decimal('20.00'), nominal_fee)

        return {
            'base_fee': float(self.base_fee),
            'distance_fee': float(dist_dec * self.per_km_fee),
            'discount': float(discount),
            'final_fee': float(final_fee),
            'is_free': False,
            'rule_id': self.id,
        }

    def __str__(self):
        zone_label = self.zone.name if self.zone else 'Global'
        return f"{zone_label} - {self.get_delivery_option_display()} (Base: Rs. {self.base_fee})"


class DeliveryBatch(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_RELEASED = 'RELEASED'
    STATUS_IN_TRANSIT = 'IN_TRANSIT'
    STATUS_COMPLETED = 'COMPLETED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft (Accumulating Orders)'),
        (STATUS_RELEASED, 'Released for Pickup'),
        (STATUS_IN_TRANSIT, 'Out for Delivery'),
        (STATUS_COMPLETED, 'Batch Completed'),
    ]

    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.PROTECT,
        related_name='batches'
    )
    slot = models.ForeignKey(
        DeliverySlot,
        on_delete=models.PROTECT,
        related_name='batches'
    )
    delivery_partner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_batches',
        limit_choices_to={'role': 'delivery_partner'}
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )
    max_orders = models.PositiveIntegerField(
        default=15,
        help_text="Maximum orders combined into this single partner route"
    )
    released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Delivery Batches'

    @property
    def order_count(self):
        return self.pooled_orders.count()

    def release_batch(self, partner=None):
        self.status = self.STATUS_RELEASED
        if partner:
            self.delivery_partner = partner
        self.released_at = timezone.now()
        self.save(update_fields=['status', 'delivery_partner', 'released_at', 'updated_at'])

    def __str__(self):
        return f"Batch #{self.id} | {self.zone.name} | Slot: {self.slot.start_time.strftime('%H:%M')}-{self.slot.end_time.strftime('%H:%M')} [{self.status}]"


class PooledOrder(models.Model):
    STATUS_QUEUED = 'QUEUED'
    STATUS_PICKED_UP = 'PICKED_UP'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_QUEUED, 'Queued in Batch'),
        (STATUS_PICKED_UP, 'Picked Up by Partner'),
        (STATUS_DELIVERED, 'Delivered to Customer'),
        (STATUS_FAILED, 'Delivery Attempt Failed'),
    ]

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='pooled_order',
        help_text="An order cannot belong to more than one active delivery batch"
    )
    batch = models.ForeignKey(
        DeliveryBatch,
        on_delete=models.CASCADE,
        related_name='pooled_orders'
    )
    sequence = models.PositiveIntegerField(
        default=1,
        help_text="Order drop-off sequence for optimized routing"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_QUEUED
    )
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['batch', 'sequence']

    def __str__(self):
        return f"Order #{self.order_id} in Batch #{self.batch_id} (Stop {self.sequence})"


class DeliveryPartner(models.Model):
    STATUS_AVAILABLE = 'AVAILABLE'
    STATUS_BUSY = 'BUSY'
    STATUS_OFFLINE = 'OFFLINE'

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Available for Deliveries'),
        (STATUS_BUSY, 'On Delivery / Busy'),
        (STATUS_OFFLINE, 'Offline'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delivery_partner_profile'
    )
    availability_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_AVAILABLE
    )
    vehicle_type = models.CharField(max_length=50, default='Bike / Scooter')
    current_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Delivery Partner'
        verbose_name_plural = 'Delivery Partners'

    def __str__(self):
        return f"{self.user.username} ({self.get_availability_status_display()})"


class DeliveryEvent(models.Model):
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='delivery_events')
    batch = models.ForeignKey(DeliveryBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_events')
    status = models.CharField(max_length=50)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Event: Order #{self.order_id} -> {self.status} at {self.timestamp}"
