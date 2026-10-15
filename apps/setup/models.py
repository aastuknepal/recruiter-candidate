"""
Blood Bank Setup Models - Master Data & Configuration

This module contains all master/reference data models for the blood bank system:
- Blood groups, component types, bag types
- Donor & donation type classifications
- Screening tests and eligibility questions
- Camp and external blood bank details
- Outsourced blood tracking
"""

from django.conf import settings
from django.db import models
from common_utils.models.mixins import (
    BaseAuditModelMixin,
    BaseTimeStampModelMixin,
    SoftDeleteModelMixin
)

class Configuration(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    name = models.CharField(
        max_length=255, help_text="Name of the configuration.")
    display_name = models.CharField(
        max_length=255, help_text="Display name of the configuration."
    )
    description = models.TextField(
        blank=True, null=True, help_text="Description of the configuration."
    )
    config_type = models.CharField(
        max_length=100, help_text="Input type of the configuration. eg. text, number"
    )
    config_key = models.CharField(
        max_length=255, unique=True, help_text="Key of the configuration.")
    value = models.CharField(
        max_length=255, help_text="Value of the configuration.")

    class Meta:
        db_table = "configuration"
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"
