"""
Vistas para la API de noticias.
"""
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.models import News
from .serializers import NewsImageSerializer, NewsSerializer, NewsDetailSerializer


class NewsPagination(PageNumberPagination):
    """Paginación personalizada para noticias."""
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
            and (obj.author == request.user or request.user.is_admin)
        )


@extend_schema(tags=['News'])
class NewsViewSet(viewsets.ModelViewSet):
    """ViewSet para listar, crear y gestionar noticias.

    - GET (list/retrieve): público (solo publicaciones por defecto)
    - POST: usuarios autenticados con rol miembro
    - PUT/PATCH/DELETE: solo autor o admin
    - Acciones personalizadas: publish, archive, draft
    """
    serializer_class = NewsSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = NewsPagination

    def get_queryset(self):
        """Obtener queryset filtrado según parámetros."""
        # Filtrar por tenant del usuario autenticado o usar tenant_id=1 por defecto
        if self.request.user.is_authenticated and self.request.user.tenant:
            tenant_id = self.request.user.tenant_id
        else:
            tenant_id = 1  # Default tenant para usuarios no autenticados

        queryset = News.objects.filter(tenant_id=tenant_id).prefetch_related('categories')

        # Filtro por status (por defecto solo 'published' para usuarios no autenticados)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        elif not self.request.user.is_authenticated:
            # Usuarios no autenticados solo ven publicadas
            queryset = queryset.filter(status='published')

        # Filtro por categoría
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(categories__id=category_id)

        # Filtro por autor
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        # Filtro por fecha de publicación
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(published_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(published_at__lte=date_to)

        # Búsqueda por título o contenido
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                title__icontains=search
            ) | queryset.filter(
                content__icontains=search
            )

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        """Usar serializer detallado para retrieve."""
        if self.action in ('retrieve',):
            return NewsDetailSerializer
        elif self.action == 'upload_image':
            return NewsImageSerializer

        return NewsSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter('status', str, description='Filter by status (draft/published/archived)'),
            OpenApiParameter('category', int, description='Filter by category ID'),
            OpenApiParameter('author', int, description='Filter by author ID'),
            OpenApiParameter('date_from', str, description='Filter from date (YYYY-MM-DD)'),
            OpenApiParameter('date_to', str, description='Filter to date (YYYY-MM-DD)'),
            OpenApiParameter('search', str, description='Search in title and content'),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Listar noticias con filtros opcionales."""
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Crear noticia asignando autor y tenant."""
        tenant_id = self.request.user.tenant_id if self.request.user.tenant else 1
        serializer.save(
            author=self.request.user,
            tenant_id=tenant_id,
        )

    @extend_schema(
        description='Publicar una noticia (cambiar status a published)',
        request=None,
    )

    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Subir imagen de portada a noticia."""
        news = self.get_object()
        serializer = self.get_serializer(
            news,
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

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publicar una noticia."""
        news = self.get_object()

        if news.status == 'published':
            return Response(
                {'detail': 'La noticia ya está publicada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        news.status = 'published'
        news.published_at = timezone.now()
        news.published_by = request.user
        news.save()

        serializer = self.get_serializer(news)
        return Response(serializer.data)

    @extend_schema(
        description='Archivar una noticia (cambiar status a archived)',
        request=None,
    )
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archivar una noticia."""
        news = self.get_object()

        if news.status == 'archived':
            return Response(
                {'detail': 'La noticia ya está archivada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        news.status = 'archived'
        news.archived_at = timezone.now()
        news.archived_by = request.user
        news.save()

        serializer = self.get_serializer(news)
        return Response(serializer.data)

    @extend_schema(
        description='Volver una noticia a borrador (cambiar status a draft)',
        request=None,
    )
    @action(detail=True, methods=['post'])
    def draft(self, request, pk=None):
        """Volver una noticia a borrador."""
        news = self.get_object()

        if news.status == 'draft':
            return Response(
                {'detail': 'La noticia ya está en borrador.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        news.status = 'draft'
        news.save()

        serializer = self.get_serializer(news)
        return Response(serializer.data)