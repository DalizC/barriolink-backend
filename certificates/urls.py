from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import CertificateViewSet

app_name = 'certificates'

router = DefaultRouter()
router.register('', CertificateViewSet, basename='certificate')

urlpatterns = [
    path('', include(router.urls)),
]
