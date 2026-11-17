from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from .models import Inventory
from .serializers import InventorySerializer, InventoryStockUpdateSerializer


class IsStoreOperatorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and (
                request.user.role in ['store_operator', 'admin', 'dispatcher'] or request.user.is_staff
            )
        )


class InventoryListView(APIView):
    # list inventory items and stock levels
    permission_classes = [IsStoreOperatorOrAdmin]

    def get(self, request):
        queryset = Inventory.objects.select_related('product', 'product__category').all()
        status_filter = request.query_params.get('status')
        location = request.query_params.get('location_id')

        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        if location:
            queryset = queryset.filter(location_id=location)

        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InventoryDetailUpdateView(APIView):
    # update stock quantity or price
    permission_classes = [IsStoreOperatorOrAdmin]

    def get(self, request, product_id):
        try:
            inv = Inventory.objects.select_related('product', 'product__category').get(product_id=product_id)
        except Inventory.DoesNotExist:
            return Response({'error': f"Inventory for product #{product_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = InventorySerializer(inv)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, product_id):
        serializer = InventoryStockUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        delta = serializer.validated_data['quantity_delta']
        new_price = serializer.validated_data.get('price')

        with transaction.atomic():
            try:
                inv = Inventory.objects.select_for_update().get(product_id=product_id)
            except Inventory.DoesNotExist:
                return Response({'error': f"Inventory for product #{product_id} not found."}, status=status.HTTP_404_NOT_FOUND)

            new_qty = inv.quantity_available + delta
            if new_qty < 0:
                return Response({
                    'error': f"Cannot reduce stock below zero. Current available: {inv.quantity_available}."
                }, status=status.HTTP_400_BAD_REQUEST)

            inv.quantity_available = new_qty
            if new_price is not None:
                inv.price = new_price
            inv.sync_status()
            inv.save()

        return Response({
            'message': f"Stock for '{inv.product.name}' updated successfully.",
            'inventory': InventorySerializer(inv).data
        }, status=status.HTTP_200_OK)
