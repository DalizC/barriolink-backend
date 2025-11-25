"""Serializers para el módulo de Events."""
from datetime import datetime, time
from rest_framework import serializers
from core.models import Event, Facility


class FacilityNestedSerializer(serializers.ModelSerializer):
    """Serializer anidado para Facility en Event."""

    class Meta:
        model = Facility
        fields = ['id', 'name', 'slug', 'address', 'capacity']
        read_only_fields = ['id', 'slug']


class EventSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Event."""

    tenant_id = serializers.IntegerField(
        source='tenant.id',
        read_only=True
    )
    author_id = serializers.IntegerField(
        source='user.id',
        read_only=True
    )
    author_name = serializers.CharField(
        source='user.name',
        read_only=True
    )
    facility_detail = FacilityNestedSerializer(
        source='facility',
        read_only=True
    )

    # Campos auxiliares para UI (write_only)
    start_date = serializers.DateField(write_only=True, required=False)
    start_time = serializers.TimeField(write_only=True, required=False)
    end_date = serializers.DateField(write_only=True, required=False, allow_null=True)
    end_time = serializers.TimeField(write_only=True, required=False, allow_null=True)

    # Campos computados
    duration = serializers.SerializerMethodField()
    is_recurring = serializers.BooleanField(read_only=True)
    is_multi_day = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'tenant_id',
            'author_id',
            'author_name',
            'title',
            'slug',
            'description',
            'status',
            'is_active',
            'is_public',
            'facility',
            'facility_detail',
            'location',
            'address',
            'address_url',
            # Campos reales del modelo
            'start_datetime',
            'end_datetime',
            # Campos auxiliares para UI
            'start_date',
            'start_time',
            'end_date',
            'end_time',
            'duration',
            'recurrence_type',
            'recurrence_end_date',
            'recurrence_interval',
            'recurrence_days_of_week',
            'is_recurring',
            'is_multi_day',
            'capacity',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'tenant_id',
            'author_id',
            'author_name',
            'slug',
            'duration',
            'is_recurring',
            'is_multi_day',
            'created_at',
            'updated_at',
        ]

    def get_duration(self, obj):
        """Retorna la duración en segundos."""
        return obj.duration

    def validate(self, data):
        """Validar y convertir campos de fecha/hora auxiliares a datetime."""
        # Convertir campos auxiliares (start_date + start_time) a start_datetime
        if 'start_date' in data and 'start_time' in data:
            start_dt = datetime.combine(
                data.pop('start_date'),
                data.pop('start_time')
            )
            data['start_datetime'] = start_dt

        # Convertir campos auxiliares (end_date + end_time) a end_datetime
        if 'end_date' in data or 'end_time' in data:
            end_date = data.pop('end_date', None)
            end_time = data.pop('end_time', None)

            if end_date and end_time:
                data['end_datetime'] = datetime.combine(end_date, end_time)
            elif end_date:  # Solo fecha de fin, sin hora
                # Usar mismo día hasta las 23:59:59
                data['end_datetime'] = datetime.combine(end_date, time(23, 59, 59))
            elif end_time and 'start_datetime' in data:
                # Solo hora de fin, asumir mismo día que inicio
                data['end_datetime'] = datetime.combine(
                    data['start_datetime'].date(),
                    end_time
                )

        # Validar que end_datetime sea posterior a start_datetime
        if 'start_datetime' in data and 'end_datetime' in data:
            if data['end_datetime'] and data['end_datetime'] <= data['start_datetime']:
                raise serializers.ValidationError({
                    'end_datetime': 'La fecha/hora de fin debe ser posterior al inicio.'
                })

        # Validar recurrencia
        if data.get('recurrence_type') != Event.RecurrenceType.NONE:
            start_dt = data.get('start_datetime')
            if data.get('recurrence_end_date') and start_dt:
                if data['recurrence_end_date'] < start_dt.date():
                    raise serializers.ValidationError({
                        'recurrence_end_date': 'La fecha fin de recurrencia debe ser posterior al inicio del evento.'
                    })

        return data