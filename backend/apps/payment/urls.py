from django.urls import path
from .views import (
    PaymentCreateView,
    PaymentVerificationWebhookView,
    PaymentWebhookView,
    PaymentRefundView,
    CODCollectionConfirmView,
    PaymentConfigView,
)

urlpatterns = [
    path('create/', PaymentCreateView.as_view(), name='payment-create'),
    path('verify/', PaymentVerificationWebhookView.as_view(), name='payment-verify'),
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    path('refund/', PaymentRefundView.as_view(), name='payment-refund'),
    path('cod-collect/', CODCollectionConfirmView.as_view(), name='payment-cod-collect'),
    path('config/', PaymentConfigView.as_view(), name='payment-config'),
]
