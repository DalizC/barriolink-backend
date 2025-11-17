"""
vistas del API proyecto.
"""
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from drf_spectacular.utils import extend_schema

from core.models import Project
from core.permissions import IsMemberUser
from project import serializers


@extend_schema(tags=['Project'])
class ProjectViewSet(viewsets.ModelViewSet):
    """Vista para manejar proyectos en la API."""
    serializer_class = serializers.ProjectSerializer
    queryset = Project.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsMemberUser]

    def get_queryset(self):
        """Retornar proyectos para el usuario autenticado."""
        return self.queryset.filter(user=self.request.user).order_by('-id')
