import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.jobs.models import Job
from apps.jobs.serializers import JobSerializer
from apps.kafka_app.producer import publish
from shared.kafka.topics import KafkaTopics

logger = logging.getLogger(__name__)


class JobViewSet(viewsets.ModelViewSet):
    """
    CRUD for Job postings.

    On create  → publishes  recruiter.job.posted
    On update  → publishes  recruiter.job.updated
    On destroy → publishes  recruiter.job.closed  (soft delete)
    """

    queryset         = Job.objects.all()
    serializer_class = JobSerializer

    def perform_create(self, serializer):
        job = serializer.save(created_by=self.request.user)
        self._publish_job_event(KafkaTopics.JOB_POSTED, job)

    def perform_update(self, serializer):
        job = serializer.save(updated_by=self.request.user)
        self._publish_job_event(KafkaTopics.JOB_UPDATED, job)

    def perform_destroy(self, instance):
        instance.status = Job.Status.CLOSED
        instance.save()
        self._publish_job_event(KafkaTopics.JOB_CLOSED, instance)
        instance.delete(user=self.request.user)  # soft delete

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """POST /jobs/{id}/archive/ — manually archive a job."""
        job = self.get_object()
        job.status = Job.Status.ARCHIVED
        job.save()
        self._publish_job_event(KafkaTopics.JOB_ARCHIVED, job)
        return Response({'detail': 'Job archived.'}, status=status.HTTP_200_OK)

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _publish_job_event(topic: str, job: Job) -> None:
        try:
            publish(
                topic=topic,
                key=str(job.id),
                payload={
                    "job_id":      str(job.id),
                    "title":       job.title,
                    "company":     job.company_name,
                    "location":    job.location,
                    "job_type":    job.job_type,
                    "status":      job.status,
                    "expires_at":  job.expires_at.isoformat() if job.expires_at else None,
                    "posted_at":   job.created_at.isoformat(),
                },
            )
        except Exception as exc:
            # Never let a Kafka failure break the HTTP response
            logger.error("Failed to publish Kafka event topic=%s job_id=%s: %s", topic, job.id, exc)
