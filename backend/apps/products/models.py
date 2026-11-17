from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True, help_text="Category icon or emoji")
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    unit = models.CharField(
        max_length=50,
        default='1 unit',
        help_text="Pack size or unit measurement (e.g. 1 Kg, 500g, 1 L, 12 pcs)"
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def pack_size(self):
        return self.unit

    @property
    def price(self):
        if hasattr(self, 'inventory') and self.inventory:
            return self.inventory.price
        return None

    @property
    def current_price(self):
        return self.price

    @property
    def quantity_available(self):
        if hasattr(self, 'inventory') and self.inventory:
            return self.inventory.quantity_available
        return 0

    @property
    def stock_status(self):
        if hasattr(self, 'inventory') and self.inventory:
            return self.inventory.status
        return 'OUT_OF_STOCK'

    def __str__(self):
        return f"{self.name} ({self.unit})"
