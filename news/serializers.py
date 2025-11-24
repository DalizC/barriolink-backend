"""
Serializers para la API de noticias.
"""
from rest_framework import serializers

from core.models import News, Category


class NewsSerializer(serializers.ModelSerializer):
    """Serializer para el modelo News."""

    author = serializers.StringRelatedField(read_only=True)
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        required=False,
    )

    class Meta:
        model = News
        fields = ['id', 'tenant', 'title', 'content', 'author', 'published', 'link']
        read_only_fields = ['id', 'author', 'tenant']


class NewsDetailSerializer(NewsSerializer):
    """Serializer detallado para noticias."""

    pass