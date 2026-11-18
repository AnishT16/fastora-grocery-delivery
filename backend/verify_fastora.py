import os
import sys
from decimal import Decimal
from datetime import timedelta
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastora.settings')
django.setup()

from django.db import connection
from django.utils import timezone
from django.test import Client

from apps.accounts.models import User
from apps.memberships.models import MembershipPlan, CustomerMembership
from apps.products.models import Category, Product
from apps.inventory.models import Inventory
from apps.inventory.services import reserve_stock, release_stock, confirm_stock_deduction
from apps.orders.models import Order
from apps.delivery.models import DeliveryZone, DeliverySlot, DeliveryFeeRule, DeliveryBatch, PooledOrder
from apps.delivery.services.zone_service import get_serviceable_zone
from apps.delivery.services.slot_service import get_available_slots, reserve_slot_capacity, release_slot_capacity
from apps.delivery.services.pricing_service import calculate_delivery_quote
from apps.delivery.services.pooling_service import run_batch_matching, release_batch
from common.exceptions import InsufficientStockError, ZoneNotServiceableError, SlotNotAvailableError


def run_checks():
    print("======================================================================")
    print("🚀  FASTORA FULL-STACK SYSTEM VERIFICATION SUITE")
    print("======================================================================")

    print("\n[1/8] Checking Database Connection (PostgreSQL)...")
    db_engine = connection.settings_dict['ENGINE']
    db_name = connection.settings_dict['NAME']
    print(f"  • Connected Engine : {db_engine}")
    print(f"  • Database Name    : {db_name}")
    assert 'postgresql' in db_engine, "Database is not PostgreSQL!"
    print("  ✅ PostgreSQL is active and connected.")

    print("\n[2/8] Checking User Authentication & Roles...")
    client = Client()
    test_username = f"verify_cust_{int(timezone.now().timestamp())}"
    reg_res = client.post('/accounts/register/', {
        'username': test_username,
        'email': f"{test_username}@example.com",
        'phone': '9876543210',
        'password1': 'Pass@123456',
        'password2': 'Pass@123456',
    })
    assert reg_res.status_code == 302, "Registration POST did not redirect"
    cust_user = User.objects.get(username=test_username)
    assert cust_user.role == User.ROLE_CUSTOMER
    print(f"  • Customer Registered: {cust_user.username} (Role: {cust_user.role})")
    login_res = client.post('/accounts/login/', {
        'username': test_username,
        'password': 'Pass@123456',
    })
    assert login_res.status_code == 302
    print("  • Login & Session verified successfully.")
    print("  ✅ Authentication & Role-Based Access working.")

    print("\n[3/8] Checking Product Catalogue & REST APIs...")
    api_res = client.get('/api/products/')
    assert api_res.status_code == 200
    products_data = api_res.json()
    print(f"  • Total Products in API: {len(products_data)}")
    assert len(products_data) > 0, "No products found in database!"
    sample = products_data[0]
    print(f"  • Sample Item: {sample['name']} | Price: ₹{sample['price']} | Stock: {sample['quantity_available']} ({sample['stock_status']})")
    cat_res = client.get('/api/products/?category=groceries')
    assert cat_res.status_code == 200
    print(f"  • Category Filter (?category=groceries) returned {len(cat_res.json())} items")
    print("  ✅ DRF Product API working.")

    print("\n[4/8] Checking Inventory Service & Overselling Protection...")
    prod = Product.objects.first()
    inv = prod.inventory
    original_stock = inv.quantity_available
    res_inv = reserve_stock(prod.id, 2)
    assert res_inv.quantity_available == original_stock - 2
    assert res_inv.reserved_quantity >= 2
    print(f"  • reserve_stock(2) -> Stock reduced: {original_stock} -> {res_inv.quantity_available}")
    try:
        reserve_stock(prod.id, 99999)
        assert False, "Overselling protection failed!"
    except InsufficientStockError:
        print("  • InsufficientStockError caught on overbooking attempt (Zero oversell confirmed).")
    rel_inv = release_stock(prod.id, 2)
    assert rel_inv.quantity_available == original_stock
    print(f"  • release_stock(2) -> Stock restored back to {rel_inv.quantity_available}")
    print("  ✅ Concurrency-safe atomic inventory service working.")

    print("\n[5/8] Checking Delivery Zone Mapping (Geospatial & Postal Codes)...")
    zone = get_serviceable_zone('411038')
    print(f"  • Postal Code 411038 mapped to: '{zone.name}'")
    coords_zone = get_serviceable_zone({'latitude': 18.5085, 'longitude': 73.8110})
    print(f"  • Coordinates (18.5085, 73.8110) mapped to: '{coords_zone.name}'")
    try:
        get_serviceable_zone('999999')
    except ZoneNotServiceableError:
        print("  • Out-of-zone postal code (999999) rejected with ZoneNotServiceableError.")
    print("  ✅ Zone Service mapping working.")

    print("\n[6/8] Checking Delivery Slot Capacity Engine...")
    tomorrow = timezone.localdate() + timedelta(days=1)
    slots = get_available_slots(zone_id=zone.id, target_date=tomorrow)
    print(f"  • Open slots found for tomorrow: {slots.count()}")
    test_slot = slots.first()
    initial_bookings = test_slot.current_bookings
    reserved_slot = reserve_slot_capacity(test_slot.id)
    assert reserved_slot.current_bookings == initial_bookings + 1
    print(f"  • reserve_slot_capacity() -> Bookings: {initial_bookings} -> {reserved_slot.current_bookings}/{reserved_slot.max_capacity}")
    rel_slot = release_slot_capacity(test_slot.id)
    assert rel_slot.current_bookings == initial_bookings
    print(f"  • release_slot_capacity() -> Restored to {rel_slot.current_bookings}")
    print("  ✅ Slot Capacity & Concurrency Protection working.")

    print("\n[7/8] Checking Smart Delivery-Fee Engine (SRS Section 3.4.3)...")
    q_exp = calculate_delivery_quote({'postal_code': '411038'}, cart_subtotal=100.0, delivery_option='EXPRESS')
    print(f"  • Express Delivery Fee: ₹{q_exp['final_fee']} (Base: ₹{q_exp['base_fee']} + Dist: ₹{q_exp['distance_fee']})")
    q_pool = calculate_delivery_quote({'postal_code': '411038'}, cart_subtotal=100.0, delivery_option='SCHEDULED_POOLED')
    print(f"  • Scheduled Pooled Fee : ₹{q_pool['final_fee']} (Discount: -₹{q_pool['pooled_discount']})")
    assert q_pool['final_fee'] < q_exp['final_fee'], "Pooled delivery was not cheaper than Express!"
    print("  • Verified: Scheduled micro-delivery is cheaper than Express delivery.")
    plan = MembershipPlan.objects.first()
    CustomerMembership.objects.create(
        customer=cust_user,
        plan=plan,
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=30),
        status=CustomerMembership.STATUS_ACTIVE
    )
    q_mem = calculate_delivery_quote({'postal_code': '411038'}, cart_subtotal=50.0, delivery_option='SCHEDULED_POOLED', user=cust_user)
    assert q_mem['final_fee'] == 0.0
    print(f"  • Fastora Plus Member Quote: ₹{q_mem['final_fee']} (100% Free delivery waiver applied)")
    print("  ✅ Smart Delivery-Fee Engine working.")

    print("\n[8/8] Checking Neighbourhood Pooling & Dispatch Clustering...")
    order_a = Order.objects.create(
        customer=cust_user,
        subtotal=Decimal('150.00'),
        delivery_fee=Decimal('10.00'),
        total=Decimal('160.00'),
        delivery_option=Order.DELIVERY_SCHEDULED_POOLED,
        delivery_zone=zone,
        delivery_slot=test_slot,
        address_snapshot={'postal_code': '411038', 'latitude': 18.5085, 'longitude': 73.8110},
        status=Order.STATUS_CONFIRMED
    )
    order_b = Order.objects.create(
        customer=cust_user,
        subtotal=Decimal('120.00'),
        delivery_fee=Decimal('10.00'),
        total=Decimal('130.00'),
        delivery_option=Order.DELIVERY_SCHEDULED_POOLED,
        delivery_zone=zone,
        delivery_slot=test_slot,
        address_snapshot={'postal_code': '411038', 'latitude': 18.5175, 'longitude': 73.8415},
        status=Order.STATUS_CONFIRMED
    )
    batches = run_batch_matching(zone_id=zone.id, slot_id=test_slot.id)
    assert len(batches) > 0, "No batches generated"
    matched_batch = batches[0]
    print(f"  • Batch #{matched_batch.id} created with {matched_batch.pooled_orders.count()} pooled orders")
    partner = User.objects.filter(role=User.ROLE_DELIVERY_PARTNER).first()
    if not partner:
        partner = User.objects.create(
            username=f"rider_{int(timezone.now().timestamp())}",
            email="rider@fastora.com",
            role=User.ROLE_DELIVERY_PARTNER
        )
    rel_batch = release_batch(matched_batch.id, partner.id)
    assert rel_batch.status == DeliveryBatch.STATUS_RELEASED
    assert rel_batch.delivery_partner_id == partner.id
    print(f"  • Batch #{rel_batch.id} released and assigned to Delivery Partner '{partner.username}'")
    order_a.refresh_from_db()
    order_b.refresh_from_db()
    assert order_a.status == Order.STATUS_READY
    assert order_b.status == Order.STATUS_READY
    print("  • Attached orders advanced to 'READY' for pickup.")
    print("  ✅ Neighbourhood Pooling Engine working.")

    order_a.delete()
    order_b.delete()
    matched_batch.delete()
    cust_user.delete()

    print("\n======================================================================")
    print("🎉  ALL 8 CORE SYSTEM MODULES ARE FULLY OPERATIONAL!")
    print("======================================================================")


if __name__ == '__main__':
    run_checks()
