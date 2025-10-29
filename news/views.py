"""
Vistas para la API de noticias.
"""
from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication
from drf_spectacular.utils import extend_schema

from core.models import News
from .serializers import NewsSerializer, NewsDetailSerializer


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
			and obj.author == request.user
		)


@extend_schema(tags=['News'])
class NewsViewSet(viewsets.ModelViewSet):
	"""ViewSet para listar, crear y gestionar noticias.

	- GET (list/retrieve): público (solo publicaciones)
	- POST: usuarios autenticados
	- PUT/PATCH/DELETE: solo autor
	"""
	queryset = News.objects.filter(published=True).order_by('-id')
	serializer_class = NewsSerializer
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthorOrReadOnly]

	def get_serializer_class(self):
		if self.action in ('retrieve',):
			return NewsDetailSerializer
		return NewsSerializer

	def perform_create(self, serializer):
		serializer.save(author=self.request.user)
