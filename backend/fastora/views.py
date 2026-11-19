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
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True).select_related('category', 'inventory')
    return render(request, 'index.html', {'categories': categories, 'products': products})


def beauty(request):
    products = Product.objects.filter(category__slug='beauty', is_active=True).select_related('category', 'inventory')
    return render(request, 'products/beauty.html', {
        'products': products,
        'category_name': 'Beauty & Personal Care',
        'category_slug': 'beauty',
    })


def electronics(request):
    products = Product.objects.filter(category__slug='electronics', is_active=True).select_related('category', 'inventory')
    return render(request, 'products/electronics.html', {
        'products': products,
        'category_name': 'Electronics & Gadgets',
        'category_slug': 'electronics',
    })


def gifting(request):
    products = Product.objects.filter(category__slug='gifting', is_active=True).select_related('category', 'inventory')
    return render(request, 'products/gifting.html', {
        'products': products,
        'category_name': 'Gifts & Flowers',
        'category_slug': 'gifting',
    })


def kids(request):
    products = Product.objects.filter(category__slug='kids', is_active=True).select_related('category', 'inventory')
    return render(request, 'products/kids.html', {
        'products': products,
        'category_name': 'Baby & Kids',
        'category_slug': 'kids',
    })


def pharmacy(request):
    products = Product.objects.filter(category__slug='pharmacy', is_active=True).select_related('category', 'inventory')
    return render(request, 'products/pharmacy.html', {
        'products': products,
        'category_name': 'Pharmacy & Wellness',
        'category_slug': 'pharmacy',
    })


def meat(request):
    products = Product.objects.filter(category__slug='meat', is_active=True).select_related('category', 'inventory')
    return render(request, 'products/meat.html', {
        'products': products,
        'category_name': 'Meat & Seafood',
        'category_slug': 'meat',
    })


def fruits(request):
    products = Product.objects.filter(category__slug='fruits', is_active=True).select_related('category', 'inventory')
    return render(request, 'products/fruits.html', {
        'products': products,
        'category_name': 'Fruits & Vegetables',
        'category_slug': 'fruits',
    })


def Grocery(request):
    products = Product.objects.filter(category__slug='groceries', is_active=True).select_related('category', 'inventory')
    return render(request, 'products/Grocery.html', {
        'products': products,
        'category_name': 'Groceries & Kitchen',
        'category_slug': 'groceries',
    })


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
