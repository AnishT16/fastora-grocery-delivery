from django.urls import path
from .views import (
    AdminDeliveryBatchListView,
    AdminRunBatchMatchingView,
    AdminReleaseBatchView,
    AdminMetricsReportView,
)

urlpatterns = [
    path('delivery-batches/', AdminDeliveryBatchListView.as_view(), name='api_admin_batches'),
    path('delivery-batches/run-matching/', AdminRunBatchMatchingView.as_view(), name='api_admin_run_matching'),
    path('delivery-batches/<int:pk>/release/', AdminReleaseBatchView.as_view(), name='api_admin_release_batch'),
    path('reports/metrics/', AdminMetricsReportView.as_view(), name='api_admin_metrics'),
]
