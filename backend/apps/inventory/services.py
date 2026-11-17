from django.db import transaction
from .models import Inventory
from common.exceptions import (
    InsufficientStockError,
    ProductNotFoundError,
    InvalidQuantityError,
)


def reserve_stock(product_id, quantity, location_id=None):
    # reserve stock for checkout using row lock to avoid overselling
    if quantity <= 0:
        raise InvalidQuantityError("Quantity to reserve must be greater than zero.")

    with transaction.atomic():
        try:
            queryset = Inventory.objects.select_for_update()
            if location_id:
                inventory = queryset.get(product_id=product_id, location_id=location_id)
            else:
                inventory = queryset.get(product_id=product_id)
        except Inventory.DoesNotExist:
            raise ProductNotFoundError(f"Inventory record for product ID {product_id} does not exist.")

        if inventory.quantity_available < quantity:
            raise InsufficientStockError(
                f"Insufficient stock for '{inventory.product.name}'. "
                f"Available: {inventory.quantity_available}, Requested: {quantity}."
            )

        inventory.quantity_available -= quantity
        inventory.reserved_quantity += quantity
        inventory.sync_status()
        inventory.save(update_fields=['quantity_available', 'reserved_quantity', 'status', 'updated_at'])
        return inventory


def release_stock(product_id, quantity, location_id=None):
    # release reserved stock back when an order is cancelled
    if quantity <= 0:
        raise InvalidQuantityError("Quantity to release must be greater than zero.")

    with transaction.atomic():
        try:
            queryset = Inventory.objects.select_for_update()
            if location_id:
                inventory = queryset.get(product_id=product_id, location_id=location_id)
            else:
                inventory = queryset.get(product_id=product_id)
        except Inventory.DoesNotExist:
            raise ProductNotFoundError(f"Inventory record for product ID {product_id} does not exist.")

        release_amount = min(inventory.reserved_quantity, quantity)
        inventory.reserved_quantity -= release_amount
        inventory.quantity_available += release_amount
        inventory.sync_status()
        inventory.save(update_fields=['quantity_available', 'reserved_quantity', 'status', 'updated_at'])
        return inventory


def confirm_stock_deduction(product_id, quantity, location_id=None):
    # permanently deduct reserved stock when order is fulfilled
    if quantity <= 0:
        raise InvalidQuantityError("Quantity to deduct must be greater than zero.")

    with transaction.atomic():
        try:
            queryset = Inventory.objects.select_for_update()
            if location_id:
                inventory = queryset.get(product_id=product_id, location_id=location_id)
            else:
                inventory = queryset.get(product_id=product_id)
        except Inventory.DoesNotExist:
            raise ProductNotFoundError(f"Inventory record for product ID {product_id} does not exist.")

        deduct_amount = min(inventory.reserved_quantity, quantity)
        inventory.reserved_quantity -= deduct_amount
        inventory.sync_status()
        inventory.save(update_fields=['reserved_quantity', 'status', 'updated_at'])
        return inventory
