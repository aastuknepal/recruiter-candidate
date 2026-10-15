import logging
from rest_framework import viewsets, status
from rest_framework.response import Response

from apps.applications.models import Application
from apps.applications.serializers import ApplicationSerializer
from apps.kafka_app.producer import publish
from shared.kafka.topics import KafkaTopics

logger = logging.getLogger(__name__)


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    Candidate applies for / withdraws from a job.

    On create  → publishes  candidate.application.submitted
    On destroy → publishes  candidate.application.withdrawn
    """

    serializer_class = ApplicationSerializer

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user)

    def perform_create(self, serializer):
        application = serializer.save(candidate=self.request.user)
        self._publish_application_event(
            KafkaTopics.APPLICATION_SUBMITTED, application
        )

    def perform_destroy(self, instance):
        self._publish_application_event(
            KafkaTopics.APPLICATION_WITHDRAWN, instance
        )
        instance.delete(user=self.request.user)  # soft delete

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _publish_application_event(topic: str, application: Application) -> None:
        try:
            publish(
                topic=topic,
                key=str(application.id),
                payload={
                    "application_id": str(application.id),
                    "job_id":         application.job_id,
                    "candidate_id":   str(application.candidate_id),
                    "applied_at":     application.created_at.isoformat(),
                },
            )
        except Exception as exc:
            logger.error(
                "Failed to publish Kafka event topic=%s application_id=%s: %s",
                topic, application.id, exc,
            )
