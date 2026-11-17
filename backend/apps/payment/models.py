from decimal import Decimal

from django.db import models
from django.utils import timezone


class PaymentConfig(models.Model):
    is_cod_enabled_globally = models.BooleanField(
        default=True,
        help_text="Enable or disable Cash on Delivery across all zones."
    )
    disabled_cod_zones = models.ManyToManyField(
        'delivery.DeliveryZone',
        blank=True,
        related_name='disabled_cod_configs',
        help_text="Specific zones where Cash on Delivery is disabled."
    )
    min_order_for_cod = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Minimum basket subtotal required for Cash on Delivery."
    )
    max_order_for_cod = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('5000.00'),
        help_text="Maximum allowed order value for Cash on Delivery."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment Configuration"
        verbose_name_plural = "Payment Configurations"

    @classmethod
    def get_config(cls):
        config = cls.objects.first()
        if not config:
            config = cls.objects.create(is_cod_enabled_globally=True)
        return config

    def is_cod_allowed_for(self, zone=None, subtotal=None):
        if not self.is_cod_enabled_globally:
            return False, "Cash on Delivery (COD) is currently disabled."

        if zone and self.disabled_cod_zones.filter(id=zone.id).exists():
            return False, f"Cash on Delivery is currently disabled in '{zone.name}'."

        if subtotal is not None:
            sub = Decimal(str(subtotal))
            if self.min_order_for_cod > Decimal('0.00') and sub < self.min_order_for_cod:
                return False, f"Minimum order subtotal of Rs. {self.min_order_for_cod} required for COD."
            if self.max_order_for_cod > Decimal('0.00') and sub > self.max_order_for_cod:
                return False, f"Cash on Delivery is only available for orders up to Rs. {self.max_order_for_cod}."

        return True, ""

    def __str__(self):
        status_str = "ENABLED" if self.is_cod_enabled_globally else "DISABLED"
        return f"Payment Config (COD Global: {status_str}, Disabled Zones: {self.disabled_cod_zones.count()})"


class Payment(models.Model):
    METHOD_COD = 'COD'
    METHOD_ONLINE = 'ONLINE'

    METHOD_CHOICES = [
        (METHOD_COD, 'Cash on Delivery (COD)'),
        (METHOD_ONLINE, 'Online Payment (UPI/Cards/Netbanking)'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_COD_PENDING = 'COD_PENDING'
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'
    STATUS_REFUNDED = 'REFUNDED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Online Verification'),
        (STATUS_COD_PENDING, 'Cash Collection Pending (COD)'),
        (STATUS_SUCCESS, 'Successful'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=METHOD_COD)
    transaction_reference = models.CharField(max_length=120, blank=True, null=True, unique=True)
    refund_reference = models.CharField(max_length=120, blank=True, null=True, help_text="Gateway refund reference")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Total amount refunded")
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    gateway_response = models.JSONField(default=dict, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of cash collection for COD")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def mark_success(self, ref=None, raw_response=None):
        self.status = self.STATUS_SUCCESS
        if ref:
            self.transaction_reference = ref
        if raw_response:
            self.gateway_response = raw_response
        self.save(update_fields=['status', 'transaction_reference', 'gateway_response', 'updated_at'])

        from apps.orders.models import Order
        if self.order.status in [Order.STATUS_PENDING_PAYMENT, 'pending']:
            self.order.status = Order.STATUS_CONFIRMED
            self.order.save(update_fields=['status', 'updated_at'])

    def mark_failed(self, error_details=None):
        self.status = self.STATUS_FAILED
        if error_details:
            self.gateway_response = error_details
        self.save(update_fields=['status', 'gateway_response', 'updated_at'])

    def mark_cod_collected(self, collected_by=None):
        self.status = self.STATUS_SUCCESS
        self.collected_at = timezone.now()
        if collected_by:
            self.gateway_response['collected_by'] = str(collected_by)
        self.save(update_fields=['status', 'collected_at', 'gateway_response', 'updated_at'])

    def mark_refunded(self, refund_ref=None, refund_amount=None, reason=None):
        self.status = self.STATUS_REFUNDED
        if refund_ref:
            self.refund_reference = refund_ref
        self.refund_amount = refund_amount if refund_amount is not None else self.amount
        if reason:
            self.gateway_response['refund_reason'] = str(reason)
            self.gateway_response['refunded_at'] = timezone.now().isoformat()
        self.save(update_fields=['status', 'refund_reference', 'refund_amount', 'gateway_response', 'updated_at'])

        from apps.orders.models import Order
        if self.order.status != Order.STATUS_CANCELLED:
            self.order.status = Order.STATUS_CANCELLED
            self.order.cancellation_reason = reason or "Order refunded and cancelled."
            self.order.save(update_fields=['status', 'cancellation_reason', 'updated_at'])

    def __str__(self):
        return f"Payment #{self.id} for Order #{self.order.id} - Rs. {self.amount} ({self.get_status_display()})"
