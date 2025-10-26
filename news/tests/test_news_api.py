"""
Test para la API de noticias.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import News

from news.serializers import NewsSerializer


NEWS_URL = reverse('news:news-list')


class PrivateNewsApiTests(TestCase):
    """Pruebas de API de noticias privadas (autenticadas)."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def create_news(user, **params):
        """Crear y retornar una noticia de prueba."""
        defaults = {
            'title': 'Noticia de prueba',
            'content': 'Contenido de la noticia de prueba',
            'published': False,
            'link': 'http://example.com/noticia-prueba',
        }
        defaults.update(params)
        return News.objects.create(author=user, **defaults)


class PublicNewsApiTests(TestCase):
    """Pruebas de API de noticias públicas (sin autenticar)."""

    def setUp(self):
        self.client = APIClient()

    def test_retrieve_news_public(self):
        """Prueba que las noticias son públicas y accesibles sin autenticación."""
        # Por ahora comentamos hasta crear las URLs
        # res = self.client.get(NEWS_URL)
        # self.assertEqual(res.status_code, status.HTTP_200_OK)
        pass