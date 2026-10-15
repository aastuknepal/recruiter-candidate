from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from apps.job_listings.models import JobListing
from apps.job_listings.serializers import JobListingSerializer


class JobListingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for candidates to browse jobs.
    Data is populated automatically by the Kafka consumer.
    """
    queryset = JobListing.objects.filter(status=JobListing.Status.PUBLISHED)
    serializer_class = JobListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
