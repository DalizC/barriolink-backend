"""
Serializadores para la aplicación de eventos.
"""
from rest_framework import serializers

from core.models import Event

class EventSerializer(serializers.ModelSerializer):
    """Serializer para el modelo de evento."""
    duration = serializers.DurationField()

    class Meta:
        model = Event
        fields = [
            'id', 'user', 'title', 'description', 'location',
            'address', 'address_url', 'date', 'duration', 'capacity'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        """Crear un nuevo evento."""
        return Event.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Actualizar un evento existente."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance