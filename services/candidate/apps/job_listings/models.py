from django.db import models
from common_utils.models.mixins import BaseTimeStampModelMixin


class JobListing(BaseTimeStampModelMixin):
    """
    Local read-model of jobs.

    Populated and kept in sync by consuming Kafka events
    published by the recruiter service. Candidates browse
    this table directly — no cross-service HTTP call needed.
    """

    class Status(models.TextChoices):
        PUBLISHED = "PUBLISHED", "Published"
        CLOSED    = "CLOSED",    "Closed"
        ARCHIVED  = "ARCHIVED",  "Archived"

    # job_id is the PK from the recruiter service's DB
    job_id   = models.CharField(max_length=64, unique=True, db_index=True)
    title    = models.CharField(max_length=255)
    company  = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    job_type = models.CharField(max_length=50,  blank=True, null=True)
    status   = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PUBLISHED,
        db_index=True,
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'job_listings_joblisting'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} @ {self.company} [{self.status}]"
