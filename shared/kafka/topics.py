# =============================================================================
# shared/kafka/topics.py
#
# Single source of truth for ALL Kafka topic names used across both services.
# Both recruiter and candidate services import from here.
# =============================================================================


class KafkaTopics:
    """
    Topic naming convention:  <source-service>.<entity>.<event>

    Recruiter  →  Candidate  :  recruiter.*
    Candidate  →  Recruiter  :  candidate.*
    """

    # ── Recruiter → Candidate ─────────────────────────────────────────────────
    JOB_POSTED              = "recruiter.job.posted"
    JOB_UPDATED             = "recruiter.job.updated"
    JOB_CLOSED              = "recruiter.job.closed"
    JOB_ARCHIVED            = "recruiter.job.archived"

    # ── Candidate → Recruiter ─────────────────────────────────────────────────
    APPLICATION_SUBMITTED   = "candidate.application.submitted"
    APPLICATION_WITHDRAWN   = "candidate.application.withdrawn"
    CANDIDATE_PROFILE_UPDATED = "candidate.profile.updated"

    # ── All topics per consumer ────────────────────────────────────────────────
    RECRUITER_CONSUMES = [
        APPLICATION_SUBMITTED,
        APPLICATION_WITHDRAWN,
        CANDIDATE_PROFILE_UPDATED,
    ]

    CANDIDATE_CONSUMES = [
        JOB_POSTED,
        JOB_UPDATED,
        JOB_CLOSED,
        JOB_ARCHIVED,
    ]
