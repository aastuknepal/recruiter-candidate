from rest_framework.routers import DefaultRouter

from apps.setup.views import (
    ConfigurationViewSet,
)

router = DefaultRouter()
router.register("configurations", ConfigurationViewSet,
                basename="configuration")

urlpatterns = []

urlpatterns += router.urls
