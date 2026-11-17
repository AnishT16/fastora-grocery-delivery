from rest_framework import viewsets, permissions
from django.db.models import Q
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductAdminSerializer,
)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductAdminSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'inventory')

        is_staff = self.request.user and self.request.user.is_staff
        include_inactive = self.request.query_params.get('include_inactive', 'false').lower() == 'true'

        if not (is_staff and include_inactive):
            queryset = queryset.filter(is_active=True)

        # search filter (?search= or ?q=)
        search_query = self.request.query_params.get('search') or self.request.query_params.get('q')
        if search_query:
            search_query = search_query.strip()
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # category filter
        category_param = self.request.query_params.get('category')
        if category_param:
            category_param = category_param.strip()
            if category_param.isdigit():
                queryset = queryset.filter(category_id=int(category_param))
            else:
                queryset = queryset.filter(category__slug=category_param)

        # in stock filter
        in_stock = self.request.query_params.get('in_stock')
        if in_stock and in_stock.lower() == 'true':
            queryset = queryset.filter(inventory__quantity_available__gt=0)

        return queryset
