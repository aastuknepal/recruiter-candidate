# =============================================================================
# apps/kafka_app/handlers.py  — Recruiter Service
#
# Business logic for events consumed FROM the candidate service.
# Each handler receives a validated payload dict.
# =============================================================================
import logging

logger = logging.getLogger(__name__)


def handle_event(topic: str, payload: dict) -> None:
    """
    Router — dispatches to the correct handler based on topic name.
    Add a new elif branch when you add a new consumed topic.
    """
    from shared.kafka.topics import KafkaTopics

    if topic == KafkaTopics.APPLICATION_SUBMITTED:
        handle_application_submitted(payload)

    elif topic == KafkaTopics.APPLICATION_WITHDRAWN:
        handle_application_withdrawn(payload)

    elif topic == KafkaTopics.CANDIDATE_PROFILE_UPDATED:
        handle_candidate_profile_updated(payload)

    else:
        logger.warning("Recruiter: unhandled topic=%s", topic)


# ── Individual Handlers ───────────────────────────────────────────────────────

def handle_application_submitted(payload: dict) -> None:
    """
    A candidate applied for a job posted by this recruiter service.
    Update the recruiter-side application count / notification.

    Expected payload keys:
        application_id, job_id, candidate_id, applied_at
    """
    logger.info(
        "Application submitted: job_id=%s candidate_id=%s",
        payload.get("job_id"),
        payload.get("candidate_id"),
    )
    # TODO: update Job.application_count, send recruiter notification, etc.


def handle_application_withdrawn(payload: dict) -> None:
    """
    A candidate withdrew their application.

    Expected payload keys:
        application_id, job_id, candidate_id
    """
    logger.info(
        "Application withdrawn: job_id=%s candidate_id=%s",
        payload.get("job_id"),
        payload.get("candidate_id"),
    )
    # TODO: decrement Job.application_count


def handle_candidate_profile_updated(payload: dict) -> None:
    """
    A candidate updated their profile.
    Recruiter may want to re-rank applicants.

    Expected payload keys:
        candidate_id, updated_fields
    """
    logger.info(
        "Candidate profile updated: candidate_id=%s fields=%s",
        payload.get("candidate_id"),
        payload.get("updated_fields"),
    )
    # TODO: trigger re-scoring / ranking pipeline
