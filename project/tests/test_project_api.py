"""
Tests para la API de proyectos.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Project

from project.serializers import ProjectSerializer, ProjectDetailSerializer


PROJECTS_URL = reverse('project:project-list')


def detail_url(project_id):
    """Crear y retornar la URL de detalle del proyecto."""
    return reverse('project:project-detail', args=[project_id])


def create_project(user, **params):
    """Crear y retornar un proyecto de prueba."""
    defaults = {
        'name': 'Proyecto de prueba',
        'description': 'Descripción del proyecto de prueba',
        'active': True,
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',
        'link': 'http://example.com/proyecto-prueba',
    }
    defaults.update(params)
    return Project.objects.create(user=user, **defaults)

class PublicProjectApiTests(TestCase):
    """Pruebas de API de proyectos públicas (sin autenticar)."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Prueba que la autenticación es requerida para acceder a proyectos."""
        res = self.client.get(PROJECTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateProjectApiTests(TestCase):
    """Pruebas de API de proyectos privadas (autenticadas)."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass',
            role=get_user_model().Role.MEMBER,
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_projects(self):
        """Prueba recuperar una lista de proyectos."""
        create_project(user=self.user)
        create_project(user=self.user, name='Otro proyecto')

        res = self.client.get(PROJECTS_URL)

        projects = Project.objects.all().order_by('-id')
        serializer = ProjectSerializer(projects, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_project_list_limited_to_user(self):
        """Prueba que la lista de proyectos está limitada al usuario autenticado."""
        other_user = get_user_model().objects.create_user(
            'other@example.com',
            'testpass'
        )
        create_project(user=other_user)
        create_project(user=self.user)

        res = self.client.get(PROJECTS_URL)

        projects = Project.objects.filter(user=self.user).order_by('-id')
        serializer = ProjectSerializer(projects, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_project_detail(self):
        """Prueba obtener el detalle de un proyecto."""
        project = create_project(user=self.user)

        url = detail_url(project.id)
        res = self.client.get(url)

        serializer = ProjectDetailSerializer(project)
        self.assertEqual(res.data, serializer.data)

    def test_registered_user_cannot_access_projects(self):
        """Prueba que un usuario registrado básico no puede acceder a los proyectos."""
        basic_user = get_user_model().objects.create_user(
            'registered@example.com',
            'testpass',
            role=get_user_model().Role.REGISTERED,
        )
        self.client.force_authenticate(user=basic_user)

        res = self.client.get(PROJECTS_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
