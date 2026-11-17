from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import MembershipPlan
from .serializers import (
    MembershipPlanSerializer,
    CustomerMembershipSerializer,
    SubscribeMembershipSerializer,
)
from .services import (
    subscribe_user_to_plan,
    get_user_membership_status,
)


class MembershipPlanListView(APIView):
    # Lists available membership plans
    permission_classes = [AllowAny]

    def get(self, request):
        plans = MembershipPlan.objects.filter(is_active=True).order_by('price')
        serializer = MembershipPlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscribeMembershipView(APIView):
    # Subscribes authenticated user to a selected membership plan
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubscribeMembershipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_id = serializer.validated_data['plan_id']
        membership = subscribe_user_to_plan(user=request.user, plan_id=plan_id)

        output_serializer = CustomerMembershipSerializer(membership)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class MembershipStatusView(APIView):
    # Returns membership status and active plan details for the user
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_user_membership_status(request.user)
        return Response(data, status=status.HTTP_200_OK)
