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
ADMIN_USERS_URL = reverse('user:admin-user-list')


def admin_user_role_url(user_id):
    """Retornar URL para actualización de rol de usuario."""
    return reverse('user:admin-user-role', args=[user_id])


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
        self.assertEqual(response.data['role'], get_user_model().Role.REGISTERED)

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
        """Prueba crear token para un usuario con rol miembro."""
        user_details = {
            'name': 'Test Name',
            'email': 'testuser@example.com',
            'password': 'test-user-pass123'
        }
        create_user(**user_details, role=get_user_model().Role.MEMBER)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_allows_registered_role(self):
        """Prueba que un usuario registrado básico puede obtener token."""
        user_details = {
            'name': 'Basic User',
            'email': 'basic@example.com',
            'password': 'basic-pass123'
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
            password='testpass123',
            role=get_user_model().Role.MEMBER,
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
                'email': self.user.email,
                'role': self.user.role,
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


class AdminUserApiTests(TestCase):
    """Pruebas para endpoints administrados por usuarios con rol admin."""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = create_user(
            name='Admin User',
            email='admin@example.com',
            password='adminpass123',
            role=get_user_model().Role.ADMIN,
        )
        self.client.force_authenticate(user=self.admin_user)
        self.target_user = create_user(
            name='Target User',
            email='target@example.com',
            password='targetpass123',
            role=get_user_model().Role.REGISTERED,
        )

    def test_admin_can_list_users(self):
        """Prueba que un administrador puede listar usuarios."""
        response = self.client.get(ADMIN_USERS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_admin_can_update_user_role(self):
        """Prueba que un administrador puede actualizar el rol de un usuario."""
        payload = {'role': get_user_model().Role.MEMBER}
        url = admin_user_role_url(self.target_user.id)

        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.role, payload['role'])

    def test_admin_cannot_set_invalid_role(self):
        """Prueba que se retorna error al asignar un rol inválido."""
        url = admin_user_role_url(self.target_user.id)
        response = self.client.patch(url, {'role': 'invalid-role'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_admin_cannot_access_admin_endpoints(self):
        """Prueba que un usuario sin rol admin no puede acceder a endpoints admin."""
        basic_user = create_user(
            name='Basic',
            email='basic-admin@example.com',
            password='basicpass123',
            role=get_user_model().Role.MEMBER,
        )
        self.client.force_authenticate(user=basic_user)

        response = self.client.get(ADMIN_USERS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
