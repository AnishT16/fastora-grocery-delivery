# Fastora Project Issues & Task Breakdown (50 Issues)

> **Specification Reference:** Fastora Quick-Commerce Grocery Platform (Django 6.0 / DRF / PostgreSQL)  
> **Methodology:** GSD (Get Shit Done) — Spec-Driven, Low-Coupling, Atomic Tasks  
> **Total Issues:** 50 Issues Across 14 Functional Modules  
> **Dependency Strategy:** Minimal cross-issue dependencies; modular vertical slices  

---

## Executive Summary & Module Matrix

| Module | Module Name | Issue Range | Issue Count | Primary Target Area |
|:---|:---|:---:|:---:|:---|
| **MOD-01** | Core Configuration & Security Hardening | ISSUE-01 to ISSUE-03 | 3 | `fastora.settings`, `fastora.urls` |
| **MOD-02** | Authentication, User Profiles & Addresses | ISSUE-04 to ISSUE-08 | 5 | `apps.accounts` |
| **MOD-03** | Product Catalog & Category Management | ISSUE-09 to ISSUE-12 | 4 | `apps.products`, `fastora.views` |
| **MOD-04** | Inventory & Multi-Hub Warehouse Engine | ISSUE-13 to ISSUE-16 | 4 | `apps.inventory` |
| **MOD-05** | Shopping Cart & Guest Session Management | ISSUE-17 to ISSUE-20 | 4 | `apps.carts` |
| **MOD-06** | Delivery Zones & Slot Capacity Management | ISSUE-21 to ISSUE-25 | 5 | `apps.delivery` |
| **MOD-07** | Smart Delivery Pricing & Dynamic Fee Engine | ISSUE-26 to ISSUE-28 | 3 | `apps.delivery.services.pricing_service` |
| **MOD-08** | Neighbourhood Delivery Pooling & Clustering | ISSUE-29 to ISSUE-32 | 4 | `apps.delivery.services.pooling_service` |
| **MOD-09** | Order Lifecycle & Checkout Management | ISSUE-33 to ISSUE-36 | 4 | `apps.orders` |
| **MOD-10** | Payment Processing, COD Guardrails & Refunds | ISSUE-37 to ISSUE-40 | 4 | `apps.payment` |
| **MOD-11** | Customer Memberships (Fastora Plus) | ISSUE-41 to ISSUE-43 | 3 | `apps.memberships` |
| **MOD-12** | Delivery Partner & Rider Fleet Operations | ISSUE-44 to ISSUE-46 | 3 | `apps.delivery`, `apps.accounts` |
| **MOD-13** | Dispatcher Operations & Dark Store Analytics | ISSUE-47 to ISSUE-48 | 2 | `apps.delivery.urls_admin` |
| **MOD-14** | Frontend Storefront, UI & Automated Testing | ISSUE-49 to ISSUE-50 | 2 | `frontend/templates`, `apps/*/tests.py` |
| **TOTAL** | **Full Project System Breakdown** | **ISSUE-01 to ISSUE-50** | **50** | **Complete Platform Lifecycle** |

---

## Wave Execution Map

```mermaid
flowchart TD
  subgraph Wave 1: Foundation, Security & Core Models
    I01[ISSUE-01: Env Config]
    I02[ISSUE-02: DRF Auth Hardening]
    I03[ISSUE-03: Media URLs]
    I04[ISSUE-04: Reg Role Fix]
    I05[ISSUE-05: Profile Signal]
    I06[ISSUE-06: Address Exclusivity]
    I08[ISSUE-08: Web Login]
    I09[ISSUE-09: Dynamic Categories]
    I13[ISSUE-13: Multi-Hub Inventory]
    I21[ISSUE-21: Pune Coordinates]
  end

  subgraph Wave 2: Core Domain Services
    I07[ISSUE-07: Token Login API]
    I10[ISSUE-10: Product API]
    I11[ISSUE-11: N+1 Elimination]
    I12[ISSUE-12: Search API]
    I14[ISSUE-14: Atomic Stock Reserve]
    I15[ISSUE-15: Stock Release]
    I17[ISSUE-17: Cart Pre-validation]
    I18[ISSUE-18: Guest Cart Merge]
    I19[ISSUE-19: Cart Item Update]
    I20[ISSUE-20: Cart Detail API]
    I22[ISSUE-22: Zone Validator]
    I23[ISSUE-23: Slot Windows]
    I24[ISSUE-24: Slot Reservation]
    I26[ISSUE-26: Dynamic Fee Engine]
    I27[ISSUE-27: Distance Surcharge]
    I28[ISSUE-28: Order Value Discounts]
    I37[ISSUE-37: Payment Verification]
    I38[ISSUE-38: Webhook HMAC]
    I39[ISSUE-39: COD Rules]
    I41[ISSUE-41: Membership Plans]
  end

  subgraph Wave 3: Pooling, Logistics & Fulfillment
    I16[ISSUE-16: Stock Deduction]
    I25[ISSUE-25: Slot Release]
    I29[ISSUE-29: Order Clustering]
    I30[ISSUE-30: Route Sequencing]
    I31[ISSUE-31: Batch Creation]
    I32[ISSUE-32: Batch Release]
    I33[ISSUE-33: Atomic Checkout]
    I34[ISSUE-34: Order History API]
    I35[ISSUE-35: Order Cancel Rollback]
    I36[ISSUE-36: Express Dispatch]
    I40[ISSUE-40: Staff Refunds]
    I42[ISSUE-42: Paid Membership Sub]
    I43[ISSUE-43: Membership Waiver]
    I44[ISSUE-44: Rider Status Sync]
    I45[ISSUE-45: Rider Drop-off Progression]
    I46[ISSUE-46: Failed Delivery Rollback]
  end

  subgraph Wave 4: Analytics, Storefront & Test Suite
    I47[ISSUE-47: Operations Metrics]
    I48[ISSUE-48: COD Cash Reconciliation]
    I49[ISSUE-49: Responsive Checkout UI]
    I50[ISSUE-50: Full Test Suite]
  end

  I02 --> I07
  I14 --> I16
  I14 --> I33
  I24 --> I33
  I15 --> I35
  I25 --> I35
  I30 --> I31
  I31 --> I32
  I26 --> I43
  I15 --> I46
  I25 --> I46
```

