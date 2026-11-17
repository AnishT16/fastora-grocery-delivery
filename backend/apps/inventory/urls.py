from django.urls import path
from .views import InventoryListView, InventoryDetailUpdateView

app_name = 'inventory'

urlpatterns = [
    path('', InventoryListView.as_view(), name='inventory-list'),
    path('<int:product_id>/', InventoryDetailUpdateView.as_view(), name='inventory-detail-update'),
]
