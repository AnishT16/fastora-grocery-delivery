# Fastora Backend Issues & Technical Debt Catalog

> **Audit Date:** 2026-11-18  
> **Target System:** Fastora Quick-Commerce Backend (Django 6.0 / DRF / PostgreSQL)  
> **Status:** Open for Triage & Remediation  

---

## Executive Summary

A comprehensive architectural, security, and code quality audit of the Fastora backend was conducted across all 8 core apps (`accounts`, `products`, `inventory`, `carts`, `orders`, `payment`, `delivery`, `memberships`) and core project configuration (`fastora/settings.py`, `fastora/urls.py`, `fastora/views.py`).

A total of **25 distinct issues** were identified and categorized by severity:
- 🔴 **Critical Severity (5 issues):** Remote privilege escalation, unauthenticated payment spoofing, bypassed webhook signatures, unauthorized customer self-refunds, and unverified free membership subscriptions.
- 🟠 **High Severity (5 issues):** Hardcoded production secrets, stock deduction never finalized on fulfillment (inventory leakage), unhandled failed deliveries locking stock, express orders untrackable/undeliverable by partners, and complete absence of automated unit/integration tests.
- 🟡 **Medium Severity (10 issues):** Multi-warehouse scalability blockers (`OneToOneField`), DoS vulnerability on slot capacity, stranded guest carts on login session rotation, missing default address exclusivity, duplicate profile phone fields, missing DRF pagination, and N+1 query bottlenecks in frontend views.
- 🟢 **Low / Tech Debt (5 issues):** Misconfigured Pune fallback coordinates, hardcoded category routes, missing media file routing in local development, duplicate URL routes, and non-atomic admin product creation.

---

## Issue Matrix

| Issue ID | Severity | App / Component | Title | Impact |
|:---|:---:|:---|:---|:---|
| **ISSUE-01** | 🔴 Critical | `apps.accounts` | Privilege Escalation: Self-Registration Allows Arbitrary Role Assignment | Unauthenticated users can register directly as `admin` or `dispatcher` |
| **ISSUE-02** | 🔴 Critical | `apps.payment` | Unauthenticated Payment Verification Endpoint Spoofing | Anyone can send fake payment confirmations to mark orders as paid |
| **ISSUE-03** | 🔴 Critical | `apps.payment` | Payment Webhook Signature Bypassed If Header Is Omitted | Attackers can forge gateway callbacks by omitting the signature header |
| **ISSUE-04** | 🔴 Critical | `apps.payment` | Arbitrary Customer-Initiated Refunds Without State Validation | Customers can refund delivered orders while keeping goods |
| **ISSUE-05** | 🔴 Critical | `apps.memberships` | Free Membership Activation Without Payment Verification | Any user can activate paid Fastora Plus plans with zero payment |
| **ISSUE-06** | 🟠 High | `fastora.settings` | Hardcoded Sensitive Secrets, Database Credentials & Permissive CORS | Compromised database passwords, debug mode, and wildcards in settings |
| **ISSUE-07** | 🟠 High | `fastora.settings` | Permissive Default DRF Permissions & Missing API Token Authentication | Endpoints default to `AllowAny`; API clients receive no auth tokens |
| **ISSUE-08** | 🟠 High | `apps.inventory` | Stock Deduction Never Finalized on Order Fulfillment | `confirm_stock_deduction` is dead code; `reserved_quantity` leaks forever |
| **ISSUE-09** | 🟠 High | `apps.delivery` | Failed Deliveries Do Not Release Reserved Stock or Update Order Status | Orders stuck in limbo; inventory & slots stay permanently blocked |
| **ISSUE-10** | 🟠 High | `apps.delivery` | Express Delivery Orders Cannot Be Dispatched or Delivered by Riders | `DeliveryOrderStatusUpdateView` only handles pooled orders |
| **ISSUE-11** | 🟠 High | `backend` | Zero Automated Unit or Integration Tests Across All Apps | Regression risks; `tests.py` files are empty across all apps |
| **ISSUE-12** | 🟡 Medium | `apps.inventory` | `OneToOneField` on Product Inventory Blocks Multi-Dark-Store Architecture | Cannot maintain inventory across multiple fulfillment hubs |
| **ISSUE-13** | 🟡 Medium | `apps.carts` | Cart Service Inserts Item in DB Before Verifying Stock Availability | Unnecessary DB write and immediate delete when stock is exceeded |
| **ISSUE-14** | 🟡 Medium | `apps.orders` | Cancelled COD Orders Incorrectly Marked as "REFUNDED" | Financial mismatch: unpaid orders marked as refunded |
| **ISSUE-15** | 🟡 Medium | `apps.delivery` | Slot Reservation Endpoint Enables Denial of Service (DoS) & Double Booking | Slot capacity can be filled without orders; checkout reserves slot twice |
| **ISSUE-16** | 🟡 Medium | `apps.delivery` | Delivery Partner Availability Status Not Synchronized with Batches | Riders never marked `BUSY` or reset to `AVAILABLE` on completion |
| **ISSUE-17** | 🟡 Medium | `apps.carts` | Guest Cart Stranded Upon Login Due to Session Key Rotation | Django `login()` rotates session key; guest cart is lost on sign-in |
| **ISSUE-18** | 🟡 Medium | `apps.accounts` | Divergent Phone Fields & Missing Profile on HTML Registration | `user.profile` not created by web form; phone is duplicated |
| **ISSUE-19** | 🟡 Medium | `apps.accounts` | Lack of Exclusivity on `Address.is_default` | Multiple addresses can have `is_default=True` simultaneously |
| **ISSUE-20** | 🟡 Medium | `apps.products` / `apps.orders` | Missing DRF Pagination on Product and Order APIs | Large datasets cause memory spikes and slow response times |
| **ISSUE-21** | 🟡 Medium | `fastora.views` | N+1 Query Bottleneck in Frontend Product Catalog and Search | Omission of `select_related('inventory')` triggers queries per item |
| **ISSUE-22** | 🟢 Low | `fastora.urls` | Redundant and Overlapping URL Routes | Duplicated routes (`payment/` vs `payments/`, `delivery/` vs `api/delivery/`) |
| **ISSUE-23** | 🟢 Low | `fastora.urls` | Missing Media File Routing in Local Development | `MEDIA_URL` not mapped in `urls.py`; uploaded product images return 404 |
| **ISSUE-24** | 🟢 Low | `fastora.views` | Hardcoded Category Views Instead of Dynamic Slug Resolution | New categories added via admin cannot be viewed on frontend |
| **ISSUE-25** | 🟢 Low | `apps.delivery` | Default Fallback Coordinates Set to Ahmedabad Instead of Pune | Fallback coordinates point to Gujarat instead of Pune dark store |

