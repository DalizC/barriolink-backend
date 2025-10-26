from django.test import SimpleTestCase

from app import calc

"""Unit tests for the calc module.
    Métodos de prueba. TODO: Eliminar estos metodos
    una vez se hayan implementado las pruebas reales.
"""


class CalcTests(SimpleTestCase):
    def test_add_numbers(self):
        result = calc.add(5, 7)
        self.assertEqual(result, 12)
