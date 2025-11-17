"""
Serializers para la API de certificados.
"""
from rest_framework import serializers

from core.models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Certificate."""

    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Certificate
        fields = [
            'id', 'title', 'description', 'file', 'issued_at', 'expires_at',
            'status', 'user', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class CertificateDetailSerializer(CertificateSerializer):
    """Serializer detallado para certificados (extensible)."""

    class Meta(CertificateSerializer.Meta):
        fields = CertificateSerializer.Meta.fields
