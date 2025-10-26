"""
URLs para la API de eventos.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from event import views

router = DefaultRouter()
router.register('', views.EventViewSet, basename='event')

app_name = 'event'

urlpatterns = [
    path('', include(router.urls)),
]