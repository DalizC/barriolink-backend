"""ViewSets para Facilities."""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.models import Facility
from .serializers import FacilitySerializer
from .permissions import IsAdminOrReadOnly


class FacilityPagination(PageNumberPagination):
    """Paginación para facilities."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(tags=['Facilities'])
class FacilityViewSet(viewsets.ModelViewSet):
    """ViewSet para listar, crear y gestionar facilities.

    - GET (list/retrieve): público
    - POST: solo administradores
    - PUT/PATCH/DELETE: solo administradores
    """
    serializer_class = FacilitySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = FacilityPagination

    def get_queryset(self):
        # Single-tenant simplificado
        tenant_id = 1
        if self.request.user.is_authenticated and self.request.user.tenant_id:
            tenant_id = self.request.user.tenant_id

        qs = Facility.objects.filter(tenant_id=tenant_id)

        # Filtros opcionales
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(description__icontains=search)
        capacity_min = self.request.query_params.get('capacity_min')
        if capacity_min:
            qs = qs.filter(capacity__gte=capacity_min)
        capacity_max = self.request.query_params.get('capacity_max')
        if capacity_max:
            qs = qs.filter(capacity__lte=capacity_max)
        active = self.request.query_params.get('is_active')
        if active in ('true', 'false'):
            qs = qs.filter(is_active=(active == 'true'))

        order = self.request.query_params.get('order')
        if order in ('name', '-name', 'capacity', '-capacity'):
            qs = qs.order_by(order)
        else:
            qs = qs.order_by('name')
        return qs

    @extend_schema(parameters=[
        OpenApiParameter('search', str, description='Buscar por nombre o descripción'),
        OpenApiParameter('capacity_min', int, description='Capacidad mínima'),
        OpenApiParameter('capacity_max', int, description='Capacidad máxima'),
        OpenApiParameter('is_active', str, description='Filtrar por estado (true/false)'),
        OpenApiParameter('order', str, description='Ordenar por: name,-name,capacity,-capacity'),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        tenant_id = self.request.user.tenant_id if (self.request.user.is_authenticated and self.request.user.tenant_id) else 1
        serializer.save(tenant_id=tenant_id, user=self.request.user)
