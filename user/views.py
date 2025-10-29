"""
Vistas para la API de usuario.
"""
from django.contrib.auth import get_user_model
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from drf_spectacular.utils import extend_schema

from core.permissions import IsAdminRoleUser
from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    UserRoleUpdateSerializer,
)


@extend_schema(tags=['User'])
class CreateUserView(generics.CreateAPIView):
    """Crear un nuevo usuario."""
    serializer_class = UserSerializer
    authentication_classes = ()


@extend_schema(tags=['User'])
class CreateTokenView(ObtainAuthToken):
    """Crear un nuevo token de autenticación para el usuario."""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


@extend_schema(tags=['User'])
class ManageUserView(generics.RetrieveUpdateAPIView):
    """Gestionar el usuario autenticado."""
    serializer_class = UserSerializer
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        """Retornar el usuario autenticado."""
        return self.request.user


@extend_schema(tags=['User'])
class AdminUserListView(generics.ListAPIView):
    """Listar usuarios para administradores."""
    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsAdminRoleUser)


@extend_schema(tags=['User'])
class AdminUserRoleUpdateView(generics.UpdateAPIView):
    """Permitir a administradores actualizar el rol de un usuario."""
    serializer_class = UserRoleUpdateSerializer
    queryset = get_user_model().objects.all()
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsAdminRoleUser)
    http_method_names = ['patch']
