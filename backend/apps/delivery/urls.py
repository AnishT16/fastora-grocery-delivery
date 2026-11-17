from django.urls import path
from .views import (
    delivery_check_view,
    DeliveryOptionsAPIView,
    DeliverySlotsAPIView,
    DeliveryFeeQuoteAPIView,
    SlotReservationAPIView,
    AdminDeliveryBatchListView,
    AdminRunBatchMatchingView,
    AdminReleaseBatchView,
    DeliveryMyBatchesView,
    DeliveryOrderStatusUpdateView,
)

urlpatterns = [
    path('check/', delivery_check_view, name='delivery_check'),
    path('options/', DeliveryOptionsAPIView.as_view(), name='api_delivery_options'),
    path('slots/', DeliverySlotsAPIView.as_view(), name='api_delivery_slots'),
    path('fee-quote/', DeliveryFeeQuoteAPIView.as_view(), name='api_delivery_quote'),
    path('slot-reservations/', SlotReservationAPIView.as_view(), name='api_slot_reservations'),
    path('my-batches/', DeliveryMyBatchesView.as_view(), name='api_delivery_my_batches'),
    path('orders/<int:pk>/status/', DeliveryOrderStatusUpdateView.as_view(), name='api_delivery_order_status'),
    path('admin/delivery-batches/', AdminDeliveryBatchListView.as_view(), name='api_delivery_admin_batches'),
    path('admin/delivery-batches/run-matching/', AdminRunBatchMatchingView.as_view(), name='api_delivery_admin_run_matching'),
    path('admin/delivery-batches/<int:pk>/release/', AdminReleaseBatchView.as_view(), name='api_delivery_admin_release_batch'),
]