---

## Detailed Issue Catalog (Issues 01 to 50)

### Module 1: Core Configuration & Security Hardening

#### ISSUE-01: Environment-Based Configuration & Secrets Decoupling
- **Module:** `fastora.settings`
- **User Story:** As a DevOps engineer, I want database credentials, `SECRET_KEY`, and `DEBUG` loaded from environment variables via `.env`, so that sensitive production credentials are never committed to version control.
- **Scope & Description:** Remove hardcoded secrets from `backend/fastora/settings.py`. Integrate `python-dotenv` or `environ` with a local `.env.example` template and sensible defaults.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/fastora/settings.py`
  - `backend/.env.example`
  - `backend/requirements.txt`
- **Acceptance Criteria:** Application loads `SECRET_KEY`, `DEBUG`, and database parameters from `.env`. If `.env` is absent, it falls back gracefully without failing local startup.

---

#### ISSUE-02: Centralized REST Framework Authentication & Permission Hardening
- **Module:** `fastora.settings` / DRF
- **User Story:** As a platform security architect, I want DRF endpoints to default to `IsAuthenticated` and support token-based authentication, so that APIs are secured against unauthenticated access by default.
- **Scope & Description:** Configure `DEFAULT_AUTHENTICATION_CLASSES` to include `rest_framework.authentication.TokenAuthentication` and `SessionAuthentication`. Change `DEFAULT_PERMISSION_CLASSES` from `AllowAny` to `IsAuthenticated`. Add `rest_framework.authtoken` to `INSTALLED_APPS`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/fastora/settings.py`
- **Acceptance Criteria:** All DRF API views reject unauthenticated requests with HTTP 401/403 unless explicitly annotated with `permission_classes = [AllowAny]`.

---

#### ISSUE-03: Media File Local Routing & Static Assets Configuration
- **Module:** `fastora.urls` / `fastora.settings`
- **User Story:** As a web customer, I want product images and category icons to load seamlessly in development, so that catalog pages display full visuals instead of 404 broken image placeholders.
- **Scope & Description:** Configure `MEDIA_URL` and `MEDIA_ROOT` in `settings.py`. Append `+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` to `fastora/urls.py` when `DEBUG=True`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/fastora/urls.py`
  - `backend/fastora/settings.py`
- **Acceptance Criteria:** Uploading a product image in Django Admin or seed script returns HTTP 200 when requesting `/media/<filename>` in browser.

---

### Module 2: Authentication, User Profiles & Addresses

#### ISSUE-04: Role Privilege Escalation Guard on Registration API
- **Module:** `apps.accounts` (Serializers)
- **User Story:** As a system administrator, I want user registration to enforce the `customer` role, so that external attackers cannot register directly with `admin` or `dispatcher` privileges.
- **Scope & Description:** Audit `UserRegisterSerializer` in `backend/apps/accounts/serializers.py`. Remove `role` from writable fields or enforce `validated_data['role'] = User.ROLE_CUSTOMER` in `create()`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/accounts/serializers.py`
- **Acceptance Criteria:** `POST /api/auth/register/` with `{"role": "admin"}` creates a user with `role='customer'`.

---

#### ISSUE-05: CustomerProfile Lifecycle Automation via Post-Save Signal
- **Module:** `apps.accounts` (Signals / Models)
- **User Story:** As a customer registering via web form or API, I want my `CustomerProfile` created automatically, so that accessing `user.profile` never raises `RelatedObjectDoesNotExist`.
- **Scope & Description:** Attach a `post_save` receiver on `User` model. Synchronize `User.phone` and `CustomerProfile.phone`. Ensure web form registration triggers profile generation.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/accounts/models.py`
  - `backend/apps/accounts/apps.py`
  - `backend/apps/accounts/forms.py`
- **Acceptance Criteria:** Creating any new `User` instance automatically creates a linked `CustomerProfile` record with matching phone.

---

#### ISSUE-06: Multi-Address Default Exclusivity Enforcement on Model Save
- **Module:** `apps.accounts` (Models)
- **User Story:** As a customer, I want setting one shipping address as default to automatically unset my other addresses, so that I only ever have one default delivery address.
- **Scope & Description:** Override `Address.save()` to reset `is_default=False` on all other addresses belonging to the same user when `self.is_default=True` within a transaction.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/accounts/models.py`
- **Acceptance Criteria:** Creating or updating an address with `is_default=True` results in exactly one address with `is_default=True` for that customer across Admin and API.

---

#### ISSUE-07: Token-Based API Authentication Endpoint (`/api/auth/token-login/`)
- **Module:** `apps.accounts` (Views / Serializers)
- **User Story:** As a mobile app or frontend client, I want to exchange credentials for a persistent auth token, so that I can authorize subsequent REST requests with `Authorization: Token <key>`.
- **Scope & Description:** Implement `TokenAuthLoginView` in `apps.accounts.views` returning token key, user ID, role, and username upon valid credentials.
- **Dependencies:** ISSUE-02 (DRF Token Auth configuration)
- **Files Touched:**
  - `backend/apps/accounts/views.py`
  - `backend/apps/accounts/urls_api.py`
- **Acceptance Criteria:** Valid `POST /api/auth/token-login/` returns HTTP 200 with `{"token": "..."}`; invalid credentials return HTTP 400/401.

---

