from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .serializers import (
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)
from .services import (
    get_or_create_cart,
    add_item_to_cart,
    update_cart_item,
    remove_cart_item,
    clear_cart,
)


class CartDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cart = get_or_create_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        cart = get_or_create_cart(request)
        clear_cart(cart)
        return Response(
            {'message': 'Cart successfully emptied.', 'total_items': 0, 'subtotal': '0.00'},
            status=status.HTTP_200_OK
        )


class CartItemCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = get_or_create_cart(request)
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data.get('quantity', 1)

        item = add_item_to_cart(cart=cart, product_id=product_id, quantity=quantity)
        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, pk):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = get_or_create_cart(request)
        quantity = serializer.validated_data['quantity']

        item = update_cart_item(cart=cart, item_id=pk, quantity=quantity)
        if item is None:
            return Response(
                {
                    'message': f'Item #{pk} removed from cart.',
                    'cart_total_items': cart.total_items,
                    'cart_subtotal': str(cart.subtotal),
                },
                status=status.HTTP_200_OK
            )

        return Response(CartItemSerializer(item).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        cart = get_or_create_cart(request)
        remove_cart_item(cart=cart, item_id=pk)
        return Response(
            {
                'message': f'Item #{pk} removed from cart.',
                'cart_total_items': cart.total_items,
                'cart_subtotal': str(cart.subtotal),
            },
            status=status.HTTP_200_OK
        )


class CartClearView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cart = get_or_create_cart(request)
        clear_cart(cart)
        return Response(
            {'message': 'Cart cleared.', 'total_items': 0, 'subtotal': '0.00'},
            status=status.HTTP_200_OK
        )
