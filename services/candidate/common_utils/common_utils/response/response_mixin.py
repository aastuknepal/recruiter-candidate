import traceback
from django.core.exceptions import (
    MultipleObjectsReturned, 
    ObjectDoesNotExist,
    ValidationError as DjangoValidationError,
)
from django.db import DatabaseError, IntegrityError, OperationalError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response

from ..logs.error_log import log_exception_to_db

from decouple import config as settings_config


class ResponseHandlerMixin:
    """
    Standardized response handling with intelligent error logging.
    Only logs unexpected/server-side (5xx) errors.
    """

    # Define exception → (status_code, default_message)
    # Define exception → (status_code, default_message)
    EXCEPTION_CONFIG = {
        # DRF built-ins
        DRFValidationError: (status.HTTP_400_BAD_REQUEST, "Validation Error"),
        # Django Model Validation
        DjangoValidationError: (status.HTTP_400_BAD_REQUEST, "Validation Error"),
        
        PermissionDenied: (status.HTTP_403_FORBIDDEN, "Permission Denied"),
        NotFound: (status.HTTP_404_NOT_FOUND, "Resource Not Found"),
        Http404: (status.HTTP_404_NOT_FOUND, "Resource Not Found"),
        ObjectDoesNotExist: (status.HTTP_404_NOT_FOUND, "Resource Not Found"),
        MultipleObjectsReturned: (
            status.HTTP_409_CONFLICT,
            "Multiple objects found when one was expected",
        ),
        AuthenticationFailed: (status.HTTP_401_UNAUTHORIZED, "Authentication Failed"),
        MethodNotAllowed: (status.HTTP_405_METHOD_NOT_ALLOWED, "Method Not Allowed"),
        Throttled: (status.HTTP_429_TOO_MANY_REQUESTS, "Request Throttled"),
        
        # Django DB
        IntegrityError: (status.HTTP_409_CONFLICT, "Database Integrity Error"),
        DatabaseError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Database Error"),
        OperationalError: (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Database Operational Error",
        ),
        
        # Python built-ins (5xx)
        ValueError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid Value"),
        TypeError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Type Error"),
        KeyError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Key Error"),
        IndexError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Index Error"),
        AttributeError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Attribute Error"),
    }

    def success_response(
        self,
        data=None,
        message="Success",
        status_code=status.HTTP_200_OK,
        **kwargs,
    ):
        """Return a standardized success response."""
        response_data = {"success": True, "message": message, **kwargs}
        if data is not None:
            response_data["data"] = data
        return Response(response_data, status=status_code)

    def _get_error_message(self, errors):
        """
        Extract a user-friendly error message from DRF errors.
        - If multiple errors: "Please resolve all the following {n} errors."
        - If single error: The specific error message (with field name if generic).
        """
        if not errors:
            return None

        all_messages = []

        def collect_messages(error_data, field_name=None):
            if isinstance(error_data, dict):
                for key, val in error_data.items():
                    collect_messages(val, field_name=key)
            elif isinstance(error_data, (list, tuple)):
                for val in error_data:
                    collect_messages(val, field_name=field_name)
            else:
                msg = str(error_data)
                if msg:
                    if field_name and field_name != "non_field_errors":
                        display_name = field_name.replace("_", " ").title()
                        if msg.strip().lower() in ["this field is required.", "this field may not be blank.", "this field may not be null."]:
                            msg = f"The {display_name} field is required."
                        elif not (display_name.lower() in msg.lower() or field_name.lower() in msg.lower()):
                            msg = f"{display_name}: {msg}"
                    all_messages.append(msg)

        collect_messages(errors)

        if len(all_messages) > 1:
            return f"Please resolve all the following {len(all_messages)} errors."
        elif len(all_messages) == 1:
            return all_messages[0]

        return None

    def error_response(
        self,
        errors=None,
        message="Error",
        status_code=status.HTTP_400_BAD_REQUEST,
        **kwargs,
    ):
        """Return a standardized error response."""

        # If the message is generic, try to improve it from errors
        if message in ["Error", "Validation Error"] and errors:
            improved_message = self._get_error_message(errors)
            if improved_message:
                message = improved_message

        response_data = {"success": False, "message": message, **kwargs}
        if errors is not None:
            response_data["errors"] = errors
        return Response(response_data, status=status_code)

    def exception_response(self, exc, message=None):
        """
        Handle known exceptions; log only 5xx/unhandled ones.
        """
        exc_type = type(exc)
        config = self.EXCEPTION_CONFIG.get(exc_type)

        if config:
            status_code, default_msg = config
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            default_msg = "Internal Server Error"

        # Only persist expected/unexpected SERVER-side (5xx) errors to ErrorLog.
        # Expected client errors (validation, permission, not found, auth, etc.) are not logged.
        if status_code >= 500:
            self._log_exception(exc)

        if settings_config("DEBUG") and not isinstance(exc, ValidationError):
            traceback.print_exc()

        if config:
            final_msg = message or default_msg
            errors = getattr(exc, "detail", str(exc)) if status_code < 500 else None
            return self.error_response(
                message=final_msg,
                errors=errors,
                status_code=status_code,
            )

        return self.error_response(
            message=message or "Internal Server Error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def _log_exception(self, exc):
        """Extract context and delegate to utility."""
        if not hasattr(self, "request") or self.request is None:
            return  # Skip during schema gen, etc.

        request = self.request
        user = getattr(request, "user", None)

        model_name = None
        try:
            model_name = self.get_queryset().model._meta.verbose_name.title()
        except Exception:
            model_name = "Unknown"

        log_exception_to_db(
            exc=exc,
            model_name=model_name,
            user=user,
            path=getattr(request, "path", None),
            method=getattr(request, "method", None),
            view_name=self.__class__.__name__,
        )

    def paginated_response(
        self,
        paginator,
        queryset,
        serializer_class,
        page=None,
        context=None,
        fields=None,
        exclude=None,
    ):
        """Handle paginated responses consistently using CustomPagination."""
        try:
            context = context or self.get_serializer_context()

            if page is None:
                page = paginator.paginate_queryset(
                    queryset, self.request, view=self)

            try:
                serializer = serializer_class(
                    page, fields=fields, exclude=exclude, many=True, context=context
                )
            except TypeError:
                serializer = serializer_class(page, many=True, context=context)

            paginated_response = paginator.get_paginated_response(
                serializer.data)
            return self.success_response(
                data=paginated_response.data["data"],
                message="Success",
                meta=paginated_response.data["meta"],
            )
        except Exception as exc:
            return self.exception_response(exc)