#### ISSUE-08: Web Session Authentication & Redirect Handler
- **Module:** `apps.accounts` (Views / Templates)
- **User Story:** As a web customer, I want to sign in through standard HTML forms with session cookies and redirect support, so that I can securely navigate between protected pages.
- **Scope & Description:** Standardize session login and logout in `apps/accounts/views.py`. Respect `?next=` query parameters on successful login and provide proper flash messages.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/accounts/views.py`
  - `backend/apps/accounts/urls.py`
  - `frontend/templates/accounts/login.html`
- **Acceptance Criteria:** Form POST to `/accounts/login/` logs in user, creates session cookie, and redirects to requested target or home.

---

### Module 3: Product Catalog & Category Management

#### ISSUE-09: Dynamic Category URL Routing & View Resolution
- **Module:** `fastora.views` / `fastora.urls`
- **User Story:** As a content manager, I want newly added categories to render dynamically on the frontend, so that new categories do not require writing hardcoded Django views or URL routes.
- **Scope & Description:** Refactor hardcoded views (`beauty`, `electronics`, `fruits`, etc.) in `fastora/views.py` into a single dynamic `category_products(request, slug)` view with slug lookup.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/fastora/views.py`
  - `backend/fastora/urls.py`
  - `frontend/templates/products/category_products.html`
- **Acceptance Criteria:** Visiting `/category/<slug>/` loads the category and products dynamically; returns HTTP 404 for non-existent categories.

---

#### ISSUE-10: Product Catalog REST API with Pagination & Filtering
- **Module:** `apps.products` (Views / Serializers)
- **User Story:** As a frontend developer, I want a paginated product API with category filtering, so that product browsing is fast and payload sizes are controlled.
- **Scope & Description:** Add `PageNumberPagination` (e.g. 20 items per page) to `ProductViewSet` / `ProductListView`. Support query parameter filtering by `category`, `search`, and `is_active`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/products/views.py`
  - `backend/apps/products/serializers.py`
- **Acceptance Criteria:** `GET /api/products/?category=groceries&page=1` returns standard paginated JSON structure (`count`, `next`, `previous`, `results`).

---

#### ISSUE-11: N+1 Database Query Bottleneck Elimination in Product Catalog
- **Module:** `fastora.views` / `apps.products`
- **User Story:** As a user browsing the storefront, I want catalog pages to load in under 100ms, so that the database is not strained by executing queries per product card.
- **Scope & Description:** Audit all querysets in `backend/fastora/views.py` and `backend/apps/products/views.py`. Add `.select_related('inventory', 'category')` to prefetch inventory details in a single query.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/fastora/views.py`
  - `backend/apps/products/views.py`
- **Acceptance Criteria:** SQL query count for rendering index and category pages remains constant (O(1)) regardless of the number of products rendered.

---

#### ISSUE-12: Full-Text Product Search API & Template Integration
- **Module:** `fastora.views` / `apps.products`
- **User Story:** As a customer, I want to search for grocery products by name or description, so that I can quickly find items to buy.
- **Scope & Description:** Enhance `/search/` view and `GET /api/products/?search=<term>` using `Q(name__icontains=q) | Q(description__icontains=q)` with active inventory joins.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/fastora/views.py`
  - `frontend/templates/search.html`
- **Acceptance Criteria:** Submitting query `atta` returns all matching active flour products with live prices and stock statuses.

---

### Module 4: Inventory & Warehouse Management

#### ISSUE-13: Multi-Dark-Store Inventory Model Refactoring
- **Module:** `apps.inventory` (Models / Migrations)
- **User Story:** As an operations engineer, I want products to maintain distinct inventory levels across multiple dark store locations, so that Fastora can scale to multiple fulfillment warehouses.
- **Scope & Description:** Refactor `Inventory.product` from `OneToOneField` to `ForeignKey('products.Product')` with `unique_together = ('product', 'location_id')`. Create database migration.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/inventory/models.py`
  - `backend/apps/inventory/migrations/`
- **Acceptance Criteria:** Same product can have distinct stock records for `DARK_STORE_01` (Pune West) and `DARK_STORE_02` (Pune East).

---

#### ISSUE-14: Concurrency-Safe Atomic Stock Reservation Service
- **Module:** `apps.inventory` (Services)
- **User Story:** As an inventory service, I want to reserve stock atomically with row-level database locks, so that two concurrent checkout operations never oversell stock.
- **Scope & Description:** Refactor `reserve_stock(product_id, quantity, location_id)` to execute inside `transaction.atomic()` using `select_for_update()`. Check `quantity_available >= quantity`, deduct available, and increment `reserved_quantity`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/inventory/services.py`
- **Acceptance Criteria:** Simultaneous requests exceeding stock raise `InsufficientStockError`; overselling is mathematically prevented.

---

#### ISSUE-15: Stock Reservation Release & Rollback Service
- **Module:** `apps.inventory` (Services)
- **User Story:** As an inventory manager, I want reserved stock released back to available quantity when an order is cancelled or expires, restoring shelf stock accurately.
- **Scope & Description:** Implement `release_stock(product_id, quantity, location_id)` with row-level locking. Decrement `reserved_quantity` and increment `quantity_available` without allowing negative numbers.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/inventory/services.py`
- **Acceptance Criteria:** Calling `release_stock` for a cancelled order restores available quantity to its exact pre-reservation figure.

---

#### ISSUE-16: Finalized Stock Deduction on Order Fulfillment
- **Module:** `apps.inventory` (Services / Integration)
- **User Story:** As a store inventory auditor, I want stock permanently deducted from `reserved_quantity` when an order is delivered, preventing permanent inventory leakage.
- **Scope & Description:** Wire `confirm_stock_deduction(product_id, quantity, location_id)` to run upon order delivery. Decrement `reserved_quantity` while keeping `quantity_available` untouched.
- **Dependencies:** ISSUE-14 (Stock Reservation)
- **Files Touched:**
  - `backend/apps/inventory/services.py`
  - `backend/apps/delivery/views.py`
- **Acceptance Criteria:** Delivering an order clears the reservation from `reserved_quantity`; total stock count matches physical shelf counts.

---

### Module 5: Shopping Cart & Guest Session Management

