"""
Modelos de la base datos.
"""
from time import timezone
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """Manager para usuarios."""

    def create_user(self, email, password=None, **extra_fields):
        """Crear, guardar y retornar un nuevo usuario."""
        if not email:
            raise ValueError('El usuario debe tener un email')
        normalized_email = self.normalize_email(email)
        role = extra_fields.get('role', self.model.Role.REGISTERED)
        if role not in self.model.Role.values:
            raise ValueError('El rol especificado no es valido')
        extra_fields['role'] = role

        user = self.model(email=normalized_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Crear y guardar un nuevo superusuario."""
        user = self.create_user(email, password, role=self.model.Role.ADMIN)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user

class User(AbstractBaseUser, PermissionsMixin):
    """Usuario en el sistema."""
    class Role(models.TextChoices):
        REGISTERED = ('registered', 'Usuario Registrado')
        MEMBER = ('member', 'Miembro')
        ADMIN = ('admin', 'Administrador')

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.REGISTERED,
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'

    @property
    def is_member(self):
        """Retorna True si el usuario posee acceso de miembro."""
        if getattr(self, 'is_superuser', False):
            return True
        return self.role in {self.Role.MEMBER, self.Role.ADMIN}

    @property
    def is_admin(self):
        """Retorna True si el usuario posee rol administrativo."""
        if getattr(self, 'is_superuser', False):
            return True
        return self.role == self.Role.ADMIN

class Application(models.Model):
    """Modelo de Solicitud de ascenso de rol a 'Miembro'."""

    class Status(models.TextChoices):
        PENDING = ('pending', 'Pendiente')
        APPROVED = ('approved', 'Aprobada')
        REJECTED = ('rejected', 'Rechazada')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications',
    )
    admin_note = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Membership Request'
        verbose_name_plural = 'Membership Requests'

    def __str__(self):
        return f"Membership Request (user={self.user.email}, status={self.status})"

    def approve(self, reviewer):
        """Marcar la solicitud como aprobada y asignar rol MEMBER al usuario."""

        if not getattr(reviewer, 'is_admin', False):
            raise PermissionError('Only admins can approve membership requests')

        self.status = self.Status.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()

        # Cambiar rol del usuario
        user = self.user
        user.role = user.Role.MEMBER
        user.save(update_fields=['role'])

    def reject(self, reviewer, note=''):
        """Marcar la solicitud como rechazada."""

        if not getattr(reviewer, 'is_admin', False):
            raise PermissionError('Only admins can reject membership requests')

        self.status = self.Status.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        if note:
            self.admin_note = note
        self.save()


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
