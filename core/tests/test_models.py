"""
Tests para Models.
"""
from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


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
            date='2025-12-31',
            duration=timedelta(hours=4, minutes=30),  # 4.5 horas
        )
        self.assertEqual(str(event), event.title)

    def test_create_news(self):
        """Test crear una noticia exitosamente."""
        user = get_user_model().objects.create_user(
            email='user@example.com',
            password='Testpass123'
        )
        news = models.News.objects.create(
            title='Noticia de prueba',
            content='Contenido de la noticia',
            author=user,
            published=True,
        )
        self.assertEqual(str(news), news.title)
