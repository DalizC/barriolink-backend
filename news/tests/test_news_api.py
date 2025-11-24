"""
Test para la API de noticias.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from core.models import News, Tenant, Category

from news.serializers import NewsSerializer, NewsDetailSerializer


NEWS_URL = reverse('news:news-list')


def detail_url(news_id):
    """Retornar URL de detalle de noticia."""
    return reverse('news:news-detail', args=[news_id])


def publish_url(news_id):
    """Retornar URL para publicar noticia."""
    return reverse('news:news-publish', args=[news_id])


def archive_url(news_id):
    """Retornar URL para archivar noticia."""
    return reverse('news:news-archive', args=[news_id])


def draft_url(news_id):
    """Retornar URL para volver a borrador."""
    return reverse('news:news-draft', args=[news_id])


def create_user(tenant, **params):
    """Crear y retornar un nuevo usuario."""
    defaults = {
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'Test User',
    }
    defaults.update(params)
    user = get_user_model().objects.create_user(**defaults)
    user.role = 'member'
    user.tenant = tenant
    user.save()
    return user


def create_tenant(**params):
    """Obtener o crear tenant con ID=1 (tenant por defecto de la aplicación)."""
    defaults = {
        'name': 'Test Tenant',
        'slug': 'test-tenant',
    }
    defaults.update(params)
    # Obtener o crear el tenant con ID=1
    tenant, created = Tenant.objects.get_or_create(
        id=1,
        defaults=defaults
    )
    return tenant


def create_news(user, tenant, **params):
    """Crear y retornar una noticia de prueba."""
    defaults = {
        'title': 'Noticia de prueba',
        'content': 'Contenido de la noticia de prueba',
        'summary': 'Resumen de la noticia',
        'status': 'published',
        'published_at': timezone.now(),
    }
    defaults.update(params)
    return News.objects.create(author=user, tenant=tenant, **defaults)


class PublicNewsApiTests(TestCase):
    """Pruebas de API de noticias públicas (sin autenticar)."""

    def setUp(self):
        self.client = APIClient()
        self.tenant = create_tenant()
        self.user = create_user(tenant=self.tenant)

    def test_list_news_public(self):
        """Prueba que las noticias publicadas son accesibles sin autenticación."""
        create_news(self.user, self.tenant, status='published')
        create_news(self.user, self.tenant, status='published', title='Otra noticia')

        res = self.client.get(NEWS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 2)

    def test_list_news_only_published(self):
        """Prueba que solo se muestran noticias publicadas sin autenticación."""
        create_news(self.user, self.tenant, status='published')
        create_news(self.user, self.tenant, status='draft')
        create_news(self.user, self.tenant, status='archived')

        res = self.client.get(NEWS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)

    def test_retrieve_news_detail_public(self):
        """Prueba obtener detalle de noticia publicada sin autenticación."""
        news = create_news(self.user, self.tenant, status='published')

        url = detail_url(news.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer = NewsDetailSerializer(news)
        self.assertEqual(res.data, serializer.data)

    def test_create_news_unauthorized(self):
        """Prueba que usuarios no autenticados no pueden crear noticias."""
        payload = {
            'title': 'Nueva noticia',
            'content': 'Contenido de prueba',
        }

        res = self.client.post(NEWS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateNewsApiTests(TestCase):
    """Pruebas de API de noticias privadas (autenticadas)."""

    def setUp(self):
        self.client = APIClient()
        self.tenant = create_tenant()
        self.user = create_user(tenant=self.tenant)
        self.client.force_authenticate(user=self.user)

    def test_create_news(self):
        """Prueba crear una noticia autenticado."""
        payload = {
            'title': 'Nueva noticia',
            'content': 'Contenido de prueba',
            'summary': 'Resumen breve',
            'status': 'draft',
        }

        res = self.client.post(NEWS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        news = News.objects.get(id=res.data['id'])
        self.assertEqual(news.author, self.user)
        self.assertEqual(news.tenant, self.tenant)
        for key in payload.keys():
            self.assertEqual(getattr(news, key), payload[key])

    def test_update_own_news(self):
        """Prueba actualizar propia noticia."""
        news = create_news(self.user, self.tenant, status='draft')

        payload = {'title': 'Título actualizado'}
        url = detail_url(news.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        news.refresh_from_db()
        self.assertEqual(news.title, payload['title'])

    def test_cannot_update_other_user_news(self):
        """Prueba que no se puede actualizar noticia de otro usuario."""
        other_user = create_user(tenant=self.tenant, email='other@example.com')
        news = create_news(other_user, self.tenant)

        payload = {'title': 'Título modificado'}
        url = detail_url(news.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_news(self):
        """Prueba eliminar propia noticia."""
        news = create_news(self.user, self.tenant)

        url = detail_url(news.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(News.objects.filter(id=news.id).exists())

    def test_publish_news(self):
        """Prueba publicar una noticia en borrador."""
        news = create_news(
            self.user,
            self.tenant,
            status='draft',
            published_at=None
        )

        url = publish_url(news.id)
        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        news.refresh_from_db()
        self.assertEqual(news.status, 'published')
        self.assertIsNotNone(news.published_at)
        self.assertEqual(news.published_by, self.user)

    def test_archive_news(self):
        """Prueba archivar una noticia publicada."""
        news = create_news(self.user, self.tenant, status='published')

        url = archive_url(news.id)
        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        news.refresh_from_db()
        self.assertEqual(news.status, 'archived')
        self.assertIsNotNone(news.archived_at)
        self.assertEqual(news.archived_by, self.user)

    def test_draft_news(self):
        """Prueba volver una noticia a borrador."""
        news = create_news(self.user, self.tenant, status='published')

        url = draft_url(news.id)
        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        news.refresh_from_db()
        self.assertEqual(news.status, 'draft')

    def test_filter_by_status(self):
        """Prueba filtrar noticias por status."""
        create_news(self.user, self.tenant, status='draft')
        create_news(self.user, self.tenant, status='published')

        res = self.client.get(NEWS_URL, {'status': 'draft'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['results'][0]['status'], 'draft')

    def test_filter_by_category(self):
        """Prueba filtrar noticias por categoría."""
        category = Category.objects.create(name='Test Category', tenant=self.tenant)
        news = create_news(self.user, self.tenant)
        news.categories.add(category)
        create_news(self.user, self.tenant, title='Otra noticia')

        res = self.client.get(NEWS_URL, {'category': category.id})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)

    def test_search_news(self):
        """Prueba búsqueda en título y contenido."""
        create_news(self.user, self.tenant, title='Python Tutorial')
        create_news(self.user, self.tenant, title='Django Guide')
        create_news(self.user, self.tenant, title='React Basics', content='Python mention here')

        res = self.client.get(NEWS_URL, {'search': 'Python'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 2)