---

## Detailed Issue Specifications

### 🔴 Critical Issues

#### ISSUE-01: Privilege Escalation — Self-Registration Allows Arbitrary Role Assignment
- **Module:** `backend/apps/accounts/serializers.py` (Lines 16-37)
- **Problem:** `UserRegisterSerializer` includes the `role` field in its `Meta.fields` and accepts arbitrary values without validation or read-only restrictions:
  ```python
  class Meta:
      model = User
      fields = ['id', 'username', 'email', 'phone', 'first_name', 'last_name', 'password', 'password_confirm', 'role']
  ```
- **Impact:** Any unauthenticated client calling `POST /api/auth/register/` can send `{"role": "admin"}` or `{"role": "dispatcher"}` and immediately receive superuser/staff operational rights.
- **Remediation:** Remove `'role'` from writable serializer fields or explicitly enforce `role = User.ROLE_CUSTOMER` in `create()`:
  ```python
  def create(self, validated_data):
      validated_data.pop('password_confirm', None)
      password = validated_data.pop('password')
      validated_data['role'] = User.ROLE_CUSTOMER  # Force customer role
      user = User(**validated_data)
      user.set_password(password)
      user.save()
  ```

---

#### ISSUE-02: Unauthenticated & Unsigned Payment Verification Endpoint
- **Module:** `backend/apps/payment/views.py` (Lines 28-58)
- **Problem:** `PaymentVerificationWebhookView` has `permission_classes = [AllowAny]` and does not perform HMAC or token validation on `request.data`:
  ```python
  class PaymentVerificationWebhookView(APIView):
      permission_classes = [AllowAny]
      def post(self, request):
          serializer = PaymentVerificationInputSerializer(data=request.data)
          ...
          payment = verify_online_payment(order_id=order_id, payment_status=payment_status)
  ```
- **Impact:** An attacker can POST `{"order_id": 105, "payment_status": "SUCCESS"}` to `/api/payment/verify/` and mark any unpaid online order as confirmed and ready for dispatch.
- **Remediation:** Protect the endpoint with `IsAuthenticated` and verify that the calling user is the order owner, or deprecate this endpoint in favor of the secured signature-verified webhook.

