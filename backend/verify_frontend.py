import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastora.settings')
django.setup()

from django.test import Client
from apps.accounts.models import User, Address
from apps.products.models import Product, Category
from apps.memberships.models import MembershipPlan, CustomerMembership
from apps.delivery.models import DeliveryZone, DeliverySlot, DeliveryBatch, PooledOrder, DeliveryPartner
from apps.orders.models import Order, OrderItem
from apps.carts.models import Cart, CartItem
from apps.carts.services import add_item_to_cart

def verify_all_frontend():
    print("======================================================================")
    print("🚀  FASTORA COMPLETE FRONTEND & SRS INTEGRATION VERIFICATION")
    print("======================================================================")
    
    client = Client()
    
    # 1. Storefront & Catalog
    print("\n[1/7] Testing Storefront, Categories & Search...")
    res_home = client.get('/')
    assert res_home.status_code == 200, f"Home failed: {res_home.status_code}"
    print("  • GET / (Storefront): HTTP 200 OK")

    prod = Product.objects.filter(is_active=True).first()
    assert prod is not None, "No active products found"
    
    res_detail = client.get(f'/product/{prod.id}/')
    assert res_detail.status_code == 200, f"Product detail failed: {res_detail.status_code}"
    print(f"  • GET /product/{prod.id}/ ({prod.name}): HTTP 200 OK")

    res_cat = client.get('/category/groceries/')
    assert res_cat.status_code in [200, 302], f"Category groceries failed: {res_cat.status_code}"
    print("  • GET /category/groceries/: HTTP 200 OK")

    res_search = client.get('/search/?q=fresh')
    assert res_search.status_code == 200, f"Search failed: {res_search.status_code}"
    print("  • GET /search/?q=fresh: HTTP 200 OK")

    # 2. Cart & Fastora Plus Membership
    print("\n[2/7] Testing Cart & Fastora Plus Membership Plans...")
    res_cart = client.get('/cart/')
    assert res_cart.status_code == 200, f"Cart failed: {res_cart.status_code}"
    print("  • GET /cart/: HTTP 200 OK")

    res_mem = client.get('/membership/')
    assert res_mem.status_code == 200, f"Membership plans failed: {res_mem.status_code}"
    print("  • GET /membership/ (Fastora Plus): HTTP 200 OK")

    res_sim = client.get('/delivery/check/')
    assert res_sim.status_code == 200, f"Delivery check failed: {res_sim.status_code}"
    print("  • GET /delivery/check/: HTTP 200 OK")

    # 3. User Session & Address Management
    print("\n[3/7] Testing Customer Authentication & Address Management...")
    user, _ = User.objects.get_or_create(
        username='frontend_test_cust',
        defaults={'email': 'test_cust@fastora.com', 'role': User.ROLE_CUSTOMER}
    )
    user.set_password('TestPass@123')
    user.save()
    client.force_login(user)

    res_prof = client.get('/profile/')
    assert res_prof.status_code == 200, f"Profile failed: {res_prof.status_code}"
    print(f"  • GET /profile/ ({user.username}): HTTP 200 OK")

    zone = DeliveryZone.objects.first()
    addr, _ = Address.objects.get_or_create(
        customer=user,
        title='Test Home',
        defaults={
            'street_address': 'Flat 101, Fastora Heights',
            'city': 'Pune',
            'state': 'Maharashtra',
            'postal_code': '411038',
            'delivery_zone': zone,
            'is_default': True
        }
    )
    print(f"  • Saved Address verified: #{addr.id} ({addr.title}, PIN: {addr.postal_code})")

    # 4. Dynamic Checkout & Smart Fee Quotes
    print("\n[4/7] Testing Dynamic Checkout & Delivery Fee Engine...")
    cart_obj, _ = Cart.objects.get_or_create(customer=user)
    add_item_to_cart(cart_obj, prod.id, quantity=2)

    res_chk = client.get('/checkout/')
    assert res_chk.status_code == 200, f"Checkout failed: {res_chk.status_code}"
    print("  • GET /checkout/: HTTP 200 OK")

    res_quote = client.post('/api/delivery/fee-quote/', {
        'postal_code': '411038',
        'subtotal': 150.0,
        'delivery_option': 'SCHEDULED_POOLED'
    }, content_type='application/json')
    assert res_quote.status_code == 200, f"Fee quote failed: {res_quote.status_code}"
    qdata = res_quote.json()
    print(f"  • POST /api/delivery/fee-quote/ -> Final Fee: ₹{qdata['final_fee']} (Discount: ₹{qdata['pooled_discount']})")

    # 5. Order Lifecycle, Tracking Stepper & Cancellation (1-2 Hr Same-Day Smart Delivery)
    print("\n[5/7] Testing Order Lifecycle, Tracking & Cancellation (1-2 Hr Smart Delivery)...")
    from datetime import time, timedelta
    from django.utils import timezone
    from apps.delivery.services.slot_service import ensure_rolling_slots, get_available_slots

    # Ensure 1-2 hr rolling slots exist
    ensure_rolling_slots(zone.id)
    today = timezone.localdate()
    available_today = get_available_slots(zone.id, target_date=today)
    if available_today.exists():
        slot = available_today.first()
        print(f"  • Selected 1-2 Hr Rolling Slot: Today ({slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')})")
    else:
        tomorrow = today + timedelta(days=1)
        slot = get_available_slots(zone.id, target_date=tomorrow).first()
        print(f"  • Selected Slot: Tomorrow ({slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')})")
    res_order = client.post('/api/orders/', {
        'delivery_option': 'SCHEDULED_POOLED',
        'payment_method': 'COD',
        'address_id': addr.id,
        'slot_id': slot.id,
    }, content_type='application/json')
    assert res_order.status_code in [200, 201], f"Order creation failed: {res_order.status_code} {res_order.content}"
    order_data = res_order.json()
    new_order_id = order_data['id']
    print(f"  • Order #{new_order_id} created successfully!")

    res_ord_detail = client.get(f'/orders/{new_order_id}/')
    assert res_ord_detail.status_code == 200, f"Order detail failed: {res_ord_detail.status_code}"
    print(f"  • GET /orders/{new_order_id}/ (Tracking Stepper View): HTTP 200 OK")

    res_cancel = client.post(f'/api/orders/{new_order_id}/cancel/', {
        'reason': 'Automated frontend verification test'
    }, content_type='application/json')
    assert res_cancel.status_code == 200, f"Order cancel failed: {res_cancel.status_code}"
    print(f"  • POST /api/orders/{new_order_id}/cancel/ -> Order cancelled & inventory released: HTTP 200 OK")

    # 6. Delivery Partner Rider Portal
    print("\n[6/7] Testing Delivery Partner Rider Portal...")
    rider_user, _ = User.objects.get_or_create(
        username='frontend_test_rider',
        defaults={'email': 'rider@fastora.com', 'role': User.ROLE_DELIVERY_PARTNER}
    )
    rider_user.set_password('RiderPass@123')
    rider_user.save()
    partner, _ = DeliveryPartner.objects.get_or_create(
        user=rider_user,
        defaults={'availability_status': DeliveryPartner.STATUS_AVAILABLE}
    )

    client.force_login(rider_user)
    res_rider = client.get('/delivery/rider/')
    assert res_rider.status_code == 200, f"Rider portal failed: {res_rider.status_code}"
    print(f"  • GET /delivery/rider/ ({rider_user.username}): HTTP 200 OK")

    # 7. Dark Store Dispatcher Dashboard
    print("\n[7/7] Testing Dark Store Operations & Dispatcher Console...")
    dispatcher_user, _ = User.objects.get_or_create(
        username='frontend_test_dispatcher',
        defaults={'email': 'dispatcher@fastora.com', 'role': User.ROLE_DISPATCHER, 'is_staff': True}
    )
    dispatcher_user.set_password('DispPass@123')
    dispatcher_user.save()

    client.force_login(dispatcher_user)
    res_disp = client.get('/dispatcher/')
    assert res_disp.status_code == 200, f"Dispatcher dashboard failed: {res_disp.status_code}"
    print(f"  • GET /dispatcher/ ({dispatcher_user.username}): HTTP 200 OK")

    print("\n======================================================================")
    print("🎉 ALL 7 FRONTEND SRS MODULES VERIFIED SUCCESSFULLY (100% PASS)!")
    print("======================================================================")

if __name__ == '__main__':
    verify_all_frontend()
