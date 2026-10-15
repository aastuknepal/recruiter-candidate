import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpRequest

from apps.users.models import ErrorLog

User = get_user_model()
logger = logging.getLogger(__name__)


# =============================================================================
# ERROR LOG  — stays in PostgreSQL (relational, needs FK to User)
# =============================================================================

def log_exception_to_db(
    exc: Exception,
    model_name: Optional[str] = None,
    user: Optional[Any] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    view_name: Optional[str] = None,
) -> None:
    """
    Safely log an exception to the PostgreSQL ErrorLog model.
    Never raises; falls back to Python logging on failure.
    """
    try:
        error_message = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
        if len(error_message) > 10000:
            error_message = error_message[:10000] + "... [TRUNCATED]"

        with transaction.atomic():
            ErrorLog.objects.create(
                error_message=error_message,
                model_name=model_name or "Unknown",
                user=user
                if user and hasattr(user, "is_authenticated") and user.is_authenticated
                else None,
                path=path[:500] if path else "",
                method=method[:10] if method else "",
                view_name=view_name[:255] if view_name else "",
            )

    except Exception as log_exc:
        logger.error(
            "Failed to log exception to DB: %s | Original error: %s",
            log_exc,
            str(exc),
            exc_info=True,
        )


# =============================================================================
# ACTIVITY LOG  — goes to MongoDB
# =============================================================================

def log_activity_to_db(
    request: HttpRequest = None,
    user=None,
    email_or_username: str = None,
    activity_type: str = None,
    is_successful: bool = True,
    failure_reason: str = None,
    extra_data: dict = None,
) -> None:
    """
    Append a user-activity record to the MongoDB ``activity_logs`` collection.

    Signature is identical to the old PostgreSQL version so all existing
    callers work without any change.

    MongoDB document shape:
    {
        "service":           "recruiter" | "candidate"   (from settings.SERVICE_NAME),
        "activity_type":     str,
        "timestamp":         datetime (UTC),
        "is_successful":     bool,
        "failure_reason":    str,
        "user_id":           int | None,
        "username":          str,
        "ip_address":        str | None,
        "user_agent":        str,
        "path":              str,
        "http_method":       str,
        "extra_data":        dict | None,
    }
    """
    try:
        ip_address  = None
        user_agent  = ""
        path        = ""
        http_method = ""

        if request:
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            ip_address = (
                x_forwarded_for.split(",")[0].strip()
                if x_forwarded_for
                else request.META.get("REMOTE_ADDR")
            )
            user_agent  = request.META.get("HTTP_USER_AGENT", "")[:500]
            path        = request.path[:500]
            http_method = request.method

        doc = {
            "service":        getattr(settings, "SERVICE_NAME", "unknown"),
            "activity_type":  activity_type,
            "timestamp":      datetime.now(tz=timezone.utc),
            "is_successful":  is_successful,
            "failure_reason": failure_reason or "",
            "user_id":        user.pk if user and hasattr(user, "pk") else None,
            "username":       email_or_username or (user.username if user else ""),
            "ip_address":     ip_address,
            "user_agent":     user_agent,
            "path":           path,
            "http_method":    http_method,
            "extra_data":     extra_data or {},
        }

        from common_utils.mongo.client import get_db
        get_db()["activity_logs"].insert_one(doc)

    except Exception as e:
        # Never let a log failure crash the request
        logger.error("Failed to log activity to MongoDB: %s", e)
