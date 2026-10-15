import logging
import traceback
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpRequest

from apps.users.models import ActivityLog, ErrorLog

User = get_user_model()
logger = logging.getLogger(__name__)


def log_exception_to_db(
    exc: Exception,
    model_name: Optional[str] = None,
    user: Optional[Any] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    view_name: Optional[str] = None,
) -> None:
    """
    Safely log an exception to the ErrorLog model with full traceback and context.
    Never raises; logs internal failures to Python logging.
    """
    try:
        # Generate full traceback
        error_message = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
        if len(error_message) > 10000:
            error_message = error_message[:10000] + "... [TRUNCATED]"

        # Use atomic to avoid partial writes (though not critical for logs)
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
        # Fallback to standard logging
        logger.error(
            "Failed to log exception to DB: %s | Original error: %s",
            log_exc,
            str(exc),
            exc_info=True,
        )


def log_activity_to_db(
    request: HttpRequest = None,
    user=None,
    email_or_username: str = None,
    activity_type: str = None,
    is_successful: bool = True,
    failure_reason: str = None,
    extra_data: dict = None,
):
    """
    Log user activity in a safe, decoupled way.
    """
    try:
        ip_address = None
        user_agent = ""
        path = ""
        http_method = ""

        if request:
            # Get IP (handle proxies)
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0].strip()
            else:
                ip_address = request.META.get("REMOTE_ADDR")
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
            path = request.path[:500]
            http_method = request.method

        ActivityLog.objects.create(
            user=user,
            email_or_username=email_or_username or (user.username if user else ""),
            activity_type=activity_type,
            ip_address=ip_address,
            user_agent=user_agent,
            path=path,
            http_method=http_method,
            is_successful=is_successful,
            failure_reason=failure_reason or "",
        )
    except Exception as e:
        # Fallback to standard logging
        logger.error("Failed to log activity: %s", e)
