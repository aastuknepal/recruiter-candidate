from django.db import models
from django.conf import settings
from common_utils.models.mixins import BaseTimeStampModelMixin, SoftDeleteModelMixin


class Application(BaseTimeStampModelMixin, SoftDeleteModelMixin):
    """
    A candidate's application for a job.

    On create  → publishes  candidate.application.submitted
    On destroy → publishes  candidate.application.withdrawn
    """

    class Status(models.TextChoices):
        PENDING   = "PENDING",   "Pending"
        REVIEWED  = "REVIEWED",  "Reviewed"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        REJECTED  = "REJECTED",  "Rejected"
        HIRED     = "HIRED",     "Hired"

    # job_id references the recruiter service's Job — no FK, just a char field
    job_id    = models.CharField(max_length=64, db_index=True)
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    cover_letter = models.TextField(blank=True, null=True)
    resume_url   = models.URLField(blank=True, null=True)
    status       = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    class Meta:
        db_table = 'applications_application'
        ordering = ['-created_at']
        unique_together = [('job_id', 'candidate')]  # one application per job per candidate

    def __str__(self):
        return f"{self.candidate.username} → job:{self.job_id} [{self.status}]"
