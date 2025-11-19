"""Validadores personalizados para modelos."""
from django.core.exceptions import ValidationError
import re


def validate_chilean_rut(value):
    """Validar formato y dígito verificador de RUT chileno.

    Acepta formatos: 12345678-9, 12.345.678-9, o 123456789
    """
    if not value:
        return  # Campo opcional, no validar si está vacío

    # Remover puntos y guiones
    clean_rut = value.replace('.', '').replace('-', '').strip()

    # Validar que tenga al menos 2 caracteres (número + dígito verificador)
    if len(clean_rut) < 2:
        raise ValidationError('RUT debe tener al menos 2 caracteres.')

    # Separar número y dígito verificador
    rut_body = clean_rut[:-1]
    dv = clean_rut[-1].upper()

    # Validar que el cuerpo sea numérico
    if not rut_body.isdigit():
        raise ValidationError('El RUT debe contener solo números antes del dígito verificador.')

    # Validar que el dígito verificador sea válido (0-9 o K)
    if dv not in '0123456789K':
        raise ValidationError('El dígito verificador debe ser un número del 0-9 o la letra K.')

    # Calcular dígito verificador esperado
    reversed_digits = map(int, reversed(rut_body))
    factors = [2, 3, 4, 5, 6, 7]
    s = sum(d * factors[i % 6] for i, d in enumerate(reversed_digits))
    remainder = s % 11
    expected_dv = 'K' if remainder == 10 else str(11 - remainder) if remainder > 0 else '0'

    # Validar que coincida
    if dv != expected_dv:
        raise ValidationError(f'RUT inválido. El dígito verificador debería ser {expected_dv}.')


def validate_national_id_format(value):
    """Validar formato básico de identificador nacional (RUT u otros).

    Acepta: números, puntos, guiones, letras (para dígitos verificadores).
    Mínimo 2 caracteres, máximo 50.
    """
    if not value:
        return  # Campo opcional

    # Patron: permite números, puntos, guiones y letras (case-insensitive)
    if not re.match(r'^[\d\.\-a-zA-Z]+$', value):
        raise ValidationError('El identificador nacional solo puede contener números, puntos, guiones y letras.')

    if len(value) < 2:
        raise ValidationError('El identificador nacional debe tener al menos 2 caracteres.')

    if len(value) > 50:
        raise ValidationError('El identificador nacional no puede tener más de 50 caracteres.')
