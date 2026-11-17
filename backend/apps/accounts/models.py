from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    ROLE_CUSTOMER = 'customer'
    ROLE_DISPATCHER = 'dispatcher'
    ROLE_STORE_OPERATOR = 'store_operator'
    ROLE_DELIVERY_PARTNER = 'delivery_partner'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_DISPATCHER, 'Dispatcher / Admin'),
        (ROLE_STORE_OPERATOR, 'Store Operator / Fulfiller'),
        (ROLE_DELIVERY_PARTNER, 'Delivery Partner'),
        (ROLE_ADMIN, 'System Administrator'),
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def is_customer(self):
        return self.role == self.ROLE_CUSTOMER

    def is_delivery_partner(self):
        return self.role == self.ROLE_DELIVERY_PARTNER

    def is_dispatcher(self):
        return self.role in [self.ROLE_DISPATCHER, self.ROLE_ADMIN]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.username}"


class Address(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField(max_length=50, default='Home')
    street_address = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, default='Pune')
    state = models.CharField(max_length=100, default='Maharashtra')
    postal_code = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_zone = models.ForeignKey(
        'delivery.DeliveryZone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='addresses'
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.title} - {self.street_address}, {self.postal_code}"
