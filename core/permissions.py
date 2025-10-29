"""
Permisos personalizados relacionados a los roles de usuario.
"""
from rest_framework import permissions


class IsMemberUser(permissions.BasePermission):
    """Permite acceso solo a usuarios con rol de miembro o administrador."""

    message = 'Se requiere rol de miembro para realizar esta acción.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_member


class IsAdminRoleUser(permissions.BasePermission):
    """Permite acceso únicamente a usuarios con rol administrador."""

    message = 'Se requiere rol de administrador para realizar esta acción.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_admin


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permite acceso al propietario del objeto o a usuarios administradores.

    Implementa `has_object_permission` para controlar acceso a nivel de objeto
    (por ejemplo: editar o eliminar recursos). Si el objeto tiene un campo
    `user` que representa su propietario, se compara con `request.user`.
    """

    message = 'Se requiere ser el propietario del recurso o administrador.'

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Permite siempre a los administradores
        if getattr(request.user, 'is_admin', False):
            return True

        # Si el objeto tiene atributo `user`, comparar.
        owner = getattr(obj, 'user', None)
        return owner == request.user
