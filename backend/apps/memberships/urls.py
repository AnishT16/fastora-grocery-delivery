from django.urls import path
from .views import (
    MembershipPlanListView,
    SubscribeMembershipView,
    MembershipStatusView,
)

app_name = 'memberships'

urlpatterns = [
    path('plans/', MembershipPlanListView.as_view(), name='membership-plans'),
    path('subscribe/', SubscribeMembershipView.as_view(), name='membership-subscribe'),
    path('status/', MembershipStatusView.as_view(), name='membership-status'),
]