#### ISSUE-17: Pre-Insert Stock Availability Verification in Cart Service
- **Module:** `apps.carts` (Services)
- **User Story:** As a shopper, I want immediate validation when adding items to my cart, so that the system doesn't write and then delete invalid cart items in the database.
- **Scope & Description:** Refactor `add_item_to_cart(cart, product_id, quantity)` in `backend/apps/carts/services.py`. Query inventory and check stock before invoking `CartItem.objects.get_or_create()`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/carts/services.py`
- **Acceptance Criteria:** If requested quantity exceeds available inventory, the service raises `InsufficientStockError` without writing any row to `CartItem`.

---

#### ISSUE-18: Guest Cart Migration Across Login Session Rotation
- **Module:** `apps.carts` (Services / Views)
- **User Story:** As a guest shopper, I want my cart items retained after I log in, so that I do not lose my selected groceries when authenticating.
- **Scope & Description:** Intercept guest `session_key` before Django's `login()` rotates the session key. Merge items from the old session cart into the customer's authenticated user cart via `merge_guest_cart()`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/carts/services.py`
  - `backend/apps/accounts/views.py`
- **Acceptance Criteria:** Adding items as an anonymous visitor, then logging in, results in all guest items being present in the user's cart.

---

#### ISSUE-19: Cart Item Quantity Update & Removal Service
- **Module:** `apps.carts` (Services / Views)
- **User Story:** As a customer, I want to increase, decrease, or remove item quantities from my cart, so that my cart reflects my exact shopping list.
- **Scope & Description:** Implement `update_cart_item(cart, item_id, quantity)` with stock validation. Remove item if `quantity <= 0`. Implement `remove_cart_item(cart, item_id)`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/carts/services.py`
  - `backend/apps/carts/views.py`
- **Acceptance Criteria:** Updating quantity to 3 updates total price; updating to 0 deletes the cart item; over-quantity is rejected.

---

#### ISSUE-20: Cart Detail API with Pricing Summary Breakdown
- **Module:** `apps.carts` (Serializers / Views)
- **User Story:** As a frontend developer, I want a comprehensive cart API returning items, unit prices, discounts, and subtotal, so that the cart UI can display real-time totals.
- **Scope & Description:** Expose `GET /api/cart/` returning structured JSON with item count, products, unit price, total item price, and aggregated cart subtotal.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/carts/serializers.py`
  - `backend/apps/carts/views.py`
- **Acceptance Criteria:** `GET /api/cart/` returns HTTP 200 with accurate calculations matching database items.

---

### Module 6: Delivery Zones & Delivery Slots

#### ISSUE-21: Pune Dark Store Center Coordinates & Default Fallback Configuration
- **Module:** `apps.delivery` (Services)
- **User Story:** As a delivery fleet coordinator, I want fallback routing coordinates set to Pune central dark store (`18.5204, 73.8567`) instead of Ahmedabad, so that fallback routing is accurate.
- **Scope & Description:** Update fallback center coordinates in `backend/apps/delivery/services/pooling_service.py` to Central Pune Hub coordinates.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/services/pooling_service.py`
- **Acceptance Criteria:** Unassigned zone center queries default to Pune coordinates (`18.5204, 73.8567`).

---

#### ISSUE-22: Postal Code & Geospatial Serviceable Zone Validator
- **Module:** `apps.delivery` (Services / Views)
- **User Story:** As a customer, I want to verify if my address is within Fastora's delivery coverage before ordering, so that I only order if delivery is supported.
- **Scope & Description:** Enhance `get_serviceable_zone(location_data)` to handle 6-digit postal codes and `{latitude, longitude}` coordinates. Raise `ZoneNotServiceableError` for unsupported zones. Expose `GET /api/delivery/check-zone/`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/services/zone_service.py`
  - `backend/apps/delivery/views.py`
- **Acceptance Criteria:** Valid Pune postal code `411038` returns matching zone; out-of-zone postal code `999999` returns HTTP 400 with `ZoneNotServiceableError`.

---

#### ISSUE-23: Automated Delivery Slot Window Generator & Cutoff Enforcement
- **Module:** `apps.delivery` (Models / Services)
- **User Story:** As a delivery operations manager, I want daily 2-hour delivery slot windows generated with automated order cutoffs, so that customers cannot book expired slots.
- **Scope & Description:** Implement service to create 6 standard 2-hour slot windows per zone for today and tomorrow. Filter out slots where `now() > cutoff_time`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/services/slot_service.py`
  - `backend/apps/delivery/models.py`
- **Acceptance Criteria:** Expired slots are marked `STATUS_CLOSED` or omitted from available slot API responses.

---

#### ISSUE-24: Concurrency-Safe Delivery Slot Capacity Reservation Service
- **Module:** `apps.delivery` (Services)
- **User Story:** As a logistics planner, I want slot capacity checked and incremented atomically during order creation, so that slots never exceed their maximum rider capacity.
- **Scope & Description:** Refactor `reserve_slot_capacity(slot_id)` to execute inside `transaction.atomic()` with `select_for_update()`. Check `current_bookings < max_capacity`, increment by 1, and set `STATUS_FULL` if max reached.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/services/slot_service.py`
- **Acceptance Criteria:** When bookings reach `max_capacity`, further booking attempts raise `SlotNotAvailableError`.

---

#### ISSUE-25: Automated Slot Capacity Release on Order Cancellation
- **Module:** `apps.delivery` (Services)
- **User Story:** As a delivery coordinator, I want cancelled or failed orders to automatically release reserved slot capacity, freeing the window for other shoppers.
- **Scope & Description:** Implement `release_slot_capacity(slot_id)` with row-level locking. Decrement `current_bookings` safely; reset status from `FULL` to `OPEN`.
- **Dependencies:** ISSUE-24 (Slot Reservation)
- **Files Touched:**
  - `backend/apps/delivery/services/slot_service.py`
- **Acceptance Criteria:** Cancelling an order reduces slot's `current_bookings` by 1 and reopens the slot if previously full.

---

### Module 7: Smart Delivery Pricing Engine

#### ISSUE-26: Dynamic Delivery Fee Quote Service (Express vs. Scheduled Pooled)
- **Module:** `apps.delivery` (Services - `pricing_service.py`)
- **User Story:** As a customer, I want to compare delivery costs between Express (15-20 min) and Scheduled Pooled delivery, so that I can save money by choosing micro-delivery pooling.
- **Scope & Description:** Implement `calculate_delivery_quote(location_data, cart_subtotal, delivery_option, user)` returning itemized base fee, distance fee, pooled discount, and final fee.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/services/pricing_service.py`
  - `backend/apps/delivery/views.py`
- **Acceptance Criteria:** Scheduled Pooled delivery quotes return a lower final fee than Express delivery quotes for identical orders.

---

#### ISSUE-27: Distance-Based Surcharge Calculation Using Hub Coordinates
- **Module:** `apps.delivery` (Services - `pricing_service.py`)
- **User Story:** As a delivery fleet owner, I want deliveries further from the hub to include a per-kilometer transit surcharge, ensuring fair driver compensation.
- **Scope & Description:** Compute distance between dark store hub and destination coordinates using Haversine formula. Apply `per_km_fee` from zone's `DeliveryFeeRule`.
- **Dependencies:** ISSUE-21 (Pune Coordinates)
- **Files Touched:**
  - `backend/apps/delivery/services/pricing_service.py`
- **Acceptance Criteria:** Orders located 5 km from the dark store incur calculated distance fees matching configured rule rates.

---

#### ISSUE-28: Cart Value Delivery Fee Thresholds & Free Delivery Discounts
- **Module:** `apps.delivery` (Services - `pricing_service.py`)
- **User Story:** As a shopper with an order above ₹499, I want free or discounted delivery, rewarding me for placing larger orders.
- **Scope & Description:** Apply `min_order_for_discount` evaluation in `pricing_service.py`. Waive base fee or apply tiered discount if `cart_subtotal` satisfies threshold.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/services/pricing_service.py`
- **Acceptance Criteria:** Cart subtotal of ₹500 with a ₹499 free delivery rule triggers discount in the fee calculation breakdown.

---

### Module 8: Neighbourhood Delivery Pooling Engine

#### ISSUE-29: Order Clustering Engine by Delivery Zone and Slot Window
- **Module:** `apps.delivery` (Services - `pooling_service.py`)
- **User Story:** As an operations dispatcher, I want confirmed pooled orders grouped by zone and slot window, so that neighbourhood micro-deliveries can be bundled.
- **Scope & Description:** Query `Order.objects.filter(delivery_option='SCHEDULED_POOLED', status='CONFIRMED', pooled_order__isnull=True)` grouped by `delivery_zone` and `delivery_slot`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/services/pooling_service.py`
- **Acceptance Criteria:** Service produces clustered lists of unbatched orders ready for route sequencing.

---

#### ISSUE-30: Nearest-Neighbor Drop-Off Route Sequencing for Batches
- **Module:** `apps.delivery` (Services - `pooling_service.py`)
- **User Story:** As a delivery partner, I want my batch stops ordered in sequence of nearest proximity, so that I travel the shortest path without backtracking.
- **Scope & Description:** Implement nearest-neighbor TSP heuristic in `pooling_service.py` starting from zone center and visiting customer coordinates in optimal sequence.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/services/pooling_service.py`
- **Acceptance Criteria:** Generates ordered list of order IDs with assigned sequential `drop_sequence` numbers (1, 2, 3...).

---

#### ISSUE-31: Delivery Batch Creation & Order Assignment Engine
- **Module:** `apps.delivery` (Services / Models)
- **User Story:** As a dispatcher, I want batches generated with max capacity constraints (3-5 orders per batch), creating `DeliveryBatch` and linked `PooledOrder` records.
- **Scope & Description:** Implement `run_batch_matching(zone_id, slot_id)`. Create `DeliveryBatch` instances with status `MATCHED` and assign `PooledOrder` records respecting unique order constraints.
- **Dependencies:** ISSUE-30 (Route Sequencing)
- **Files Touched:**
  - `backend/apps/delivery/services/pooling_service.py`
  - `backend/apps/delivery/models.py`
- **Acceptance Criteria:** Returns created batches; each batch contains grouped orders in sequenced drops; orders cannot belong to multiple active batches.

---

#### ISSUE-32: Delivery Batch Dispatch & Partner Assignment Service
- **Module:** `apps.delivery` (Services - `pooling_service.py`)
- **User Story:** As a dispatcher, I want to assign an available delivery partner to a batch and release it, advancing all attached orders to `READY`.
- **Scope & Description:** Implement `release_batch(batch_id, partner_id)`. Validate partner availability, set batch status to `STATUS_RELEASED`, and update all attached orders to `STATUS_READY`.
- **Dependencies:** ISSUE-31 (Batch Creation)
- **Files Touched:**
  - `backend/apps/delivery/services/pooling_service.py`
- **Acceptance Criteria:** Releasing batch assigns partner ID, changes batch status, and transitions order statuses to `READY`.

---

### Module 9: Order Lifecycle & Fulfillment

#### ISSUE-33: Atomic Checkout Service & Order Creation from Cart
- **Module:** `apps.orders` (Services)
- **User Story:** As a customer, I want to convert my cart into a confirmed order with stock reservations, slot booking, and address snapshot in a single atomic transaction.
- **Scope & Description:** Refactor `create_order_from_cart(...)` to wrap all operations in `transaction.atomic()`. Snapshot customer delivery address, reserve stock for each item, reserve slot capacity, create `Order` and `OrderItem` rows, and clear cart.
- **Dependencies:** ISSUE-14 (Stock Reservation), ISSUE-24 (Slot Reservation)
- **Files Touched:**
  - `backend/apps/orders/services.py`
  - `backend/apps/orders/views.py`
