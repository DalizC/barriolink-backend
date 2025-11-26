"""
Vistas para la API de eventos.
"""
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.models import Event
from .serializers import EventSerializer, EventImageSerializer


class EventPagination(PageNumberPagination):
    """Paginación personalizada para eventos."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Permiso: lectura pública, escritura solo por autor autenticado."""

    def has_permission(self, request, view):
        # Lectura pública
        if request.method in permissions.SAFE_METHODS:
            return True
        # Escritura requiere autenticación y rol de miembro
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_member
        )

    def has_object_permission(self, request, view, obj):
        # Lectura pública
        if request.method in permissions.SAFE_METHODS:
            return True
        # Solo el autor con rol miembro puede modificar/eliminar
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_member
            and (obj.user == request.user or request.user.is_admin)
        )


@extend_schema(tags=['Events'])
class EventViewSet(viewsets.ModelViewSet):
    """ViewSet para listar, crear y gestionar eventos.

    - GET (list/retrieve): público (solo eventos activos por defecto)
    - POST: usuarios autenticados con rol miembro
    - PUT/PATCH/DELETE: solo autor o admin
    """
    serializer_class = EventSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = EventPagination

    def get_serializer_class(self):
        """Usar serializer específico para upload de imagen."""
        if self.action == 'upload_image':
            return EventImageSerializer
        return EventSerializer

    def get_queryset(self):
        """Obtener queryset filtrado según parámetros."""
        # Filtrar por tenant del usuario autenticado
        if self.request.user.is_authenticated and self.request.user.tenant:
            queryset = Event.objects.filter(tenant_id=self.request.user.tenant_id).select_related('user', 'facility')
        elif self.request.user.is_authenticated:
            # Usuario autenticado sin tenant: ver eventos sin tenant o del tenant por defecto
            queryset = Event.objects.filter(tenant_id__isnull=True).select_related('user', 'facility')
        else:
            # Usuarios no autenticados: usar tenant_id=1 por defecto
            queryset = Event.objects.filter(tenant_id=1).select_related('user', 'facility')

        # Filtro por status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filtro por is_active (por defecto solo activos para no autenticados)
        is_active = self.request.query_params.get('is_active')
        if is_active in ('true', 'false'):
            queryset = queryset.filter(is_active=(is_active == 'true'))
        elif not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)

        # Filtro por is_public
        is_public = self.request.query_params.get('is_public')
        if is_public in ('true', 'false'):
            queryset = queryset.filter(is_public=(is_public == 'true'))

        # Filtro por facility
        facility_id = self.request.query_params.get('facility')
        if facility_id:
            queryset = queryset.filter(facility_id=facility_id)

        # Filtro por organizador
        organizer_id = self.request.query_params.get('organizer')
        if organizer_id:
            queryset = queryset.filter(user_id=organizer_id)

        # Filtros por datetime de inicio (soporta fecha YYYY-MM-DD o datetime completo)
        start_from = self.request.query_params.get('start_from')
        start_to = self.request.query_params.get('start_to')
        if start_from:
            queryset = queryset.filter(start_datetime__gte=start_from)
        if start_to:
            queryset = queryset.filter(start_datetime__lte=start_to)

        # Filtros por datetime de fin
        end_from = self.request.query_params.get('end_from')
        end_to = self.request.query_params.get('end_to')
        if end_from:
            queryset = queryset.filter(end_datetime__gte=end_from)
        if end_to:
            queryset = queryset.filter(end_datetime__lte=end_to)

        # Filtro por tipo de recurrencia
        recurrence_type = self.request.query_params.get('recurrence_type')
        if recurrence_type:
            queryset = queryset.filter(recurrence_type=recurrence_type)

        # Búsqueda por título o descripción
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                title__icontains=search
            ) | queryset.filter(
                description__icontains=search
            )

        return queryset.order_by('-created_at')

    @extend_schema(
        parameters=[
            OpenApiParameter('status', str, description='Filter by status (scheduled/cancelled/completed)'),
            OpenApiParameter('is_active', str, description='Filter by active status (true/false)'),
            OpenApiParameter('is_public', str, description='Filter by public status (true/false)'),
            OpenApiParameter('facility', int, description='Filter by facility ID'),
            OpenApiParameter('author', int, description='Filter by author ID'),
            OpenApiParameter('start_from', str, description='Filter from start datetime (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'),
            OpenApiParameter('start_to', str, description='Filter to start datetime (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'),
            OpenApiParameter('end_from', str, description='Filter from end datetime (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'),
            OpenApiParameter('end_to', str, description='Filter to end datetime (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'),
            OpenApiParameter('recurrence_type', str, description='Filter by recurrence type (none/daily/weekly/biweekly/monthly/custom)'),
            OpenApiParameter('search', str, description='Search in title and description'),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Listar eventos con filtros opcionales."""
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Subir imagen de portada a evento."""
        event = self.get_object()
        serializer = self.get_serializer(
            event,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def perform_create(self, serializer):
        """Crear evento asignando autor y tenant."""
        tenant_id = self.request.user.tenant_id if self.request.user.tenant else 1
        serializer.save(
            user=self.request.user,
            tenant_id=tenant_id,
        )

    @extend_schema(
        description='Cancelar un evento (cambiar status a cancelled)',
        request=None,
        responses={200: EventSerializer}
    )
    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """Acción personalizada: cancelar evento."""
        event = self.get_object()
        event.status = Event.Status.CANCELLED
        event.save(update_fields=['status', 'updated_at'])
        serializer = self.get_serializer(event)
        return Response(serializer.data)

    @extend_schema(
        description='Completar un evento (cambiar status a completed)',
        request=None,
        responses={200: EventSerializer}
    )
    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        """Acción personalizada: completar evento."""
        event = self.get_object()
        event.status = Event.Status.COMPLETED
        event.save(update_fields=['status', 'updated_at'])
        serializer = self.get_serializer(event)
        return Response(serializer.data)
