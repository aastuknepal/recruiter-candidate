# =============================================================================
# apps/kafka_app/handlers.py  — Candidate Service
#
# Business logic for events consumed FROM the recruiter service.
# =============================================================================
import logging

logger = logging.getLogger(__name__)


def handle_event(topic: str, payload: dict) -> None:
    """Router — dispatches to the correct handler based on topic name."""
    from shared.kafka.topics import KafkaTopics

    if topic == KafkaTopics.JOB_POSTED:
        handle_job_posted(payload)

    elif topic == KafkaTopics.JOB_UPDATED:
        handle_job_updated(payload)

    elif topic == KafkaTopics.JOB_CLOSED:
        handle_job_closed(payload)

    elif topic == KafkaTopics.JOB_ARCHIVED:
        handle_job_archived(payload)

    else:
        logger.warning("Candidate: unhandled topic=%s", topic)


# ── Individual Handlers ───────────────────────────────────────────────────────

def handle_job_posted(payload: dict) -> None:
    """
    A new job was posted by the recruiter service.
    Upsert a local read-model so candidates can browse/search jobs
    without calling the recruiter service directly.

    Expected payload keys:
        job_id, title, company, location, job_type, status, expires_at, posted_at
    """
    from apps.job_listings.models import JobListing

    JobListing.objects.update_or_create(
        job_id=payload["job_id"],
        defaults={
            "title":      payload.get("title", ""),
            "company":    payload.get("company", ""),
            "location":   payload.get("location", ""),
            "job_type":   payload.get("job_type", ""),
            "status":     payload.get("status", "PUBLISHED"),
            "expires_at": payload.get("expires_at"),
        },
    )
    logger.info("Job listing upserted: job_id=%s", payload.get("job_id"))


def handle_job_updated(payload: dict) -> None:
    """Job details changed — sync the local read-model."""
    handle_job_posted(payload)  # same upsert logic


def handle_job_closed(payload: dict) -> None:
    """Job was closed — mark it in the local read-model."""
    from apps.job_listings.models import JobListing

    JobListing.objects.filter(job_id=payload["job_id"]).update(status="CLOSED")
    logger.info("Job listing closed: job_id=%s", payload.get("job_id"))


def handle_job_archived(payload: dict) -> None:
    """Job was archived — mark it in the local read-model."""
    from apps.job_listings.models import JobListing

    JobListing.objects.filter(job_id=payload["job_id"]).update(status="ARCHIVED")
    logger.info("Job listing archived: job_id=%s", payload.get("job_id"))
