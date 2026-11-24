from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, time
from decimal import Decimal

from apps.accounts.models import User
from apps.memberships.models import MembershipPlan
from apps.products.models import Category, Product
from apps.inventory.models import Inventory
from apps.delivery.models import DeliveryZone, DeliverySlot, DeliveryFeeRule


class Command(BaseCommand):
    help = 'Seeds initial Fastora categories, products, inventory, zones, slots, fee rules, and admin'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Fastora data...")

        # 1. Admin Superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@fastora.local',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user (admin / admin123)"))

        # 2. Categories
        categories_data = [
            {'name': 'Groceries & Kitchen', 'slug': 'groceries', 'icon': '🛒', 'desc': 'Daily grocery essentials, staples, dairy & kitchen supplies'},
            {'name': 'Fruits & Vegetables', 'slug': 'fruits', 'icon': '🍎', 'desc': 'Fresh farm-picked fruits and green vegetables'},
            {'name': 'Meat & Seafood', 'slug': 'meat', 'icon': '🍗', 'desc': 'Fresh cut chicken, mutton, fish and prawns'},
            {'name': 'Pharmacy & Wellness', 'slug': 'pharmacy', 'icon': '💊', 'desc': 'Over the counter medicines, supplements and first aid'},
            {'name': 'Electronics & Gadgets', 'slug': 'electronics', 'icon': '🎧', 'desc': 'Headphones, cables, power banks and accessories'},
            {'name': 'Beauty & Personal Care', 'slug': 'beauty', 'icon': '🧴', 'desc': 'Skincare, haircare, cosmetics and hygiene'},
            {'name': 'Baby & Kids', 'slug': 'kids', 'icon': '🧸', 'desc': 'Baby diapers, kids toys, food and stationery'},
            {'name': 'Gifts & Flowers', 'slug': 'gifting', 'icon': '🎁', 'desc': 'Chocolates, gift hampers, bouquets and greetings'},
        ]

        cat_objs = {}
        for c in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=c['slug'],
                defaults={'name': c['name'], 'icon': c['icon'], 'description': c['desc']}
            )
            cat_objs[c['slug']] = cat

        # 3. Products & Inventory
        products_data = [
            # Groceries
            {'cat': 'groceries', 'name': 'Amul Taaza Homogenised Toned Milk', 'unit': '1 L', 'price': 54.00, 'disc': 52.00, 'qty': 50},
            {'cat': 'groceries', 'name': 'Aashirvaad Superior MP Sharbati Atta', 'unit': '5 Kg', 'price': 285.00, 'disc': 260.00, 'qty': 30},
            {'cat': 'groceries', 'name': 'Tata Salt Vacuum Evaporated Iodised', 'unit': '1 Kg', 'price': 28.00, 'disc': 26.00, 'qty': 100},
            {'cat': 'groceries', 'name': 'Fortune Sunlite Refined Sunflower Oil', 'unit': '1 L', 'price': 145.00, 'disc': 135.00, 'qty': 40},
            {'cat': 'groceries', 'name': 'Amul Butter - Pasteurised', 'unit': '500 g', 'price': 275.00, 'disc': 265.00, 'qty': 35},
            {'cat': 'groceries', 'name': 'Brown Bread Multi-Grain', 'unit': '400 g', 'price': 55.00, 'disc': 50.00, 'qty': 25},

            # Fruits & Vegetables
            {'cat': 'fruits', 'name': 'Fresh Royal Gala Apples', 'unit': '1 Kg (approx 4-5 pcs)', 'price': 180.00, 'disc': 165.00, 'qty': 45},
            {'cat': 'fruits', 'name': 'Robusta Fresh Bananas', 'unit': '1 Dozen (12 pcs)', 'price': 60.00, 'disc': 50.00, 'qty': 60},
            {'cat': 'fruits', 'name': 'Hybrid Red Tomatoes', 'unit': '1 Kg', 'price': 40.00, 'disc': 35.00, 'qty': 80},
            {'cat': 'fruits', 'name': 'New Crop Fresh Potatoes', 'unit': '1 Kg', 'price': 35.00, 'disc': 30.00, 'qty': 100},
            {'cat': 'fruits', 'name': 'Fresh Red Onions', 'unit': '1 Kg', 'price': 45.00, 'disc': 40.00, 'qty': 90},

            # Pharmacy
            {'cat': 'pharmacy', 'name': 'Dolo 650 Paracetamol Tablets', 'unit': '15 Tablets Strip', 'price': 34.00, 'disc': 30.00, 'qty': 70},
            {'cat': 'pharmacy', 'name': 'Dettol Antiseptic Liquid', 'unit': '250 ml', 'price': 135.00, 'disc': 125.00, 'qty': 30},
            {'cat': 'pharmacy', 'name': 'Band-Aid Spot Adhesive Bandages', 'unit': '20 Strips Pack', 'price': 50.00, 'disc': 45.00, 'qty': 50},

            # Electronics
            {'cat': 'electronics', 'name': 'boAt Bassheads 100 Wired Earphones', 'unit': '1 Unit', 'price': 399.00, 'disc': 349.00, 'qty': 20},
            {'cat': 'electronics', 'name': 'Fastora Type-C Braided Cable 65W', 'unit': '1.2 Meter', 'price': 199.00, 'disc': 149.00, 'qty': 40},

            # Beauty
            {'cat': 'beauty', 'name': 'Himalaya Purifying Neem Face Wash', 'unit': '150 ml', 'price': 165.00, 'disc': 145.00, 'qty': 35},
            {'cat': 'beauty', 'name': 'Dove Deep Moisture Body Wash', 'unit': '200 ml', 'price': 190.00, 'disc': 170.00, 'qty': 25},

            # Kids
            {'cat': 'kids', 'name': 'Pampers All Round Protection Diapers M', 'unit': '32 Pants', 'price': 499.00, 'disc': 449.00, 'qty': 15},
            {'cat': 'kids', 'name': 'Faber-Castell Wax Crayons', 'unit': '24 Shades Pack', 'price': 90.00, 'disc': 80.00, 'qty': 30},

            # Gifting
            {'cat': 'gifting', 'name': 'Cadbury Celebrations Rich Dry Fruit Box', 'unit': '177 g Box', 'price': 250.00, 'disc': 225.00, 'qty': 25},
        ]

        for p in products_data:
            cat = cat_objs[p['cat']]
            prod, _ = Product.objects.get_or_create(
                name=p['name'],
                defaults={
                    'category': cat,
                    'unit': p['unit'],
                    'description': f"Premium quality {p['name']} delivered fresh to your doorstep.",
                }
            )
            # Create or update Inventory
            inv, _ = Inventory.objects.update_or_create(
                product=prod,
                defaults={
                    'location_id': 'DARK_STORE_01',
                    'quantity_available': p['qty'],
                    'reserved_quantity': 0,
                    'price': Decimal(str(p['disc'] if p.get('disc') else p['price'])),
                    'status': Inventory.STATUS_IN_STOCK,
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(products_data)} products and inventory records."))

        # 4. Delivery Zones in Pune
        pune_zones_data = [
            {
                'name': 'Pune West - Kothrud & Deccan Hub',
                'postal_codes': ['411038', '411004', '411052', '411058', '411029', '411005'],
                'center_lat': Decimal('18.507400'),
                'center_lng': Decimal('73.807700'),
                'radius_km': Decimal('6.00'),
            },
            {
                'name': 'Pune East - Viman Nagar & Kharadi Hub',
                'postal_codes': ['411014', '411006', '411032', '411011'],
                'center_lat': Decimal('18.567900'),
                'center_lng': Decimal('73.914300'),
                'radius_km': Decimal('6.00'),
            },
            {
                'name': 'Pune North-West - Baner & Wakad Hub',
                'postal_codes': ['411045', '411057', '411033', '411027'],
                'center_lat': Decimal('18.559000'),
                'center_lng': Decimal('73.786800'),
                'radius_km': Decimal('7.00'),
            },
        ]

        active_zones = []
        for zd in pune_zones_data:
            z, _ = DeliveryZone.objects.update_or_create(
                name=zd['name'],
                defaults={
                    'postal_codes': zd['postal_codes'],
                    'center_lat': zd['center_lat'],
                    'center_lng': zd['center_lng'],
                    'radius_km': zd['radius_km'],
                    'is_active': True
                }
            )
            active_zones.append(z)
            self.stdout.write(self.style.SUCCESS(f"Delivery Zone ready: {z.name}"))

        # Clean up legacy non-Pune zones
        DeliveryZone.objects.exclude(name__startswith='Pune').delete()

        # 5. Delivery Slots (Today & Tomorrow for all Pune Zones)
        today = timezone.localdate()
        # Close past date slots
        DeliverySlot.objects.filter(date__lt=today).update(status=DeliverySlot.STATUS_CLOSED)
        for zone in active_zones:
            for day_offset in [0, 1]:
                slot_date = today + timedelta(days=day_offset)
                for start_hour in range(7, 22):
                    start_t = time(start_hour, 0)
                    end_t = time(start_hour + 1, 0)
                    slot_start_dt = timezone.make_aware(
                        timezone.datetime.combine(slot_date, start_t),
                        timezone.get_current_timezone()
                    )
                    cutoff_dt = slot_start_dt - timedelta(minutes=15)
                    DeliverySlot.objects.get_or_create(
                        zone=zone,
                        date=slot_date,
                        start_time=start_t,
                        end_time=end_t,
                        defaults={
                            'max_capacity': 15,
                            'current_bookings': 0,
                            'cutoff_time': cutoff_dt,
                            'status': DeliverySlot.STATUS_OPEN
                        }
                    )

            # 6. Delivery Fee Rules (Express vs Scheduled Pooled)
            DeliveryFeeRule.objects.update_or_create(
                zone=zone,
                delivery_option=DeliveryFeeRule.OPTION_EXPRESS,
                defaults={
                    'base_fee': Decimal('35.00'),
                    'min_order_for_discount': Decimal('499.00'),
                    'per_km_fee': Decimal('6.00'),
                    'pooled_discount_amount': Decimal('0.00'),
                    'is_active': True
                }
            )
            DeliveryFeeRule.objects.update_or_create(
                zone=zone,
                delivery_option=DeliveryFeeRule.OPTION_SCHEDULED_POOLED,
                defaults={
                    'base_fee': Decimal('25.00'),
                    'min_order_for_discount': Decimal('349.00'),
                    'per_km_fee': Decimal('3.00'),
                    'pooled_discount_amount': Decimal('15.00'),
                    'is_active': True
                }
            )

        self.stdout.write(self.style.SUCCESS("Configured Slots and Smart Fee Rules for Pune Hubs."))
        self.stdout.write(self.style.SUCCESS("Configured Smart Delivery Fee Rules (Express + Pooled)."))

        # 7. Membership Plan (SRS Section 3.4.5)
        MembershipPlan.objects.update_or_create(
            name='Fastora Plus Pass',
            defaults={
                'description': 'Enjoy free delivery on small & large orders, exclusive pooling priority, and special discounts!',
                'price': Decimal('99.00'),
                'duration_days': 30,
                'benefit_rules': {
                    'waive_delivery_fee': True,
                    'free_delivery_min_order': 0.00,
                    'delivery_discount_pct': 100.00,
                    'priority_slots': True,
                },
                'is_active': True
            }
        )
        self.stdout.write(self.style.SUCCESS("Created Fastora Plus Membership Plan."))
        self.stdout.write(self.style.SUCCESS("All Fastora seed data created successfully!"))