---

#### ISSUE-03: Webhook Signature Verification Bypassed When Header Is Omitted
- **Module:** `backend/apps/payment/views.py` (Lines 158-163)
- **Problem:** The signature verification in `PaymentWebhookView` only runs if `signature` is present:
  ```python
  if signature:
      ...
      if not getattr(settings, 'DEBUG', True) and not hmac.compare_digest(expected_sig, signature):
          return Response({'error': 'Invalid webhook signature'}, status=status.HTTP_400_BAD_REQUEST)
  ```
- **Impact:** An attacker can simply send the webhook payload without the `X-Razorpay-Signature` header, completely bypassing signature verification and confirming unauthorized payments.
- **Remediation:** Require signature verification unconditionally:
  ```python
  if not signature:
      return Response({'error': 'Missing webhook signature header'}, status=status.HTTP_401_UNAUTHORIZED)
  if not hmac.compare_digest(expected_sig, signature):
      return Response({'error': 'Invalid webhook signature'}, status=status.HTTP_400_BAD_REQUEST)
  ```

---

#### ISSUE-04: Arbitrary Customer-Initiated Refunds Without State Validation
- **Module:** `backend/apps/payment/views.py` (Lines 190-218)
- **Problem:** `PaymentRefundView` allows regular customers to trigger instant refunds on their own orders:
  ```python
  if not (request.user.is_staff or request.user == payment.order.customer):
      return Response({'error': "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
  payment.mark_refunded(...)
  ```
  It does not check whether the order has already been delivered, and does not return items to inventory or log a cancellation event with reasons.
- **Impact:** Customers can place orders, wait until the grocery items are delivered to their doorstep, and immediately call `/api/payment/refund/` to obtain a full refund while retaining the goods.
- **Remediation:** Restrict refund initiation exclusively to staff (`request.user.is_staff` or `is_dispatcher`). Customers must submit a return/refund request subject to inspection and approval.

---

#### ISSUE-05: Free Membership Activation Without Payment Verification
- **Module:** `backend/apps/memberships/views.py` (Lines 28-41)
- **Problem:** `SubscribeMembershipView` allows any authenticated user to subscribe to paid plans (e.g. Fastora Plus) without creating a payment intent or verifying transaction completion:
  ```python
  plan_id = serializer.validated_data['plan_id']
  membership = subscribe_user_to_plan(user=request.user, plan_id=plan_id)
  ```
- **Impact:** Complete revenue leakage on customer subscriptions; any user can gain 100% free delivery benefits without paying the membership subscription fee.
- **Remediation:** Create a `Payment` record for the membership plan fee and only activate `CustomerMembership` upon verified payment confirmation.

---

### 🟠 High Severity Issues

#### ISSUE-06: Production Credentials & Secrets Hardcoded in `settings.py`
- **Module:** `backend/fastora/settings.py` (Lines 23, 26, 28, 94-102, 158)
- **Problem:** Sensitive configuration values are hardcoded in source control:
  - `SECRET_KEY = 'django-insecure-7p@$mss1@)...'`
  - `DEBUG = True`
  - `ALLOWED_HOSTS = ['*']`
  - `DATABASES['default']['PASSWORD'] = 'Fastora_@20'`
  - `CORS_ALLOW_ALL_ORIGINS = True`
- **Impact:** Serious security exposure when deployed; credential leakage and CSRF/CORS vulnerabilities.
- **Remediation:** Integrate `django-environ` or `python-dotenv` to load secrets from environment variables with sensible production defaults.

---

#### ISSUE-07: Permissive Default DRF Permissions & Missing API Token Authentication
- **Module:** `backend/fastora/settings.py` (Lines 148-156) & `backend/apps/accounts/views.py`
- **Problem:** 
  1. `DEFAULT_PERMISSION_CLASSES` is set to `['rest_framework.permissions.AllowAny']`.
  2. `DEFAULT_AUTHENTICATION_CLASSES` only includes `SessionAuthentication` and `BasicAuthentication`.
  3. `rest_framework.authtoken` is missing from `INSTALLED_APPS`.
  4. `AuthLoginAPIView` creates a Django session cookie but returns no token for API or mobile clients.
