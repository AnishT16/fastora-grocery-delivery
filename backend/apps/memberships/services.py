from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from common.exceptions import FastoraException
from .models import CustomerMembership, MembershipPlan


class MembershipPlanNotFoundError(FastoraException):
    default_detail = 'The specified membership plan does not exist or is inactive.'
    default_code = 'plan_not_found'


def is_member_active(user):
    # Checks if user has an active, non-expired membership
    if not user or not getattr(user, 'is_authenticated', False):
        return False

    now = timezone.now()
    return CustomerMembership.objects.filter(
        customer=user,
        status__in=[CustomerMembership.STATUS_ACTIVE, 'active', 'ACTIVE'],
        end_date__gte=now
    ).exists()


def get_active_membership(user):
    # Returns active membership record for the user
    if not user or not getattr(user, 'is_authenticated', False):
        return None

    now = timezone.now()
    return CustomerMembership.objects.filter(
        customer=user,
        status__in=[CustomerMembership.STATUS_ACTIVE, 'active', 'ACTIVE'],
        end_date__gte=now
    ).select_related('plan').first()


def apply_membership_benefits(user, cart_subtotal, base_delivery_fee):
    # Applies free or discounted delivery fee if user has an active membership
    fee = Decimal(str(base_delivery_fee))
    subtotal = Decimal(str(cart_subtotal))

    if not is_member_active(user):
        return fee

    membership = get_active_membership(user)
    if not membership or not membership.plan:
        return fee

    rules = membership.plan.benefit_rules or {}
    waive_fee = rules.get('waive_delivery_fee', True)
    min_order = Decimal(str(rules.get('free_delivery_min_order', '0.00')))
    discount_pct = Decimal(str(rules.get('delivery_discount_pct', '100.00')))

    if waive_fee or subtotal >= min_order:
        if discount_pct >= Decimal('100.00'):
            return Decimal('0.00')
        discount_multiplier = Decimal('1.00') - (discount_pct / Decimal('100.00'))
        discounted = round(fee * discount_multiplier, 2)
        return max(Decimal('0.00'), discounted)

    return fee


def subscribe_user_to_plan(user, plan_id, payment_reference=None):
    # Subscribes user to a membership plan or extends existing subscription
    try:
        plan = MembershipPlan.objects.get(id=plan_id, is_active=True)
    except MembershipPlan.DoesNotExist:
        raise MembershipPlanNotFoundError(f"Membership plan #{plan_id} not found or is inactive.")

    txn_ref = payment_reference or f"MEM_TXN_{user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"

    with transaction.atomic():
        now = timezone.now()
        active_sub = CustomerMembership.objects.filter(
            customer=user,
            status__in=[CustomerMembership.STATUS_ACTIVE, 'active', 'ACTIVE'],
            end_date__gte=now
        ).select_related('plan').first()

        if active_sub:
            new_end_date = active_sub.end_date + timedelta(days=plan.duration_days)
            active_sub.end_date = new_end_date
            active_sub.plan = plan
            active_sub.payment_reference = txn_ref
            active_sub.status = CustomerMembership.STATUS_ACTIVE
            active_sub.save(update_fields=['end_date', 'plan', 'status', 'payment_reference'])
            return active_sub
        else:
            start_date = now
            end_date = now + timedelta(days=plan.duration_days)
            return CustomerMembership.objects.create(
                customer=user,
                plan=plan,
                start_date=start_date,
                end_date=end_date,
                payment_reference=txn_ref,
                status=CustomerMembership.STATUS_ACTIVE
            )


def get_user_membership_status(user):
    # Returns user membership status, remaining days, and total savings
    if not user or not getattr(user, 'is_authenticated', False):
        return {
            'is_active': False,
            'plan': None,
            'start_date': None,
            'end_date': None,
            'days_remaining': 0,
            'total_savings': 0.00,
        }

    membership = get_active_membership(user)
    if not membership:
        return {
            'is_active': False,
            'plan': None,
            'start_date': None,
            'end_date': None,
            'days_remaining': 0,
            'total_savings': 0.00,
        }

    total_savings = Decimal('0.00')
    try:
        from apps.orders.models import Order
        orders = Order.objects.filter(
            customer=user,
            created_at__gte=membership.start_date
        )
        for ord in orders:
            snapshot = ord.pricing_rule_snapshot or {}
            mem_disc = Decimal(str(snapshot.get('membership_discount', 0.00)))
            total_savings += mem_disc
    except Exception:
        pass

    return {
        'is_active': True,
        'plan': {
            'id': membership.plan.id,
            'name': membership.plan.name,
            'description': membership.plan.description,
            'price': float(membership.plan.price),
            'duration_days': membership.plan.duration_days,
            'benefit_rules': membership.plan.benefit_rules,
        },
        'start_date': membership.start_date.isoformat(),
        'end_date': membership.end_date.isoformat(),
        'days_remaining': membership.days_remaining(),
        'total_savings': float(total_savings),
    }
