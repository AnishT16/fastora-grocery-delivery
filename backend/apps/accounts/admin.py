from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, CustomerProfile, Address


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Fastora Role & Details', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Fastora Role & Details', {'fields': ('role', 'phone')}),
    )
    inlines = [CustomerProfileInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'street_address', 'city', 'postal_code', 'delivery_zone', 'is_default')
    list_filter = ('city', 'delivery_zone', 'is_default')
    search_fields = ('street_address', 'postal_code', 'customer__username')
