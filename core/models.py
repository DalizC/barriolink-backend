"""
Modelos de la base datos.
"""
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """Manager para usuarios."""

    def create_user(self, email, password=None, **extra_fields):
        """Crear, guardar y retornar un nuevo usuario."""
        if not email:
            raise ValueError('El usuario debe tener un email')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Crear y guardar un nuevo superusuario."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user

class User(AbstractBaseUser, PermissionsMixin):
    """Usuario en el sistema."""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Event(models.Model):
    """Modelo de Evento."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255)  # Nombre del lugar
    address = models.CharField(max_length=255, blank=True) # Dirección física
    address_url = models.URLField(max_length=500, blank=True, null=True)  # Link al mapa
    date = models.DateField()
    duration = models.DurationField()
    capacity = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title

class Space(models.Model):
    """Modelo de Espacio Comunitario."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)
    capacity = models.IntegerField()

    def __str__(self):
        return self.name

class News(models.Model):
    """Modelo de Noticia."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    published = models.BooleanField(default=False)
    link = models.URLField(max_length=200, blank=True)

    def __str__(self):
        return self.title

class Project(models.Model):
    """Modelo de Proyecto Comunitario."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    start_date = models.DateField()
    end_date = models.DateField()
    link = models.URLField(max_length=200, blank=True)
    stage = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name