from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class MembershipPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    benefit_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuration rules for discounts and delivery fee waivers"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price']

    @property
    def free_delivery_threshold(self):
        val = self.benefit_rules.get('free_delivery_min_order', 0.00)
        return Decimal(str(val))

    @property
    def discount_percentage(self):
        val = self.benefit_rules.get('delivery_discount_pct', 100.00)
        return Decimal(str(val))

    @property
    def waives_delivery(self):
        return bool(self.benefit_rules.get('waive_delivery_fee', True))

    def __str__(self):
        return f"{self.name} (Rs. {self.price}/{self.duration_days} days)"


class CustomerMembership(models.Model):
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_CANCELLED = 'CANCELLED'

    ACTIVE = STATUS_ACTIVE
    EXPIRED = STATUS_EXPIRED
    CANCELLED = STATUS_CANCELLED

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    auto_renew = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=120, blank=True, null=True, help_text="Payment transaction reference")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        return (
            str(self.status).upper() in [self.STATUS_ACTIVE, 'ACTIVE']
            and self.end_date >= timezone.now()
        )

    def days_remaining(self):
        if not self.is_valid():
            return 0
        diff = self.end_date - timezone.now()
        return max(0, diff.days)

    def __str__(self):
        return f"{self.customer.username} - {self.plan.name} ({self.status})"
