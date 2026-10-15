from rest_framework.routers import DefaultRouter
from apps.job_listings.views import JobListingViewSet

router = DefaultRouter()
router.register('', JobListingViewSet, basename='job-listing')

urlpatterns = router.urls