- **Impact:** Mobile apps and decoupled frontends cannot authenticate via standard bearer tokens. Any view without an explicit permission class is exposed publicly by default.
- **Remediation:** Set default permission to `IsAuthenticated`, add `rest_framework.authtoken` (or `rest_framework_simplejwt`), and return the token upon successful login.

---

#### ISSUE-08: Stock Deduction Never Finalized on Order Fulfillment
- **Module:** `backend/apps/inventory/services.py` & `backend/apps/delivery/views.py` (Lines 298-305)
- **Problem:** The function `confirm_stock_deduction(product_id, quantity)` exists in `inventory/services.py`, but is never invoked anywhere in the application workflow. When `PooledOrder.STATUS_DELIVERED` is reached, `order.status` is set to `STATUS_DELIVERED`, but stock remains permanently locked in `reserved_quantity`.
- **Impact:** Permanent inventory leakage. Total stock accounting becomes corrupted as `reserved_quantity` accumulates indefinitely.
- **Remediation:** In `DeliveryOrderStatusUpdateView`, iterate through `order.items.all()` and invoke `confirm_stock_deduction()` when the order transitions to `STATUS_DELIVERED`.

---

#### ISSUE-09: Failed Deliveries Do Not Release Reserved Stock or Update Order
- **Module:** `backend/apps/delivery/views.py` (Lines 305-307)
- **Problem:** When a delivery partner marks a pooled order as `STATUS_FAILED`:
  ```python
  elif new_status == PooledOrder.STATUS_FAILED:
      order.cancellation_reason = notes or "Delivery attempt failed."
  ```
  `order.status` is NOT updated, `release_stock()` is NOT called, and `release_slot_capacity()` is NOT called.
- **Impact:** Inventory remains reserved indefinitely for failed orders; customers are not notified or refunded, and slot capacity is permanently lost.
- **Remediation:** Trigger order cancellation and rollback service functions on delivery failure.

---

#### ISSUE-10: Express Delivery Orders Cannot Be Dispatched or Delivered by Riders
- **Module:** `backend/apps/delivery/views.py` (Lines 275-282)
- **Problem:** `DeliveryOrderStatusUpdateView` strictly queries:
  ```python
  pooled_order = PooledOrder.objects.select_for_update().select_related('order', 'batch').get(order_id=pk)
  ```
  Since Express orders (`delivery_option='express'`) bypass neighbourhood pooling, they have no `PooledOrder` record.
- **Impact:** Delivery partners have no API to pick up, update transit, or deliver Express orders. Express orders remain permanently stuck in `confirmed` status.
- **Remediation:** Update `DeliveryOrderStatusUpdateView` to support both pooled and direct express order workflows, or implement an express dispatch pipeline.

---

#### ISSUE-11: Complete Absence of Automated Unit and Integration Tests
- **Module:** `backend/apps/*/tests.py`
- **Problem:** All `tests.py` files across all 8 apps contain only placeholder comments (`# Create your tests here.`). The only test script is `verify_fastora.py`, which is a standalone, ad-hoc verification script that mutates the live database.
- **Impact:** High risk of undetected regression bugs when refactoring or adding features; zero CI/CD automated test validation.
- **Remediation:** Implement standard `APITestCase` and `TestCase` suites covering models, services, serializers, permissions, and edge cases.

---

### 🟡 Medium Severity Issues

#### ISSUE-12: `OneToOneField` on Inventory Blocks Multi-Warehouse Scalability
- **Module:** `backend/apps/inventory/models.py` (Lines 17-21)
- **Problem:** `Inventory` uses `OneToOneField('products.Product')`. While `location_id` is defined on `Inventory`, a product can only have one inventory record across the entire platform.
- **Impact:** The system cannot support multiple dark stores or warehouse hubs for the same product catalog.
- **Remediation:** Change to `ForeignKey` with `unique_together = ('product', 'location_id')`.

---

#### ISSUE-13: Cart Service Inserts Item in DB Before Verifying Stock
- **Module:** `backend/apps/carts/services.py` (Lines 68-93)
- **Problem:** `add_item_to_cart` creates the `CartItem` in the database first via `get_or_create()`, and only then checks `if quantity > available_stock: cart_item.delete()`.
- **Impact:** Unnecessary database writes and deletes; race conditions on high-frequency cart actions.
- **Remediation:** Validate quantity against stock before calling `get_or_create`.

---

