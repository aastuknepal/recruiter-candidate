from rest_framework.routers import DefaultRouter
from apps.applications.views import ApplicationViewSet

router = DefaultRouter()
router.register('', ApplicationViewSet, basename='application')

urlpatterns = router.urls
