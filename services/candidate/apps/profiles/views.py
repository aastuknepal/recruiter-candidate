import logging
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.profiles.models import CandidateProfile
from apps.profiles.serializers import CandidateProfileSerializer
from apps.kafka_app.producer import publish
from shared.kafka.topics import KafkaTopics

logger = logging.getLogger(__name__)


class CandidateProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /profiles/me/  — fetch your profile
    PUT  /profiles/me/  — update your profile (publishes Kafka event)
    PATCH /profiles/me/ — partial update
    """
    serializer_class = CandidateProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = CandidateProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile

    def perform_update(self, serializer):
        profile = serializer.save()
        try:
            publish(
                topic=KafkaTopics.CANDIDATE_PROFILE_UPDATED,
                key=str(profile.user_id),
                payload={
                    "candidate_id":   str(profile.user_id),
                    "updated_fields": list(serializer.validated_data.keys()),
                    "skills":         profile.skills,
                    "experience_level": profile.experience_level,
                    "is_open_to_work":  profile.is_open_to_work,
                },
            )
        except Exception as exc:
            logger.error("Failed to publish profile updated event: %s", exc)
