"""
Serializers para la API de noticias.
"""
from rest_framework import serializers

from core.models import News, Category


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para el modelo Category."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class NewsSerializer(serializers.ModelSerializer):
    """Serializer para el modelo News."""

    author_name = serializers.CharField(
        source='author.name',
        read_only=True
    )
    author_id = serializers.IntegerField(
        source='author.id',
        read_only=True
    )
    categories_detail = CategorySerializer(
        source='categories',
        many=True,
        read_only=True
    )

    class Meta:
        model = News
        fields = [
            'id',
            'tenant',
            'author_id',
            'author_name',
            'title',
            'content',
            'summary',
            'link',
            'cover_image',
            'status',
            'categories',
            'categories_detail',
            'published_at',
            'published_by',
            'archived_at',
            'archived_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'tenant',
            'author_id',
            'author_name',
            'published_at',
            'published_by',
            'archived_at',
            'archived_by',
            'created_at',
            'updated_at',
        ]


class NewsDetailSerializer(NewsSerializer):
    """Serializer detallado para noticias con información completa."""

    published_by_name = serializers.CharField(
        source='published_by.name',
        read_only=True,
        allow_null=True
    )
    archived_by_name = serializers.CharField(
        source='archived_by.name',
        read_only=True,
        allow_null=True
    )

    class Meta(NewsSerializer.Meta):
        fields = NewsSerializer.Meta.fields + [
            'published_by_name',
            'archived_by_name',
        ]