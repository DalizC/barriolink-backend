"""
Serializers para la API de noticias.
"""
from rest_framework import serializers

from core.models import News


class NewsSerializer(serializers.ModelSerializer):
    """Serializer para el modelo News."""

    author = serializers.StringRelatedField(read_only=True)
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = News
        fields = ['id', 'tenant', 'title', 'content', 'author', 'published', 'link']
        read_only_fields = ['id', 'author', 'tenant']


class NewsDetailSerializer(NewsSerializer):
    """Serializer detallado para noticias."""

    pass