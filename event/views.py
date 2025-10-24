"""
Vistas para la API de eventos.
"""
from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication
from drf_spectacular.utils import extend_schema

from core.models import Event
from .serializers import EventSerializer


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permiso: lectura pública, escritura solo por propietario autenticado."""

    def has_permission(self, request, view):
        # Lectura pública
        if request.method in permissions.SAFE_METHODS:
            return True
        # Escritura requiere autenticación
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Lectura pública
        if request.method in permissions.SAFE_METHODS:
            return True
        # Solo el propietario puede modificar/eliminar
        return obj.user == request.user


@extend_schema(tags=['Event'])
class EventViewSet(viewsets.ModelViewSet):
    """ViewSet para listar, crear y gestionar eventos.

    - GET (list/retrieve): público
    - POST: usuarios autenticados
    - PUT/PATCH/DELETE: solo propietario
    """
    queryset = Event.objects.all().order_by('-id')
    serializer_class = EventSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        """Devolver el queryset apropiado.

        - Para lista: si está autenticado, limitar a eventos del usuario; si no, todos los eventos
        - Para operaciones de detalle: siempre devolver todos para que los permisos manejen el acceso
        """
        user = getattr(self.request, 'user', None)

        # Solo filtrar por usuario en la acción 'list'
        if self.action == 'list' and user and user.is_authenticated:
            return Event.objects.filter(user=user).order_by('-id')

        # Para retrieve, update, delete: devolver todos los eventos
        # Los permisos (IsOwnerOrReadOnly) manejarán el acceso apropiado
        return Event.objects.all().order_by('-id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
