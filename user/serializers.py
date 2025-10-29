"""Serializer para el modelo de usuario."""
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo de usuario."""
    class Meta:
        model = get_user_model()
        fields = ('email', 'name', 'password', 'role')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 5
            },
            'role': {'read_only': True},
        }

    def create(self, validated_data):
        """Crear y retornar un nuevo usuario con contraseña cifrada."""
        # Asegurar que el rol asignado por defecto sea 'registered'
        validated_data.pop('role', None)
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Actualizar usuario, cifrando la contraseña si se proporciona."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer para autenticar usuarios y crear tokens."""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        """Validar y autenticar el usuario."""
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            msg = _('No se pudo autenticar con las credenciales proporcionadas.')
            raise serializers.ValidationError(msg, code='authorization')
        if not user.is_active:
            msg = _('El usuario está deshabilitado.')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """Serializer para que administradores actualicen el rol de un usuario."""
    class Meta:
        model = get_user_model()
        fields = ('role',)

    def validate_role(self, value):
        """Validar que el rol proporcionado sea válido."""
        role_values = {choice[0] for choice in get_user_model().Role.choices}
        if value not in role_values:
            raise serializers.ValidationError('El rol especificado no es válido.')
        return value