#### ISSUE-14: Cancelled COD Orders Incorrectly Marked as "REFUNDED"
- **Module:** `backend/apps/orders/services.py` (Lines 227-229)
- **Problem:** In `cancel_order`, if `payment.status` is `STATUS_COD_PENDING`, the payment status is changed to `STATUS_REFUNDED`:
  ```python
  elif payment.status in [Payment.STATUS_PENDING, Payment.STATUS_COD_PENDING]:
      payment.status = Payment.STATUS_REFUNDED
  ```
- **Impact:** Accounting anomaly: financial reports will treat unpaid cancelled COD orders as cash outflows (refunds).
- **Remediation:** Set `payment.status = Payment.STATUS_FAILED` or `STATUS_CANCELLED` for unpaid COD orders.

---

#### ISSUE-15: Slot Reservation Endpoint Enables Denial of Service & Double Booking
- **Module:** `backend/apps/delivery/views.py` (`SlotReservationAPIView`) & `backend/apps/orders/services.py` (Line 81)
- **Problem:** 
  1. `SlotReservationAPIView` increments `current_bookings` without an order or expiration TTL. A script can easily exhaust all slots.
  2. `create_order_from_cart` calls `reserve_slot_capacity(slot_id=slot_id)` again, causing a double increment if the frontend called reservation first.
- **Impact:** Slot starvation for legitimate users; inaccurate capacity tracking.
- **Remediation:** Remove redundant slot reservation or implement redis-based slot locks with TTL.

---

#### ISSUE-16: Delivery Partner Availability Status Not Synchronized with Batches
- **Module:** `backend/apps/delivery/services/pooling_service.py` & `backend/apps/delivery/views.py`
- **Problem:** Releasing a batch to a delivery partner (`release_batch`) does not set `DeliveryPartner.availability_status` to `STATUS_BUSY`. When the batch completes, it is not restored to `STATUS_AVAILABLE`.
- **Impact:** `AdminMetricsReportView` reports inaccurate `available_riders` numbers. Dispatchers cannot tell which riders are actually idle.
- **Remediation:** Update `DeliveryPartner.availability_status` synchronously in batch release and batch completion handlers.

---

#### ISSUE-17: Guest Cart Stranded Upon Login Due to Session Key Rotation
- **Module:** `backend/apps/carts/services.py` (Lines 17-37) & `backend/apps/accounts/views.py`
- **Problem:** When a user logs in via `login(request, user)`, Django automatically calls `request.session.cycle_key()`. In `get_or_create_cart(request)`, `request.session.session_key` is now the new key, so `Cart.objects.get(session_key=session_key)` fails to locate the guest cart created prior to login.
- **Impact:** Shoppers who add items to their cart as guests lose all cart items immediately upon signing in.
- **Remediation:** Capture the guest session key before `login(request, user)` and pass it explicitly to `get_or_create_cart(request, guest_session_key)`.

---

#### ISSUE-18: Divergent Phone Fields & Missing Profile on HTML Registration
- **Module:** `backend/apps/accounts/forms.py` & `backend/apps/accounts/models.py`
- **Problem:** 
  1. Phone numbers exist on both `User.phone` and `CustomerProfile.phone` without sync hooks.
  2. `CustomerRegistrationForm.save()` creates a `User` but does not create a `CustomerProfile`.
- **Impact:** Users registering via web forms crash with `RelatedObjectDoesNotExist` when accessing `user.profile`.
- **Remediation:** Attach a `post_save` signal on `User` to automatically create `CustomerProfile`.

---

#### ISSUE-19: Lack of Exclusivity on `Address.is_default`
- **Module:** `backend/apps/accounts/models.py` (Lines 48-72)
- **Problem:** `Address` model has `is_default = models.BooleanField(default=False)` without a unique constraint or model `save()` override. Only the serializer handles default exclusivity.
- **Impact:** Directly creating or updating addresses via Django admin or management commands can result in multiple default addresses for a single user.
- **Remediation:** Override `Address.save()` to reset other defaults when `self.is_default=True`.

---

#### ISSUE-20: Missing DRF Pagination on Product and Order APIs
- **Module:** `backend/apps/products/views.py` & `backend/apps/orders/views.py`
- **Problem:** Viewsets and API views do not specify `pagination_class`, and `REST_FRAMEWORK` settings lack global `PAGE_SIZE`.
- **Impact:** Endpoints like `/api/products/` and `/api/orders/` return the entire database table in a single JSON payload, causing memory exhaustion and high latency under scale.
- **Remediation:** Add `PageNumberPagination` configuration to `REST_FRAMEWORK` settings.

