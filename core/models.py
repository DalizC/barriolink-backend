"""
Modelos de la base datos.
"""
import uuid
import os

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from django.utils import timezone

from .validators import validate_national_id_format


def news_image_file_path(instance, filename):
    """Generar ruta de archivo para imagen de noticia con UUID."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads','news', filename)

def event_image_file_path(instance, filename):
    """Generar ruta de archivo para imagen de noticia con UUID."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads','events', filename)

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
    slug = models.SlugField(max_length=255, blank=True, help_text='Slug autogenerado a partir del nombre')
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)
    capacity = models.IntegerField()
    is_active = models.BooleanField(default=True)
    amenities = models.TextField(blank=True, help_text='Lista libre de comodidades, una por línea')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Facility'
        verbose_name_plural = 'Facilities'
        ordering = ['name']
        unique_together = ('tenant', 'slug')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            self.slug = slugify(self.name)[:255]
        super().save(*args, **kwargs)


class Event(models.Model):
    """Modelo de Evento o actividad comunitaria."""

    class Status(models.TextChoices):
        PENDING = ('pending', 'Pendiente de aprobación')
        SCHEDULED = ('scheduled', 'Programado')
        CANCELLED = ('cancelled', 'Cancelado')
        COMPLETED = ('completed', 'Completado')

    class RecurrenceType(models.TextChoices):
        NONE = ('none', 'Evento único')
        DAILY = ('daily', 'Diaria')
        WEEKLY = ('weekly', 'Semanal')
        MONTHLY = ('monthly', 'Mensual')
        QUARTERLY = ('quarterly', 'Trimestral')
        SEMESTRAL = ('semestral', 'Semestral')
        YEARLY = ('yearly', 'Anual')

    class MonthlyMode(models.TextChoices):
        DAY_OF_WEEK = ('day_of_week', 'Mantener día de la semana')
        DAY_OF_MONTH = ('day_of_month', 'Mantener fecha fija')

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
        help_text='Usuario creador del evento'
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, help_text='Slug autogenerado a partir del título')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=event_image_file_path, blank=True, null=True, help_text='Imagen representativa del evento')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text='Estado del evento (PENDING requiere aprobación de admin)'
    )
    is_active = models.BooleanField(default=True, help_text='Si el evento está activo/visible')
    is_public = models.BooleanField(default=True, help_text='Si el evento es público o privado')
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

    # Fecha y hora (timezone-aware para manejo correcto de horario de verano)
    start_datetime = models.DateTimeField(
        help_text='Fecha y hora de inicio del evento'
    )
    end_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha y hora de fin del evento (opcional para eventos sin hora de fin definida)'
    )

    # Recurrencia
    recurrence_type = models.CharField(
        max_length=20,
        choices=RecurrenceType.choices,
        default=RecurrenceType.NONE,
        help_text='Tipo de recurrencia del evento'
    )
    recurrence_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Número de ocurrencias por periodo (ej: 2 veces a la semana)'
    )
    recurrence_end_date = models.DateField(
        null=True,
        blank=True,
        help_text='Fecha hasta la cual se repite el evento (solo si tiene recurrencia)'
    )
    recurrence_interval = models.IntegerField(
        default=1,
        help_text='Intervalo de recurrencia (ej: cada 2 semanas)'
    )
    recurrence_days_of_week = models.CharField(
        max_length=20,
        blank=True,
        help_text='Días de la semana para recurrencia semanal (ej: "1,3,5" para L-M-V)'
    )
    recurrence_times = models.JSONField(
        null=True,
        blank=True,
        help_text='Horarios individuales por ocurrencia: [{"day": 2, "start_time": "18:00", "end_time": "20:00"}, ...]'
    )
    recurrence_monthly_mode = models.CharField(
        max_length=20,
        choices=MonthlyMode.choices,
        null=True,
        blank=True,
        help_text='Para recurrencia mensual: mantener día de la semana o fecha fija'
    )

    # Configuración de inscripciones
    requires_registration = models.BooleanField(
        default=False,
        help_text='Si el evento requiere inscripción previa'
    )
    registration_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha límite para inscribirse (si no se especifica, hasta el inicio del evento)'
    )
    auto_confirm_registration = models.BooleanField(
        default=True,
        help_text='Si True: confirmación automática. Si False: requiere aprobación manual'
    )
    members_only = models.BooleanField(
        default=False,
        help_text='Si True: solo usuarios con rol member pueden inscribirse'
    )

    # Configuración de pagos (preparado para futuro)
    has_cost = models.BooleanField(
        default=False,
        help_text='Si el evento tiene costo (futuro: integración de pagos)'
    )
    cost_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Monto del evento (0 = gratuito)'
    )
    cost_currency = models.CharField(
        max_length=3,
        default='CLP',
        help_text='Moneda (CLP, USD, etc.)'
    )

    capacity = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-start_datetime']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        unique_together = ('tenant', 'slug')
        constraints = [
            models.CheckConstraint(
                check=Q(end_datetime__isnull=True) | Q(end_datetime__gt=F('start_datetime')),
                name='event_end_after_start',
            ),
            models.CheckConstraint(
                check=Q(facility__isnull=True) | Q(end_datetime__isnull=False),
                name='event_facility_requires_end_datetime',
            ),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            self.slug = slugify(self.title)[:255]
        super().save(*args, **kwargs)

    def clean(self):
        """Validar reglas de negocio del evento."""
        from django.core.exceptions import ValidationError
        from datetime import datetime, timedelta, time
        super().clean()

        # Validar que eventos con facility tengan end_datetime
        if self.facility and not self.end_datetime:
            raise ValidationError({
                'end_datetime': 'Los eventos que usan una instalación deben tener hora de fin definida.'
            })

        # Validar que end_datetime > start_datetime
        if self.end_datetime and self.end_datetime <= self.start_datetime:
            raise ValidationError({
                'end_datetime': 'La fecha/hora de fin debe ser posterior al inicio.'
            })

        # Validar conflictos de facility (solo para eventos confirmados/programados)
        if self.facility and self.end_datetime and self.status in [self.Status.PENDING, self.Status.SCHEDULED]:
            self._validate_facility_conflicts()

    def _validate_facility_conflicts(self):
        """Validar que no haya conflictos de horario en la facility."""
        from django.core.exceptions import ValidationError
        from datetime import datetime, timedelta, time

        # Generar todas las ocurrencias del evento actual
        my_occurrences = self._generate_occurrences_for_validation()

        # Buscar eventos potencialmente conflictivos en la misma facility
        # Rango amplio para capturar eventos periódicos
        search_start = self.start_datetime.date()
        search_end = self.recurrence_end_date if self.recurrence_end_date else (self.start_datetime + timedelta(days=365)).date()

        conflicting_events = Event.objects.filter(
            facility=self.facility,
            status__in=[self.Status.PENDING, self.Status.SCHEDULED],
            start_datetime__date__lte=search_end,
        ).exclude(pk=self.pk)

        # Para eventos periódicos, también filtrar por recurrence_end_date
        from django.db.models import Q
        conflicting_events = conflicting_events.filter(
            Q(recurrence_type='none', start_datetime__date__gte=search_start) |
            Q(recurrence_end_date__gte=search_start) |
            Q(recurrence_end_date__isnull=True, start_datetime__date__lte=search_end)
        )

        # Verificar cada evento conflictivo
        for other_event in conflicting_events:
            other_occurrences = other_event._generate_occurrences_for_validation()

            # Comparar cada par de ocurrencias
            for my_occ in my_occurrences:
                for other_occ in other_occurrences:
                    # Verificar si las ocurrencias se solapan
                    if self._check_overlap(my_occ, other_occ):
                        raise ValidationError({
                            'facility': f'Conflicto de horario con "{other_event.title}" el {other_occ["date"].strftime("%d/%m/%Y")} '
                                       f'({other_occ["start_time"]} - {other_occ["end_time"]}). '
                                       f'Tu evento: {my_occ["start_time"]} - {my_occ["end_time"]}.'
                        })

    def _generate_occurrences_for_validation(self, max_days=365):
        """Generar lista de ocurrencias para validación de conflictos.

        Returns:
            List[dict]: Lista de ocurrencias con formato:
                {
                    'date': datetime.date,
                    'start_time': 'HH:MM',
                    'end_time': 'HH:MM',
                    'start_datetime': datetime,
                    'end_datetime': datetime
                }
        """
        from datetime import datetime, timedelta, time
        occurrences = []

        # Evento único
        if self.recurrence_type == self.RecurrenceType.NONE:
            occurrences.append({
                'date': self.start_datetime.date(),
                'start_time': self.start_datetime.strftime('%H:%M'),
                'end_time': self.end_datetime.strftime('%H:%M'),
                'start_datetime': self.start_datetime,
                'end_datetime': self.end_datetime
            })
            return occurrences

        # Evento periódico con horarios específicos en recurrence_times
        if self.recurrence_times:
            current_date = self.start_datetime.date()
            end_limit = self.recurrence_end_date if self.recurrence_end_date else (current_date + timedelta(days=max_days))

            while current_date <= end_limit:
                # Para eventos semanales, verificar si el día de la semana coincide
                if self.recurrence_type == self.RecurrenceType.WEEKLY:
                    weekday = current_date.weekday()
                    # Buscar en recurrence_times si hay un horario para este día
                    for rec_time in self.recurrence_times:
                        if rec_time.get('day') == weekday:
                            start_time_str = rec_time.get('start_time', '00:00')
                            end_time_str = rec_time.get('end_time', '23:59')

                            # Parsear horarios
                            start_hour, start_min = map(int, start_time_str.split(':'))
                            end_hour, end_min = map(int, end_time_str.split(':'))

                            start_dt = datetime.combine(current_date, time(start_hour, start_min))
                            end_dt = datetime.combine(current_date, time(end_hour, end_min))

                            occurrences.append({
                                'date': current_date,
                                'start_time': start_time_str,
                                'end_time': end_time_str,
                                'start_datetime': start_dt,
                                'end_datetime': end_dt
                            })

                current_date += timedelta(days=1)

        # Evento periódico sin horarios específicos (usar start_datetime y end_datetime base)
        else:
            current_date = self.start_datetime.date()
            end_limit = self.recurrence_end_date if self.recurrence_end_date else (current_date + timedelta(days=max_days))
            base_start_time = self.start_datetime.time()
            base_end_time = self.end_datetime.time()

            while current_date <= end_limit:
                # Aplicar lógica de recurrencia
                if self.recurrence_type == self.RecurrenceType.DAILY:
                    should_include = True
                elif self.recurrence_type == self.RecurrenceType.WEEKLY:
                    # Verificar días de la semana
                    if self.recurrence_days_of_week:
                        weekdays = [int(d) for d in self.recurrence_days_of_week.split(',')]
                        should_include = current_date.weekday() in weekdays
                    else:
                        should_include = current_date.weekday() == self.start_datetime.weekday()
                else:
                    should_include = True

                if should_include:
                    start_dt = datetime.combine(current_date, base_start_time)
                    end_dt = datetime.combine(current_date, base_end_time)

                    occurrences.append({
                        'date': current_date,
                        'start_time': base_start_time.strftime('%H:%M'),
                        'end_time': base_end_time.strftime('%H:%M'),
                        'start_datetime': start_dt,
                        'end_datetime': end_dt
                    })

                current_date += timedelta(days=1)

        return occurrences

    def _check_overlap(self, occ1, occ2):
        """Verificar si dos ocurrencias se solapan en fecha y hora.

        Args:
            occ1, occ2: Diccionarios con 'date', 'start_datetime', 'end_datetime'

        Returns:
            bool: True si hay solapamiento
        """
        # Deben ser el mismo día
        if occ1['date'] != occ2['date']:
            return False

        # Verificar solapamiento de horarios
        return (occ1['start_datetime'] < occ2['end_datetime'] and
                occ1['end_datetime'] > occ2['start_datetime'])

    @property
    def has_capacity_limit(self):
        return self.capacity is not None

    @property
    def duration(self):
        """Calcula la duración del evento en segundos."""
        if not self.end_datetime:
            return None
        delta = self.end_datetime - self.start_datetime
        return int(delta.total_seconds())

    @property
    def is_multi_day(self):
        """Retorna True si el evento dura más de un día."""
        if not self.end_datetime:
            return False
        return self.end_datetime.date() > self.start_datetime.date()

    @property
    def is_recurring(self):
        """Retorna True si el evento tiene recurrencia."""
        return self.recurrence_type != self.RecurrenceType.NONE

    @property
    def confirmed_registrations_count(self):
        """Número de inscripciones confirmadas."""
        return self.registrations.filter(status=EventRegistration.Status.CONFIRMED).count()

    @property
    def available_spots(self):
        """Cupos disponibles (None si no hay límite)."""
        if not self.capacity:
            return None
        return max(0, self.capacity - self.confirmed_registrations_count)

    @property
    def is_full(self):
        """True si el evento está lleno."""
        if not self.capacity:
            return False
        return self.confirmed_registrations_count >= self.capacity

    @property
    def registration_is_open(self):
        """True si las inscripciones están abiertas."""
        if not self.requires_registration:
            return False
        if self.is_full:
            return False
        if self.registration_deadline and timezone.now() > self.registration_deadline:
            return False
        return True

    @property
    def confirmed_registrations_count(self):
        """Número de inscripciones confirmadas."""
        return self.registrations.filter(status='confirmed').count()

    @property
    def available_spots(self):
        """Cupos disponibles (None si no hay límite)."""
        if not self.capacity:
            return None
        return max(0, self.capacity - self.confirmed_registrations_count)

    @property
    def is_full(self):
        """True si el evento está lleno."""
        if not self.capacity:
            return False
        return self.confirmed_registrations_count >= self.capacity

    @property
    def registration_is_open(self):
        """True si las inscripciones están abiertas."""
        if not self.requires_registration:
            return False
        if self.is_full:
            return False
        if self.registration_deadline and timezone.now() > self.registration_deadline:
            return False
        return True


class EventRegistration(models.Model):
    """Inscripción de un usuario a un evento."""

    class Status(models.TextChoices):
        PENDING = ('pending', 'Pendiente de confirmación')
        CONFIRMED = ('confirmed', 'Confirmada')
        CANCELLED = ('cancelled', 'Cancelada')
        WAITLIST = ('waitlist', 'Lista de espera')

    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='event_registrations',
        null=True,
        blank=True,
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_registrations',
        help_text='Usuario inscrito al evento'
    )

    # Datos adicionales del participante (opcional, para futuro)
    participant_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Nombre del participante (si difiere del usuario)'
    )
    participant_email = models.EmailField(
        blank=True,
        help_text='Email de contacto del participante'
    )
    participant_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Teléfono de contacto'
    )

    # Estado y metadata
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    notes = models.TextField(
        blank=True,
        help_text='Notas adicionales o comentarios'
    )

    # Campos para futuro (pagos)
    amount_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Monto a pagar (0 = gratuito) - preparado para futuro'
    )

    # Tracking
    registered_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha de confirmación'
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_registrations',
        help_text='Usuario que confirmó la inscripción (si fue manual)'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-registered_at']
        verbose_name = 'Event Registration'
        verbose_name_plural = 'Event Registrations'
        unique_together = ('event', 'user')  # Un usuario no puede inscribirse dos veces
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.event.title} ({self.get_status_display()})'

    def clean(self):
        """Validar reglas de negocio de inscripción."""
        from django.core.exceptions import ValidationError
        super().clean()

        # Validar que el evento requiera inscripción
        if not self.event.requires_registration:
            raise ValidationError('Este evento no requiere inscripción.')

        # Validar que las inscripciones estén abiertas
        if not self.event.registration_is_open and not self.pk:
            if self.event.is_full:
                raise ValidationError('El evento está lleno.')
            if self.event.registration_deadline and timezone.now() > self.event.registration_deadline:
                raise ValidationError('El plazo de inscripción ha terminado.')

        # Validar members_only
        if self.event.members_only and not self.user.is_member:
            raise ValidationError('Este evento es solo para miembros.')

    def save(self, *args, **kwargs):
        # Auto-confirmar si el evento lo permite
        if not self.pk and self.event.auto_confirm_registration:
            if not self.event.is_full:
                self.status = self.Status.CONFIRMED
                self.confirmed_at = timezone.now()
            else:
                # Si está lleno, ir a lista de espera
                self.status = self.Status.WAITLIST

        # Copiar monto del evento si no está definido
        if not self.amount_due and self.event.has_cost:
            self.amount_due = self.event.cost_amount

        super().save(*args, **kwargs)

    def confirm(self, confirmed_by=None):
        """Confirmar la inscripción manualmente."""
        if self.event.is_full and self.status != self.Status.CONFIRMED:
            raise ValidationError('El evento está lleno, no se puede confirmar.')

        self.status = self.Status.CONFIRMED
        self.confirmed_at = timezone.now()
        self.confirmed_by = confirmed_by
        self.save(update_fields=['status', 'confirmed_at', 'confirmed_by', 'updated_at'])

    def cancel(self, reason=''):
        """Cancelar la inscripción."""
        self.status = self.Status.CANCELLED
        if reason:
            self.notes = f'{self.notes}\nCancelado: {reason}' if self.notes else f'Cancelado: {reason}'
        self.save(update_fields=['status', 'notes', 'updated_at'])


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
        # TODO: Analizar si STATUS requiere publicación programada (en el futuro)
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='news'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    # Categorías
    categories = models.ManyToManyField(
        'Category',
        blank=True,
        related_name='news_items'
    )

    # Contenido
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    summary = models.CharField(max_length=300, blank=True)  # TODO: Generar el resumen automáticamente

    link = models.URLField(blank=True)  # TODO: Será necesario?
    image = models.ImageField(upload_to=news_image_file_path, blank=True, null=True)
    cover_image = models.URLField(blank=True)  # TODO: Cambiar de URLField a ImageField o FileField. post-MVP

    # Estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # Publicación
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='published_news'
    )

    # Archivado
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='archived_news'
    )

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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


class Category(models.Model):
    """
    Categoría para Noticias y Eventos.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='categories'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name