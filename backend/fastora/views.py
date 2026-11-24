from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from apps.accounts.models import Address
from apps.carts.services import get_or_create_cart
from apps.delivery.models import DeliveryZone
from apps.delivery.services.slot_service import get_available_slots
from apps.orders.models import Order
from apps.products.models import Product, Category


def indexfile(request):
    categories = Category.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_active=True).select_related('category', 'inventory')
    return render(request, 'index.html', {'categories': categories, 'products': products})


def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    all_categories = Category.objects.filter(is_active=True).order_by('name')

    sort = request.GET.get('sort', '').strip()
    stock_filter = request.GET.get('stock', '').strip()

    products = Product.objects.filter(category=category, is_active=True).select_related('category', 'inventory')

    if stock_filter == 'in_stock':
        products = products.filter(inventory__quantity_available__gt=0)

    if sort == 'price_low':
        products = products.order_by('inventory__price', 'name')
    elif sort == 'price_high':
        products = products.order_by('-inventory__price', 'name')
    elif sort == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-created_at')

    return render(request, 'products/category_products.html', {
        'category': category,
        'all_categories': all_categories,
        'products': products,
        'current_sort': sort,
        'current_stock_filter': stock_filter,
    })


def beauty(request):
    return category_products(request, slug='beauty')


def electronics(request):
    return category_products(request, slug='electronics')


def gifting(request):
    return category_products(request, slug='gifting')


def kids(request):
    return category_products(request, slug='kids')


def pharmacy(request):
    return category_products(request, slug='pharmacy')


def meat(request):
    return category_products(request, slug='meat')


def fruits(request):
    return category_products(request, slug='fruits')


def Grocery(request):
    return category_products(request, slug='groceries')


def profile(request):
    addresses = []
    if request.user.is_authenticated:
        addresses = Address.objects.filter(customer=request.user).order_by('-is_default', '-created_at')

    return render(request, 'accounts/profile.html', {
        'addresses': addresses,
    })


@login_required(login_url='/accounts/login/?next=/delivery/rider/')
def rider_dashboard_view(request):
    if not (request.user.role == 'delivery_partner' or request.user.is_staff or request.user.is_dispatcher()):
        return redirect('profile')

    from apps.delivery.models import DeliveryBatch
    batches = DeliveryBatch.objects.filter(
        delivery_partner=request.user
    ).exclude(
        status=DeliveryBatch.STATUS_COMPLETED
    ).select_related('zone', 'slot').prefetch_related('pooled_orders__order__customer', 'pooled_orders__order__items')

    return render(request, 'delivery/rider_dashboard.html', {
        'batches': batches,
    })


@login_required(login_url='/accounts/login/?next=/dispatcher/')
def dispatcher_dashboard_view(request):
    if not (request.user.is_dispatcher() or request.user.is_staff):
        return redirect('profile')

    from apps.delivery.models import DeliveryBatch, DeliveryPartner

    total_orders = Order.objects.count()
    delivered_orders = Order.objects.filter(status=Order.STATUS_DELIVERED).count()
    cancelled_orders = Order.objects.filter(status=Order.STATUS_CANCELLED).count()
    pooled_orders_count = Order.objects.filter(
        delivery_option__in=['scheduled_pooled', 'SCHEDULED_POOLED']
    ).count()

    pooled_rate_pct = round((pooled_orders_count / total_orders * 100), 1) if total_orders > 0 else 0.0
    cancellation_rate_pct = round((cancelled_orders / total_orders * 100), 1) if total_orders > 0 else 0.0

    active_batches = DeliveryBatch.objects.exclude(status=DeliveryBatch.STATUS_COMPLETED).count()
    pending_pooled_orders = Order.objects.filter(
        delivery_option__in=['scheduled_pooled', 'SCHEDULED_POOLED'],
        status__in=[Order.STATUS_CONFIRMED, Order.STATUS_PREPARING, Order.STATUS_READY_FOR_POOLING]
    ).exclude(pooled_order__isnull=False).count()

    available_riders = DeliveryPartner.objects.filter(availability_status=DeliveryPartner.STATUS_AVAILABLE).count()

    metrics = {
        'total_orders': total_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'pooled_orders_count': pooled_orders_count,
        'pooled_rate_pct': pooled_rate_pct,
        'cancellation_rate_pct': cancellation_rate_pct,
        'active_batches': active_batches,
        'pending_pooled_orders': pending_pooled_orders,
        'available_riders': available_riders,
    }

    batches = DeliveryBatch.objects.select_related('zone', 'slot', 'delivery_partner').prefetch_related(
        'pooled_orders__order__customer'
    ).order_by('-created_at')[:15]

    riders = DeliveryPartner.objects.select_related('user').all()

    return render(request, 'delivery/dispatcher_dashboard.html', {
        'metrics': metrics,
        'batches': batches,
        'riders': riders,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.filter(is_active=True).select_related('category', 'inventory'),
        pk=pk
    )
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).select_related('category', 'inventory').exclude(pk=product.pk)[:4]

    return render(request, 'products/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })


def search(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        results = Product.objects.filter(
            name__icontains=query,
            is_active=True
        ).select_related('category', 'inventory')

    return render(request, 'search.html', {
        'query': query,
        'results': results
    })


def cart_view(request):
    cart = get_or_create_cart(request)
    return render(request, 'cart.html', {'cart': cart})


@login_required(login_url='/accounts/login/?next=/checkout/')
def checkout_view(request):
    cart = get_or_create_cart(request)
    if cart.total_items == 0:
        return redirect('indexfile')

    addresses = Address.objects.filter(customer=request.user).order_by('-is_default', '-created_at')
    zone = DeliveryZone.objects.filter(is_active=True).first()
    slots = []
    today = timezone.localdate()
    if zone:
        # Prioritize today's 1-2 hour upcoming rolling slots
        today_slots = list(get_available_slots(zone.id, target_date=today))
        if today_slots:
            slots = today_slots[:6]
        else:
            # Fallback to tomorrow morning if past today's operational hours
            tomorrow = today + timedelta(days=1)
            slots = list(get_available_slots(zone.id, target_date=tomorrow))[:6]

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'addresses': addresses,
        'zone': zone,
        'slots': slots,
        'today': today,
    })


@login_required(login_url='/accounts/login/?next=/orders/')
def orders_view(request):
    orders = Order.objects.filter(customer=request.user).prefetch_related('items').select_related('delivery_zone', 'delivery_slot').order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})


@login_required(login_url='/accounts/login/')
def order_detail_view(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related('items').select_related('delivery_zone', 'delivery_slot', 'customer'),
        pk=pk,
        customer=request.user
    )
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'today': timezone.localdate(),
    })