---

#### ISSUE-21: N+1 Query Bottleneck in Frontend Product Catalog and Search
- **Module:** `backend/fastora/views.py` (`indexfile`, `search`)
- **Problem:** `Product.objects.filter(...).select_related('category')` omits `select_related('inventory')`.
- **Impact:** Rendering `{{ product.price }}` or `{{ product.current_price }}` in templates triggers an additional database query for every product displayed.
- **Remediation:** Add `.select_related('inventory')` to all product queryset queries in `views.py`.

---

### 🟢 Low Severity / Technical Debt Issues

#### ISSUE-22: Redundant and Overlapping URL Routes
- **Module:** `backend/fastora/urls.py`
- **Problem:** 
  - `api/payment/` and `api/payments/` both route to `apps.payment.urls`.
  - `delivery/` and `api/delivery/` both route to `apps.delivery.urls`.
  - `api/` routes to `apps.accounts.urls_api` while `accounts/` routes to `apps.accounts.urls`.
- **Impact:** Confusing API documentation, duplicate endpoint paths, and maintenance overhead.
- **Remediation:** Standardize on clean REST prefixes: `/api/v1/...` for APIs and root paths for HTML templates.

---

#### ISSUE-23: Missing Media URL Configuration in Development
- **Module:** `backend/fastora/urls.py`
- **Problem:** `urlpatterns` lacks `+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)`.
- **Impact:** Uploaded product images, category icons, and user avatars return 404 HTTP errors in local development.
- **Remediation:** Append static media serving pattern in `fastora/urls.py` when `DEBUG` is True.

---

#### ISSUE-24: Hardcoded Category Views Instead of Dynamic Slug Resolution
- **Module:** `backend/fastora/views.py`
- **Problem:** Hardcoded functions `beauty`, `electronics`, `gifting`, `kids`, `pharmacy`, `meat`, `fruits`, and `Grocery`.
- **Impact:** Adding new categories to the database requires manual code changes, new URL patterns, and template files.
- **Remediation:** Implement a single dynamic view: `def category_products(request, slug):`.

---

#### ISSUE-25: Default Fallback Coordinates Set to Ahmedabad Instead of Pune
- **Module:** `backend/apps/delivery/services/pooling_service.py` (Lines 80-81)
- **Problem:** When zone center coordinates are null, the pooling service falls back to `23.0365, 72.5611` (Ahmedabad, Gujarat) instead of Pune (`18.5204, 73.8567`).
- **Impact:** Nearest-neighbor routing calculations will yield incorrect sequencing if a zone has missing coordinates.
- **Remediation:** Update fallback coordinates to central Pune dark store coordinates.

---

## Prioritized Implementation Roadmap

```
Wave 1 (Security & Data Integrity Hotfixes)
  ├── Fix ISSUE-01: Remove role from UserRegisterSerializer
  ├── Fix ISSUE-02: Secure PaymentVerificationWebhookView
  ├── Fix ISSUE-03: Enforce strict webhook HMAC signature
  ├── Fix ISSUE-04: Restrict refunds to staff/admin
  ├── Fix ISSUE-05: Require payment for membership subscription
  └── Fix ISSUE-06: Extract secrets and credentials to .env

Wave 2 (Stock & Order Fulfillment Engine)
  ├── Fix ISSUE-08: Call confirm_stock_deduction on delivery
  ├── Fix ISSUE-09: Release stock & slots on failed delivery
  ├── Fix ISSUE-10: Implement express order rider dispatch/delivery
  ├── Fix ISSUE-14: Correct COD cancellation payment status
  └── Fix ISSUE-15: Fix slot reservation double-booking

Wave 3 (User Experience, Performance & Architecture)
  ├── Fix ISSUE-17: Preserve guest cart across login session rotation
  ├── Fix ISSUE-18: Auto-create CustomerProfile via post_save signal
  ├── Fix ISSUE-20: Add DRF pagination to products & orders
  ├── Fix ISSUE-21: Add select_related('inventory') to eliminate N+1 queries
  └── Fix ISSUE-23: Add MEDIA_URL routing in urls.py

Wave 4 (Test Automation & Clean Up)
  ├── Implement ISSUE-11: Full test suite for accounts, orders, inventory, delivery
  ├── Clean up ISSUE-22 & ISSUE-24: Dynamic category views and unified URL routing
  └── Resolve ISSUE-12: Refactor inventory to support multi-hub warehouses
```
