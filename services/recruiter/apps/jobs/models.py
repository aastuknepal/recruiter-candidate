from django.db import models
from common_utils.models.mixins import (
    BaseTimeStampModelMixin,
    BaseAuditModelMixin,
    SoftDeleteModelMixin,
)


class Job(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    """
    A job posting created by a recruiter.

    Lifecycle:
        DRAFT → PUBLISHED → CLOSED → ARCHIVED
    """

    class Status(models.TextChoices):
        DRAFT     = "DRAFT",     "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        CLOSED    = "CLOSED",    "Closed"
        ARCHIVED  = "ARCHIVED",  "Archived"

    class JobType(models.TextChoices):
        FULL_TIME  = "FULL_TIME",  "Full Time"
        PART_TIME  = "PART_TIME",  "Part Time"
        CONTRACT   = "CONTRACT",   "Contract"
        INTERNSHIP = "INTERNSHIP", "Internship"
        FREELANCE  = "FREELANCE",  "Freelance"

    title            = models.CharField(max_length=255)
    company_name     = models.CharField(max_length=255)
    description      = models.TextField()
    requirements     = models.TextField(blank=True, null=True)
    location         = models.CharField(max_length=255, blank=True, null=True)
    job_type         = models.CharField(
        max_length=20, choices=JobType.choices, default=JobType.FULL_TIME
    )
    salary_min       = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max       = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status           = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    expires_at       = models.DateTimeField(null=True, blank=True)
    application_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'jobs_job'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} @ {self.company_name} [{self.status}]"
