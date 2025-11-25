"""Serializers para el módulo de Facilities."""
from rest_framework import serializers
from core.models import Facility


class FacilitySerializer(serializers.ModelSerializer):
    """Serializer para el modelo Facility."""

    tenant_id = serializers.IntegerField(
        source='tenant.id',
        read_only=True
    )
    author_id = serializers.IntegerField(
        source='user.id',
        read_only=True
    )
    author_name = serializers.CharField(
        source='user.name',
        read_only=True
    )

    class Meta:
        model = Facility
        fields = [
            'id',
            'tenant_id',
            'author_id',
            'author_name',
            'name',
            'slug',
            'description',
            'address',
            'capacity',
            'is_active',
            'amenities',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'tenant_id',
            'author_id',
            'author_name',
            'slug',
            'created_at',
            'updated_at',
        ]
