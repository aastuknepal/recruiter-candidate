from django.db import models
from django.conf import settings
from common_utils.models.mixins import BaseTimeStampModelMixin


class CandidateProfile(BaseTimeStampModelMixin):
    """
    Extended profile for a candidate user.

    On save → publishes  candidate.profile.updated  to notify recruiter.
    """

    class ExperienceLevel(models.TextChoices):
        ENTRY  = "ENTRY",  "Entry Level"
        MID    = "MID",    "Mid Level"
        SENIOR = "SENIOR", "Senior Level"
        LEAD   = "LEAD",   "Lead / Principal"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='candidate_profile',
    )
    headline        = models.CharField(max_length=255, blank=True, null=True)
    bio             = models.TextField(blank=True, null=True)
    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        null=True,
        blank=True,
    )
    skills          = models.JSONField(default=list, blank=True)   # ["Python", "Django", ...]
    resume_url      = models.URLField(blank=True, null=True)
    linkedin_url    = models.URLField(blank=True, null=True)
    github_url      = models.URLField(blank=True, null=True)
    is_open_to_work = models.BooleanField(default=True)

    class Meta:
        db_table = 'profiles_candidateprofile'

    def __str__(self):
        return f"Profile({self.user.username})"
