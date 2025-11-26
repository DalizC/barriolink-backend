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


class CertificateRequestSerializer(serializers.Serializer):
    """Serializer para solicitud de certificado de residencia."""

    certificate_type = serializers.ChoiceField(
        choices=[('residence', 'Certificado de Residencia')],
        default='residence'
    )
    full_name = serializers.CharField(max_length=255)
    address = serializers.CharField(max_length=500)
    email = serializers.EmailField()
    send_email = serializers.BooleanField(default=False, required=False)

    def validate_full_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('El nombre completo es requerido.')
        return value.strip()

    def validate_address(self, value):
        if not value.strip():
            raise serializers.ValidationError('La dirección es requerida.')
        return value.strip()


class CertificateResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de solicitud de certificado."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    certificate_id = serializers.IntegerField(required=False)
    pdf_url = serializers.CharField(required=False)
    email_sent = serializers.BooleanField(default=False)