- **Acceptance Criteria:** If any step fails (e.g. out of stock or slot full), entire checkout rolls back cleanly with zero orphan orders or leaked stock.

---

#### ISSUE-34: Customer Order History & Tracking API with DRF Pagination
- **Module:** `apps.orders` (Views / Serializers)
- **User Story:** As a customer, I want to view my past and ongoing orders with live status tracking and item breakdowns in a paginated list.
- **Scope & Description:** Expose `GET /api/orders/` filtered by `customer=request.user` with `PageNumberPagination`. Expose `GET /api/orders/<id>/` returning status, tracking info, items, and delivery slot.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/orders/views.py`
  - `backend/apps/orders/serializers.py`
- **Acceptance Criteria:** Paginated response lists user orders sorted by newest first; prevents accessing orders belonging to other customers.

---

#### ISSUE-35: Customer Order Cancellation Workflow with Rollback Services
- **Module:** `apps.orders` (Services / Views)
- **User Story:** As a customer, I want to cancel an unfulfilled order, releasing reserved stock and delivery slot capacity immediately.
- **Scope & Description:** Implement `cancel_order(order_id, user, reason)`. Verify order is owned by user and status is `PENDING` or `CONFIRMED`. Invoke `release_stock()` and `release_slot_capacity()`. Update order status to `CANCELLED`.
- **Dependencies:** ISSUE-15 (Stock Release), ISSUE-25 (Slot Release)
- **Files Touched:**
  - `backend/apps/orders/services.py`
  - `backend/apps/orders/views.py`
- **Acceptance Criteria:** Cancelled order transitions to `CANCELLED`, inventory quantities are restored, and slot capacity is released.

---

#### ISSUE-36: Direct Express Order Dispatch Pipeline
- **Module:** `apps.delivery` / `apps.orders`
- **User Story:** As a delivery partner, I want to view, pick up, and deliver Express orders directly without neighbourhood pooling, fulfilling 15-20 minute delivery SLAs.
- **Scope & Description:** Update `DeliveryOrderStatusUpdateView` to support non-pooled Express orders (`delivery_option='EXPRESS'`). Allow riders to transition express orders through `CONFIRMED` -> `READY` -> `OUT_FOR_DELIVERY` -> `DELIVERED`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/views.py`
  - `backend/apps/delivery/urls.py`
- **Acceptance Criteria:** Rider can successfully deliver an Express order; updates order status to `DELIVERED` without requiring a `PooledOrder` record.

---

### Module 10: Payment Processing, COD Guardrails & Refunds

#### ISSUE-37: Authenticated Online Payment Intent Creation & Verification API
- **Module:** `apps.payment` (Views / Services)
- **User Story:** As an authenticated customer, I want to initiate and verify payment for my order, so that unauthenticated attackers cannot forge payment confirmations.
- **Scope & Description:** Restrict `/api/payment/verify/` to `IsAuthenticated`. Validate that `request.user == order.customer`. Verify payment gateway transaction details before marking order as `PAID`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/payment/views.py`
  - `backend/apps/payment/services.py`
- **Acceptance Criteria:** Unauthenticated POST to `/api/payment/verify/` is rejected with HTTP 401; users cannot verify payments for orders they do not own.

---

#### ISSUE-38: Strict HMAC Signature Verification for Payment Gateway Webhooks
- **Module:** `apps.payment` (Views)
- **User Story:** As a security engineer, I want gateway webhooks to enforce HMAC SHA256 signature verification, preventing forged payment callbacks.
- **Scope & Description:** Refactor `PaymentWebhookView`. Reject requests missing `X-Razorpay-Signature` with HTTP 401. Compute HMAC SHA256 digest with webhook secret and verify using constant-time `hmac.compare_digest`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/payment/views.py`
- **Acceptance Criteria:** Missing or invalid signature returns HTTP 400/401; verified payload processes payment confirmation cleanly.

---

#### ISSUE-39: Cash on Delivery (COD) Configuration Rules & Order Value Guardrails
- **Module:** `apps.payment` / `apps.orders`
- **User Story:** As a store risk manager, I want to enforce COD minimum/maximum limits and restrict COD in specific delivery zones, preventing payment collection defaults.
- **Scope & Description:** Implement validation against `CODConfiguration`. Check `is_globally_enabled`, zone restrictions, and `min_order_value <= subtotal <= max_order_value`. Cancelled unpaid COD orders must set status to `CANCELLED`, not `REFUNDED`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/payment/models.py`
  - `backend/apps/orders/services.py`
- **Acceptance Criteria:** Attempting COD checkout in a restricted zone or outside order limits raises a validation error; cancelled COD orders are marked `CANCELLED`.

---

#### ISSUE-40: Staff-Restricted Refund Workflow with State Validation
- **Module:** `apps.payment` (Views / Services)
- **User Story:** As an operations supervisor, I want refunds restricted strictly to staff and dispatchers with state inspection, preventing customers from refunding delivered goods unilaterally.
- **Scope & Description:** Restrict `PaymentRefundView` to `is_staff` or dispatcher role. Reject refunds if order is already marked `DELIVERED` unless an inspected return is registered. Log refund amount, reference, and staff author.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/payment/views.py`
  - `backend/apps/payment/services.py`
- **Acceptance Criteria:** Non-staff customer attempting to call refund endpoint receives HTTP 403 Forbidden; staff refund updates payment record to `STATUS_REFUNDED`.

---

### Module 11: Customer Memberships (Fastora Plus)

