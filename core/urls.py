"""
URLs para la app core (categorías).
"""
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import CategoryViewSet

app_name = 'core'

router = DefaultRouter()
router.register('', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]
