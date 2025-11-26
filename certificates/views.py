"""
Vistas para la API de certificados.
"""
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.renderers import BaseRenderer
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone

from core.models import Certificate
from .serializers import (
    CertificateSerializer,
    CertificateDetailSerializer,
    CertificateRequestSerializer,
    CertificateResponseSerializer
)
from .services import generate_certificate_pdf_bytes, send_certificate_email


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permite lectura a autenticados; escritura solo al propietario.

    - SAFE_METHODS: requiere autenticación.
    - Métodos de escritura: requiere autenticación y ser propietario.
    """

    def has_permission(self, request, view):
        # Requiere autenticación para todas las acciones
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return obj.user_id == getattr(request.user, 'id', None)


class PassthroughRenderer(BaseRenderer):
    """Renderer que pasa el contenido binario sin modificarlo."""
    media_type = 'application/pdf'
    format = 'pdf'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


@extend_schema(tags=['Certificates'])
class CertificateViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar certificados (privados por usuario)."""

    serializer_class = CertificateSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            return Certificate.objects.filter(user=user).order_by('-issued_at', '-created_at')
        return Certificate.objects.none()

    def get_serializer_class(self):
        if self.action in ('retrieve',):
            return CertificateDetailSerializer
        return CertificateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'], url_path='pdf', renderer_classes=[PassthroughRenderer])
    @extend_schema(
        responses={200: (OpenApiTypes.BINARY, 'application/pdf')},
        description='Genera el PDF en memoria y lo devuelve como application/pdf. Usa ?download=1 para forzar descarga.'
    )
    def pdf(self, request, pk=None):
        """Descargar o visualizar el PDF del certificado (on-demand).

        Usar query param ?download=1 para forzar descarga.
        """
        certificate = self.get_object()
        try:
            pdf_bytes, file_name = generate_certificate_pdf_bytes(certificate)
        except Exception as exc:
            return Response(
                {
                    'detail': 'No se pudo generar el PDF en el servidor. Revisa las dependencias de WeasyPrint.',
                    'error': str(exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        disposition = 'attachment' if request.query_params.get('download') else 'inline'
        resp['Content-Disposition'] = f"{disposition}; filename=\"{file_name}\""
        return resp

    @extend_schema(request={'type': 'object', 'properties': {'email': {'type': 'string'}}})
    @action(detail=True, methods=['post'], url_path='send-email')
    def send_email(self, request, pk=None):
        """Enviar el PDF del certificado por email (generado en memoria)."""
        certificate = self.get_object()
        to_email = request.data.get('email')
        if not to_email:
            return Response({'detail': 'Falta el campo email.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            send_certificate_email(certificate, to_email)
        except Exception as exc:
            return Response(
                {
                    'detail': 'No se pudo enviar el correo con el PDF. Revisa las dependencias de WeasyPrint y la configuración de email.',
                    'error': str(exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({'detail': 'Correo enviado.'})

    @extend_schema(
        request=CertificateRequestSerializer,
        responses={201: CertificateResponseSerializer}
    )
    @action(detail=False, methods=['post'], url_path='request')
    def request_certificate(self, request):
        """Solicitar y crear un certificado de residencia.

        Crea el certificado en la base de datos y opcionalmente lo envía por email.
        Retorna el ID del certificado creado y la URL para descargarlo.
        """
        serializer = CertificateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = request.user

        # Crear el certificado en la base de datos
        certificate = Certificate.objects.create(
            user=user,
            tenant=user.tenant,
            title='Certificado de Residencia',
            description=f"Certificado de residencia emitido para {data['full_name']}\nDirección: {data['address']}\nEmail de contacto: {data['email']}",
            issued_at=timezone.now().date(),
            status=Certificate.Status.ACTIVE,
        )

        # Intentar enviar por email si se solicitó
        email_sent = False
        if data.get('send_email', False):
            try:
                send_certificate_email(certificate, data['email'])
                email_sent = True
            except Exception as exc:
                # No fallar la creación si el email falla, solo registrar
                pass

        # Construir URL del PDF
        pdf_url = request.build_absolute_uri(
            f'/api/certificates/{certificate.id}/pdf/'
        )

        response_data = {
            'success': True,
            'message': 'Certificado creado exitosamente.',
            'certificate_id': certificate.id,
            'pdf_url': pdf_url,
            'email_sent': email_sent,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)
