from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import NewsViewSet

app_name = 'news'

router = DefaultRouter()
router.register('', NewsViewSet, basename='news')

urlpatterns = [
    path('', include(router.urls)),
]
