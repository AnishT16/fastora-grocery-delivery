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
    return render(request, 'accounts/profile.html')


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
    if zone:
        tomorrow = timezone.localdate() + timedelta(days=1)
        slots = get_available_slots(zone.id, target_date=tomorrow)

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'addresses': addresses,
        'zone': zone,
        'slots': slots,
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
    return render(request, 'orders/order_detail.html', {'order': order})
