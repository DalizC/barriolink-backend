"""
Modelos de la base datos.
"""
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from django.utils import timezone

from .validators import validate_national_id_format


class Tenant(models.Model):
    """Modelo de Barrio/Comunidad (organización multi-tenant)."""
    name = models.CharField(max_length=255, help_text='Nombre del barrio o junta de vecinos')
    national_id = models.CharField(
        max_length=50,
        blank=True,
        help_text='RUT, Tax ID, o identificador nacional',
        validators=[validate_national_id_format],
    )
    slug = models.SlugField(unique=True, help_text='Identificador único en URL')
    address = models.CharField(max_length=500, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return self.name


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

    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='users',
        help_text='Barrio/Comunidad al que pertenece el usuario',
        null=True,
        blank=True,
    )
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    national_id = models.CharField(
        max_length=50,
        blank=True,
        help_text='RUT, DNI, o identificador nacional',
        validators=[validate_national_id_format],
    )
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


class Facility(models.Model):
    """Modelo de Espacio Comunitario (instalación gestionada)."""

    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='facilities',
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)
    capacity = models.IntegerField()

    class Meta:
        verbose_name = 'Facility'
        verbose_name_plural = 'Facilities'
        ordering = ['name']

    def __str__(self):
        return self.name


class Event(models.Model):
    """Modelo de Evento o actividad comunitaria."""

    class Status(models.TextChoices):
        SCHEDULED = ('scheduled', 'Programado')
        CANCELLED = ('cancelled', 'Cancelado')
        COMPLETED = ('completed', 'Completado')

    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    is_public = models.BooleanField(default=True)
    facility = models.ForeignKey(
        'Facility',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text='Ubicación personalizada cuando no se usa una instalación administrada.',
    )
    address = models.CharField(max_length=255, blank=True)
    address_url = models.URLField(max_length=500, blank=True, null=True)
    date = models.DateField()
    duration = models.DurationField()
    capacity = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'title']

    def __str__(self):
        return self.title

    @property
    def has_capacity_limit(self):
        return self.capacity is not None


class Booking(models.Model):
    """Reserva de una instalación para un bloque de tiempo."""

    class Status(models.TextChoices):
        CONFIRMED = ('confirmed', 'Confirmada')
        PENDING = ('pending', 'Pendiente')
        CANCELLED = ('cancelled', 'Cancelada')

    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
        blank=True,
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name='bookings',
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
        blank=True,
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_bookings',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_at']
        constraints = [
            models.CheckConstraint(
                check=Q(end_at__gt=F('start_at')),
                name='booking_end_after_start',
            ),
        ]

    def __str__(self):
        return f'{self.facility.name} ({self.start_at} - {self.end_at})'

    def clean(self):
        super().clean()
        if self.end_at <= self.start_at:
            raise ValidationError('La hora de término debe ser posterior al inicio.')

        if self.status == self.Status.CANCELLED:
            return

        overlap_qs = Booking.objects.filter(
            facility=self.facility,
            status__in=[self.Status.CONFIRMED, self.Status.PENDING],
        ).exclude(pk=self.pk).filter(
            Q(start_at__lt=self.end_at) &
            Q(end_at__gt=self.start_at)
        )

        if overlap_qs.exists():
            raise ValidationError('La instalación ya está reservada en el horario solicitado.')

    def cancel(self, by_user=None, reason=''):
        """Cancelar la reserva."""
        self.status = self.Status.CANCELLED
        if reason:
            self.notes = f'{self.notes}\nCancelado: {reason}' if self.notes else f'Cancelado: {reason}'
        if by_user:
            self.notes = f'{self.notes}\nAcción por: {by_user.email}' if self.notes else f'Acción por: {by_user.email}'
        self.save(update_fields=['status', 'notes', 'updated_at'])

class News(models.Model):
    """Modelo de Noticia."""
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='news',
        null=True,
        blank=True,
    )
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
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='projects',
        null=True,
        blank=True,
    )
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


class Certificate(models.Model):
    """Modelo de Certificado emitido para un usuario.

    Actualmente solo se usa para certificados de residencia.
    """

    class Status(models.TextChoices):
        ACTIVE = ('active', 'Activo')
        EXPIRED = ('expired', 'Expirado')
        REVOKED = ('revoked', 'Revocado')

    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='certificates',
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='certificates/', blank=True, null=True)
    issued_at = models.DateField()
    expires_at = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Campos legacy para potencial almacenamiento futuro (no usados en on-demand):
    pdf_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    pdf_generated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-issued_at', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def pdf_bytes(self) -> tuple[bytes, str]:
        """Renderizar el PDF en memoria y retornar (bytes, file_name).

        Implementación on-demand: no se persiste en disco ni en FileField.
        """
        try:
            from certificates.services import generate_certificate_pdf_bytes
        except ImportError:
            raise RuntimeError('Servicio de generación de PDF no disponible.')

        return generate_certificate_pdf_bytes(self)

    def generate_pdf(self, force=False):
        """[DEPRECADO] Mantenido por compatibilidad. Genera el PDF en memoria.

        Retorna bytes del PDF. No guarda archivo. El parámetro force no tiene efecto.
        """
        pdf_bytes, _ = self.pdf_bytes()
        return pdf_bytes
