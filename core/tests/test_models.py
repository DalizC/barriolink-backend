"""
Tests para Models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model


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
