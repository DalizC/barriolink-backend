"""
Django admin customization.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models


class UserAdmin(BaseUserAdmin):
    """Admin para el modelo de usuario."""
    ordering = ['email']
    list_display = ['email', 'name', 'role']
    search_fields = ['email', 'name']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            'Información Personal',
            {'fields': ('name',)}
        ),
        (
            'Permisos',
            {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}
        ),
        (
            'Fechas Importantes',
            {'fields': ('last_login',)}
        ),
    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'role', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

admin.site.register(models.User, UserAdmin)
admin.site.register(models.Event)
admin.site.register(models.News)
admin.site.register(models.Facility)
