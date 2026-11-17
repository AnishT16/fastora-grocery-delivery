from django.db import transaction
from .models import Cart, CartItem
from apps.products.models import Product
from common.exceptions import (
    InsufficientStockError,
    ProductNotFoundError,
    InvalidQuantityError,
)


def get_or_create_cart(request):
    # get active cart for logged in user or guest session
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(customer=request.user)

        # merge guest cart if customer just logged in
        session_key = request.session.session_key
        if session_key:
            try:
                session_cart = Cart.objects.get(session_key=session_key)
                if session_cart.id != cart.id:
                    with transaction.atomic():
                        for guest_item in session_cart.items.select_related('product').all():
                            user_item, created = CartItem.objects.get_or_create(
                                cart=cart,
                                product=guest_item.product,
                                defaults={
                                    'quantity': guest_item.quantity,
                                    'unit_price_snapshot': guest_item.unit_price_snapshot,
                                }
                            )
                            if not created:
                                user_item.quantity += guest_item.quantity
                                user_item.save(update_fields=['quantity', 'updated_at'])
                        session_cart.delete()
            except Cart.DoesNotExist:
                pass

        return cart

    # guest cart using session key
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart


def add_item_to_cart(cart, product_id, quantity=1):
    # add item with stock check
    if quantity <= 0:
        raise InvalidQuantityError("Quantity must be a positive integer greater than zero.")

    try:
        product = Product.objects.select_related('inventory').get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        raise ProductNotFoundError(f"Product #{product_id} does not exist or is inactive.")

    available_stock = getattr(product, 'quantity_available', 0)
    if available_stock <= 0:
        raise InsufficientStockError(f"'{product.name}' is currently out of stock.")

    product_price = getattr(product, 'current_price', None) or getattr(product, 'price', None)
    if product_price is None:
        raise InsufficientStockError(f"'{product.name}' has no active price or inventory configured.")

    with transaction.atomic():
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                'quantity': quantity,
                'unit_price_snapshot': product_price,
            }
        )

        if not created:
            target_quantity = cart_item.quantity + quantity
            if target_quantity > available_stock:
                raise InsufficientStockError(
                    f"Cannot add {quantity} more unit(s) of '{product.name}'. "
                    f"You already have {cart_item.quantity} in cart, and only {available_stock} are available."
                )
            cart_item.quantity = target_quantity
            cart_item.unit_price_snapshot = product_price
            cart_item.save(update_fields=['quantity', 'unit_price_snapshot', 'updated_at'])
        else:
            if quantity > available_stock:
                cart_item.delete()
                raise InsufficientStockError(
                    f"Requested {quantity} unit(s) of '{product.name}', but only {available_stock} are available."
                )

        return cart_item


def update_cart_item(cart, item_id, quantity):
    # update item quantity or remove if quantity <= 0
    try:
        cart_item = cart.items.select_related('product', 'product__inventory').get(id=item_id)
    except CartItem.DoesNotExist:
        raise ProductNotFoundError(f"Cart item #{item_id} not found in this cart.")

    if quantity <= 0:
        cart_item.delete()
        return None

    product = cart_item.product
    available_stock = getattr(product, 'quantity_available', 0)
    if quantity > available_stock:
        raise InsufficientStockError(
            f"Cannot update '{product.name}' to {quantity} units. "
            f"Only {available_stock} are available in stock."
        )

    product_price = getattr(product, 'current_price', None) or getattr(product, 'price', None)
    cart_item.quantity = quantity
    if product_price is not None:
        cart_item.unit_price_snapshot = product_price
    cart_item.save(update_fields=['quantity', 'unit_price_snapshot', 'updated_at'])
    return cart_item


def remove_cart_item(cart, item_id):
    try:
        cart_item = cart.items.get(id=item_id)
        cart_item.delete()
        return True
    except CartItem.DoesNotExist:
        raise ProductNotFoundError(f"Cart item #{item_id} not found in this cart.")


def clear_cart(cart):
    cart.clear()
