from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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
    path('api/delivery/', include('apps.delivery.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('delivery/', include('apps.delivery.urls')),
    path('accounts/', include('apps.accounts.urls')),

    # Frontend Storefront & Dynamic Category pages
    path('', views.indexfile, name='indexfile'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('beauty/', views.beauty, name='beauty'),
    path('electronics/', views.electronics, name='electronics'),
    path('gifting/', views.gifting, name='gifting'),
    path('kids/', views.kids, name='kids'),
    path('pharmacy/', views.pharmacy, name='pharmacy'),
    path('meat/', views.meat, name='meat'),
    path('fruits/', views.fruits, name='fruits'),
    path('Grocery/', views.Grocery, name='Grocery'),
    path('profile/', views.profile, name='profile'),
    path('delivery/rider/', views.rider_dashboard_view, name='rider_dashboard'),
    path('dispatcher/', views.dispatcher_dashboard_view, name='dispatcher_dashboard'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),

    # Cart, Checkout & Orders
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.orders_view, name='orders'),
    path('orders/<int:pk>/', views.order_detail_view, name='order_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
