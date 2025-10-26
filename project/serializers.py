"""
Serializadores para el modelo de Proyectos.
"""
from rest_framework import serializers

from core.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for projects."""

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'start_date', 'end_date', 'stage', 'active', 'link', 'user']
        read_only_fields = ['id', 'user']


class ProjectDetailSerializer(ProjectSerializer):
    """Serializer detallado para proyectos."""

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields
