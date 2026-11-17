from rest_framework import serializers
from .models import MembershipPlan, CustomerMembership


class MembershipPlanSerializer(serializers.ModelSerializer):
    free_delivery_threshold = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = MembershipPlan
        fields = [
            'id',
            'name',
            'description',
            'price',
            'duration_days',
            'benefit_rules',
            'free_delivery_threshold',
            'discount_percentage',
            'is_active',
        ]


class CustomerMembershipSerializer(serializers.ModelSerializer):
    plan = MembershipPlanSerializer(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = CustomerMembership
        fields = [
            'id',
            'plan',
            'start_date',
            'end_date',
            'status',
            'auto_renew',
            'days_remaining',
            'is_valid',
            'created_at',
        ]


class SubscribeMembershipSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField(required=True)


class MembershipStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
    plan = MembershipPlanSerializer(allow_null=True)
    start_date = serializers.CharField(allow_null=True)
    end_date = serializers.CharField(allow_null=True)
    days_remaining = serializers.IntegerField()
    total_savings = serializers.FloatField()
