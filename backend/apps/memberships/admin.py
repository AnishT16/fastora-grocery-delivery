from django.contrib import admin
from .models import MembershipPlan, CustomerMembership


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'free_delivery_threshold', 'discount_percentage', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(CustomerMembership)
class CustomerMembershipAdmin(admin.ModelAdmin):
    list_display = ('customer', 'plan', 'start_date', 'end_date', 'status', 'auto_renew')
    list_filter = ('status', 'plan')
    search_fields = ('customer__username', 'customer__email')
