"""
Test User API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**params):
    """Crear y retornar un nuevo usuario."""
    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):
    """Pruebas de API de usuario públicas (sin autenticar)."""
    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Prueba crear un usuario con éxito."""
        payload = {
            'name': 'Test Name',
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_user_with_email_exists_error(self):
        """Prueba error al crear usuario si el email ya existe."""
        payload = {
            'name': 'Test Name',
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }
        create_user(**payload)
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Prueba error si la contraseña es demasiado corta."""
        payload = {
            'name': 'Test Name',
            'email': 'testuser@example.com',
            'password': 'pw'
        }
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Prueba crear token para el usuario."""
        user_details = {
            'name': 'Test Name',
            'email': 'testuser@example.com',
            'password': 'test-user-pass123'
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Prueba no crear token si las credenciales son inválidas."""
        create_user(
            name='Test Name',
            email='testuser@example.com',
            password='goodpass123'
        )
        payload = {
            'email': 'testuser@example.com',
            'password': 'wrongpass123'
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Prueba no crear token si la contraseña está en blanco."""
        payload = {
            'email': 'testuser@example.com',
            'password': ''
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_retrieve_user_unauthorized(self):
        """Prueba que la autenticación es requerida para los usuarios."""
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Pruebas de API de usuario privadas (autenticadas)."""
    def setUp(self):
        self.user = create_user(
            name='Test Name',
            email='testuser@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Prueba obtener perfil de usuario para usuario autenticado."""
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                'name': self.user.name,
                'email': self.user.email
            }
        )

    def test_post_me_not_allowed(self):
        """Prueba que el POST no es permitido en la ruta me."""
        response = self.client.post(ME_URL, {})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Prueba actualizar el perfil del usuario autenticado."""
        payload = {'name': 'Updated Name', 'password': 'newpassword123'}

        response = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)