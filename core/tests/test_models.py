"""
Tests para Models.
"""
from unittest.mock import patch
from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from core import models

def create_user(email='user@example.com', password='Testpass123'):
    """Crea y retorna un usuario de prueba."""
    return get_user_model().objects.create_user(email, password)

class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test crear un nuevo usuario con email exitosamente."""
        email = 'test@example.com'
        password = 'Testpass123'
        user = get_user_model().objects.create_user(email=email, password=password)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))


    def test_new_user_email_normalized(self):
        """Test que el email para un nuevo usuario es normalizado."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@Example.com', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email=email, password='Testpass123')
            self.assertEqual(user.email, expected)


    def test_new_user_without_email_raises_error(self):
        """Test que al crear usuario sin email lanza error."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email=None, password='Testpass123')


    def test_create_superuser(self):
        """Test crear un nuevo superusuario."""
        user = get_user_model().objects.create_superuser(
            email='superuser@example.com',
            password='Testpass123'
        )
        self.assertEqual(user.email, 'superuser@example.com')
        self.assertTrue(user.check_password('Testpass123'))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


    def test_create_event(self):
        """Test crear un evento exitosamente."""
        user = get_user_model().objects.create_user(
            email='user@example.com',
            password='Testpass123'
        )
        event = models.Event.objects.create(
            user=user,
            title='Evento de prueba',
            description='Descripción del evento de prueba',
            location='Ubicación del evento',
            address='Calle Falsa 123',
            address_url='http://example.com/evento-prueba',
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, hours=4, minutes=30),
        )
        self.assertEqual(str(event), event.title)

    def test_create_news(self):
        """Test crear una noticia exitosamente."""
        user = get_user_model().objects.create_user(
            email='user@example.com',
            password='Testpass123'
        )
        tenant = models.Tenant.objects.create(
            name="Tenant Test",
            slug="tenant-test",
        )
        news = models.News.objects.create(
            title='Noticia de prueba',
            content='Contenido de la noticia',
            author=user,
            tenant=tenant,
            status='draft',
        )
        self.assertEqual(str(news), news.title)

    '''def test_create_tag(self):
        """Test crear una etiqueta exitosamente."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')
        self.assertEqual(str(tag), tag.name)'''

    @patch('core.models.uuid.uuid4')
    def test_news_file_name_uuid(self, mock_uuid):
        """Test generar ruta de archivo de noticia con UUID."""
        import os
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.news_image_file_path(None, 'example.jpg')
        expected_path = os.path.join('uploads', 'news', f'{uuid}.jpg')
        self.assertEqual(file_path, expected_path)
