from django.shortcuts import render
from apps.products.models import Product, Category


def indexfile(request):
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True).select_related('category')
    return render(request, 'index.html', {'categories': categories, 'products': products})


def beauty(request):
    products = Product.objects.filter(category__slug='beauty', is_active=True)
    return render(request, 'products/beauty.html', {'products': products})


def electronics(request):
    products = Product.objects.filter(category__slug='electronics', is_active=True)
    return render(request, 'products/electronics.html', {'products': products})


def gifting(request):
    products = Product.objects.filter(category__slug='gifting', is_active=True)
    return render(request, 'products/gifting.html', {'products': products})


def kids(request):
    products = Product.objects.filter(category__slug='kids', is_active=True)
    return render(request, 'products/kids.html', {'products': products})


def pharmacy(request):
    products = Product.objects.filter(category__slug='pharmacy', is_active=True)
    return render(request, 'products/pharmacy.html', {'products': products})


def meat(request):
    products = Product.objects.filter(category__slug='meat', is_active=True)
    return render(request, 'products/meat.html', {'products': products})


def fruits(request):
    products = Product.objects.filter(category__slug='fruits', is_active=True)
    return render(request, 'products/fruits.html', {'products': products})


def Grocery(request):
    products = Product.objects.filter(category__slug='groceries', is_active=True)
    return render(request, 'products/Grocery.html', {'products': products})


def profile(request):
    return render(request, 'accounts/profile.html')


def search(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        results = Product.objects.filter(
            name__icontains=query,
            is_active=True
        ).select_related('category')

    return render(request, 'search.html', {
        'query': query,
        'results': results
    })