#### ISSUE-41: Membership Plan Catalog & Benefit Definition Engine
- **Module:** `apps.memberships` (Models / Serializers)
- **User Story:** As a marketing manager, I want to define subscription plans with benefit rules (free delivery, fee discounts, priority slots), so that customers can browse subscription offerings.
- **Scope & Description:** Structure `MembershipPlan` model with `benefit_rules` JSON field (e.g. `waive_delivery_fee`, `delivery_discount_pct`). Expose `GET /api/membership/plans/` with `AllowAny` permissions.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/memberships/models.py`
  - `backend/apps/memberships/serializers.py`
  - `backend/apps/memberships/views.py`
- **Acceptance Criteria:** `GET /api/membership/plans/` returns active plans with pricing and benefit specifications.

---

#### ISSUE-42: Verified Paid Membership Subscription Workflow
- **Module:** `apps.memberships` (Views / Services)
- **User Story:** As a business owner, I want customer membership activation to require a verified payment transaction, eliminating free subscription loopholes.
- **Scope & Description:** Refactor `SubscribeMembershipView`. Require payment intent creation for plan price. Activate `CustomerMembership` only upon verified payment confirmation with transaction reference.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/memberships/views.py`
  - `backend/apps/memberships/services.py`
- **Acceptance Criteria:** Calling subscribe without payment does not activate membership; verified payment activates 30-day `CustomerMembership(status='ACTIVE')`.

---

#### ISSUE-43: Membership Delivery Fee Waiver Integration in Pricing Engine
- **Module:** `apps.memberships` / `apps.delivery.services.pricing_service`
- **User Story:** As a Fastora Plus member, I want delivery fees automatically waived during checkout, receiving 100% free delivery benefits.
- **Scope & Description:** Update `calculate_delivery_quote` in `pricing_service.py` to inspect `check_active_membership(user)`. If active and plan waives delivery, set `final_fee = 0.0`.
- **Dependencies:** ISSUE-26 (Dynamic Fee Engine)
- **Files Touched:**
  - `backend/apps/delivery/services/pricing_service.py`
- **Acceptance Criteria:** Active Fastora Plus member receives `final_fee = 0.0` on checkout quote; non-member pays calculated standard fee.

---

### Module 12: Delivery Partner & Rider Fleet Operations

#### ISSUE-44: Delivery Partner Real-time Status Synchronization with Batches
- **Module:** `apps.delivery` / `apps.accounts`
- **User Story:** As a dispatcher, I want a rider's status to automatically switch to `BUSY` when assigned a batch, and revert to `AVAILABLE` on completion, maintaining accurate fleet tracking.
- **Scope & Description:** In `release_batch`, set `partner.availability_status = STATUS_BUSY`. In batch completion handler, reset `partner.availability_status = STATUS_AVAILABLE`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/services/pooling_service.py`
  - `backend/apps/delivery/views.py`
- **Acceptance Criteria:** Rider status transitions to `BUSY` on release and back to `AVAILABLE` when all drops are completed.

---

#### ISSUE-45: Rider Drop-Off Progression & Status Transition API
- **Module:** `apps.delivery` (Views)
- **User Story:** As a delivery partner, I want an API endpoint to advance orders from `PICKED_UP` to `DELIVERED`, recording delivery progress in real time.
- **Scope & Description:** Implement `DeliveryOrderStatusUpdateView` allowing assigned rider to advance pooled order status: `QUEUED` -> `PICKED_UP` -> `DELIVERED`. Trigger `confirm_stock_deduction()` on `DELIVERED`.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/views.py`
  - `backend/apps/delivery/urls.py`
- **Acceptance Criteria:** Rider marks order delivered; `PooledOrder.status` becomes `DELIVERED`, `Order.status` becomes `DELIVERED`, and inventory is finalized.

---

#### ISSUE-46: Failed Delivery Handling & Automatic Stock/Slot Rollback
- **Module:** `apps.delivery` (Views / Services)
- **User Story:** As a delivery operations manager, I want failed deliveries to record reasons and automatically release reserved stock and slot capacity, preventing blocked inventory.
- **Scope & Description:** When rider marks an order as `STATUS_FAILED`, update `Order.status = STATUS_CANCELLED`, record `cancellation_reason`, invoke `release_stock()`, and invoke `release_slot_capacity()`.
- **Dependencies:** ISSUE-15 (Stock Release), ISSUE-25 (Slot Release)
- **Files Touched:**
  - `backend/apps/delivery/views.py`
- **Acceptance Criteria:** Marking delivery failed marks order cancelled, frees reserved inventory, and increments available slot capacity.

---

### Module 13: Dispatcher Operations & Dark Store Analytics

#### ISSUE-47: Dark Store Operations & Delivery Metrics API
- **Module:** `apps.delivery` (Views / URLs Admin)
- **User Story:** As an operations dispatcher, I want an admin metrics dashboard API showing active batches, pending orders, and idle riders per zone, so that I can balance dispatch loads.
- **Scope & Description:** Implement `AdminMetricsReportView` under `/api/admin/metrics/`. Return JSON with total active batches, available riders, pending pooled orders, and today's delivered count.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/delivery/views.py`
  - `backend/apps/delivery/urls_admin.py`
- **Acceptance Criteria:** `GET /api/admin/metrics/` returns accurate operational counts filtered by zone.

---

#### ISSUE-48: COD Order Cash Settlement & Rider Reconciliation
- **Module:** `apps.payment` (Services / Views)
- **User Story:** As a store cashier / finance supervisor, I want to reconcile cash collected by delivery partners for COD orders, marking payments settled.
- **Scope & Description:** Implement `confirm_cod_collection(payment_id, collected_by, staff_user)`. Verify staff permission, transition `payment.status` from `STATUS_COD_PENDING` to `STATUS_SUCCESS`, and log timestamp.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `backend/apps/payment/services.py`
  - `backend/apps/payment/views.py`
- **Acceptance Criteria:** Calling COD settlement marks payment `SUCCESS` and records the settling staff member and collecting rider.

---

### Module 14: Frontend Storefront, UI & Automated Testing

#### ISSUE-49: Unified Dynamic Frontend Storefront & Checkout Interface
- **Module:** `frontend/templates` / `fastora.views`
- **User Story:** As a web customer, I want an intuitive checkout screen with slot selection, address choices, express vs. pooled delivery options, and order breakdown, so that ordering is seamless.
- **Scope & Description:** Build and polish `frontend/templates/orders/checkout.html` and `base.html`. Integrate dynamic slot dropdown, live delivery fee calculation, address selection, and payment mode toggle.
- **Dependencies:** None (Independent)
- **Files Touched:**
  - `frontend/templates/orders/checkout.html`
  - `frontend/templates/base.html`
  - `frontend/templates/index.html`
  - `backend/fastora/views.py`
