from rest_framework.routers import DefaultRouter
from .views import FacilityViewSet

router = DefaultRouter()
router.register('', FacilityViewSet, basename='facility')

urlpatterns = router.urls
