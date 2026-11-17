from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Cart(models.Model):
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())

    def clear(self):
        self.items.all().delete()

    def __str__(self):
        user_label = self.customer.username if self.customer else f"Session: {self.session_key}"
        return f"Cart ({user_label}) - {self.total_items} items"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'product')
        ordering = ['id']

    def save(self, *args, **kwargs):
        if not self.unit_price_snapshot or self.unit_price_snapshot == Decimal('0.00'):
            product_price = getattr(self.product, 'current_price', None) or getattr(self.product, 'price', None)
            if product_price is not None:
                self.unit_price_snapshot = product_price
        super().save(*args, **kwargs)

    @property
    def total_price(self):
        return (self.unit_price_snapshot or Decimal('0.00')) * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name} @ ₹{self.unit_price_snapshot}"
