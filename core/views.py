"""Views para modelos core (Category)."""
from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema

from .models import Category
from news.serializers import CategorySerializer


class CategoryPagination(PageNumberPagination):
    """Paginación personalizada para categorías."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(tags=['Categories'])
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para listar y obtener categorías.

    - GET (list/retrieve): público
    - Solo lectura (no permite POST/PUT/PATCH/DELETE)
    """
    serializer_class = CategorySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.AllowAny]
    pagination_class = CategoryPagination

    def get_queryset(self):
        """Obtener queryset filtrado."""
        queryset = Category.objects.filter(is_active=True)

        # Búsqueda por nombre o descripción
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                name__icontains=search
            ) | queryset.filter(
                description__icontains=search
            )

        return queryset.order_by('name')
