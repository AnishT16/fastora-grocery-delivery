from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # App APIs and views
    path('api/', include('apps.accounts.urls_api')),
    path('api/', include('apps.products.urls')),
    path('api/admin/', include('apps.delivery.urls_admin')),
    path('api/cart/', include('apps.carts.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/payment/', include('apps.payment.urls')),
    path('api/payments/', include('apps.payment.urls')),
    path('api/membership/', include('apps.memberships.urls')),
    path('api/delivery/', include('apps.delivery.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('delivery/', include('apps.delivery.urls')),
    path('accounts/', include('apps.accounts.urls')),

    # Frontend Storefront & Category pages
    path('', views.indexfile, name='indexfile'),
    path('beauty/', views.beauty, name='beauty'),
    path('electronics/', views.electronics, name='electronics'),
    path('gifting/', views.gifting, name='gifting'),
    path('kids/', views.kids, name='kids'),
    path('pharmacy/', views.pharmacy, name='pharmacy'),
    path('meat/', views.meat, name='meat'),
    path('fruits/', views.fruits, name='fruits'),
    path('Grocery/', views.Grocery, name='Grocery'),
    path('profile/', views.profile, name='profile'),
    path('search/', views.search, name='search'),

    # Cart, Checkout & Orders
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.orders_view, name='orders'),
    path('orders/<int:pk>/', views.order_detail_view, name='order_detail'),
]