- **Acceptance Criteria:** Customers can select an address, choose between Express and Scheduled Pooled delivery, pick an open slot, select COD or Online payment, and submit checkout successfully.

---

#### ISSUE-50: Comprehensive Automated Test Suite (Unit, Service & Integration)
- **Module:** `backend/apps/*/tests.py`
- **User Story:** As a software engineer, I want comprehensive automated unit and integration tests across all 8 apps, so that regressions are caught immediately in CI/CD.
- **Scope & Description:** Implement standard Django `TestCase` and DRF `APITestCase` suites in `tests.py` for all 8 apps (`accounts`, `products`, `inventory`, `carts`, `orders`, `payment`, `delivery`, `memberships`). Test authentication, stock overselling guards, slot capacity, dynamic pricing, and webhook HMAC.
- **Dependencies:** All Core Services
- **Files Touched:**
  - `backend/apps/accounts/tests.py`
  - `backend/apps/products/tests.py`
  - `backend/apps/inventory/tests.py`
  - `backend/apps/carts/tests.py`
  - `backend/apps/orders/tests.py`
  - `backend/apps/payment/tests.py`
  - `backend/apps/delivery/tests.py`
  - `backend/apps/memberships/tests.py`
- **Acceptance Criteria:** Running `python manage.py test apps` runs isolated test suites with zero failures and zero database leaks.

---

## Issue Dependency & Independence Matrix

| Issue ID | Title | Minimum Dependencies | Can Be Executed In Parallel? |
|:---|:---|:---|:---:|
| **ISSUE-01** | Env Config & Secrets | None | Yes |
| **ISSUE-02** | DRF Permission & Auth Config | None | Yes |
| **ISSUE-03** | Local Media & Static Routing | None | Yes |
| **ISSUE-04** | Role Privilege Guard | None | Yes |
| **ISSUE-05** | CustomerProfile Post-Save Signal | None | Yes |
| **ISSUE-06** | Address Default Exclusivity | None | Yes |
| **ISSUE-07** | Token Login API | ISSUE-02 | With Wave 2 |
| **ISSUE-08** | Web Session Auth & Redirects | None | Yes |
| **ISSUE-09** | Dynamic Category Routing | None | Yes |
| **ISSUE-10** | DRF Product Catalog API | None | Yes |
| **ISSUE-11** | N+1 Query Elimination | None | Yes |
| **ISSUE-12** | Product Search API & View | None | Yes |
| **ISSUE-13** | Multi-Hub Inventory Model | None | Yes |
| **ISSUE-14** | Atomic Stock Reservation | None | Yes |
| **ISSUE-15** | Stock Release Service | None | Yes |
| **ISSUE-16** | Stock Deduction on Delivery | ISSUE-14 | With Wave 3 |
| **ISSUE-17** | Cart Stock Pre-Validation | None | Yes |
| **ISSUE-18** | Guest Cart Session Merge | None | Yes |
| **ISSUE-19** | Cart Item Update & Removal | None | Yes |
| **ISSUE-20** | Cart Detail Breakdown API | None | Yes |
| **ISSUE-21** | Pune Hub Fallback Coordinates | None | Yes |
| **ISSUE-22** | Zone Coverage Validator | None | Yes |
| **ISSUE-23** | Slot Windows & Cutoff Engine | None | Yes |
| **ISSUE-24** | Slot Capacity Reservation | None | Yes |
| **ISSUE-25** | Slot Release Service | ISSUE-24 | With Wave 3 |
| **ISSUE-26** | Dynamic Delivery Fee Engine | None | Yes |
| **ISSUE-27** | Distance Fee Surcharge | ISSUE-21 | With Wave 2 |
| **ISSUE-28** | Cart Value Delivery Discounts | None | Yes |
| **ISSUE-29** | Order Clustering Engine | None | Yes |
| **ISSUE-30** | Route Drop-Off Sequencing | None | Yes |
| **ISSUE-31** | Batch Generation Service | ISSUE-30 | With Wave 3 |
| **ISSUE-32** | Batch Release & Rider Assignment | ISSUE-31 | With Wave 3 |
| **ISSUE-33** | Atomic Checkout from Cart | ISSUE-14, ISSUE-24 | With Wave 3 |
| **ISSUE-34** | Order History API | None | Yes |
| **ISSUE-35** | Order Cancel & Rollback | ISSUE-15, ISSUE-25 | With Wave 3 |
| **ISSUE-36** | Express Order Dispatch | None | Yes |
| **ISSUE-37** | Authenticated Payment Verify | None | Yes |
| **ISSUE-38** | Webhook HMAC Signature | None | Yes |
| **ISSUE-39** | COD Guardrails & Limits | None | Yes |
| **ISSUE-40** | Staff Refund State Validation | None | Yes |
| **ISSUE-41** | Membership Plan Catalog | None | Yes |
| **ISSUE-42** | Paid Membership Subscription | None | Yes |
| **ISSUE-43** | Membership Free Delivery Waiver | ISSUE-26 | With Wave 3 |
| **ISSUE-44** | Delivery Partner Status Sync | None | Yes |
| **ISSUE-45** | Rider Drop-off Progression API | None | Yes |
| **ISSUE-46** | Failed Delivery Stock Rollback | ISSUE-15, ISSUE-25 | With Wave 3 |
| **ISSUE-47** | Dark Store Operations Metrics | None | Yes |
| **ISSUE-48** | COD Cash Settlement Workflow | None | Yes |
| **ISSUE-49** | Dynamic Checkout Frontend UI | None | Yes |
| **ISSUE-50** | Automated Full Test Suite | All Core Services | With Wave 4 |
