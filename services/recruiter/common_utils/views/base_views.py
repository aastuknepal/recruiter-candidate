import traceback
from django.core.exceptions import FieldDoesNotExist
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied

from ..response.response_mixin import ResponseHandlerMixin


class AbstractViewSet(
    viewsets.ModelViewSet,
    ResponseHandlerMixin,
):
    """
    Abstract ViewSet with:
    - Standardized responses
    - Soft-delete awareness
    - Audit field injection
    - Permission-based deleted record visibility
    """

    @property
    def model_name(self):
        try:
            return self.get_queryset().model._meta.verbose_name.title()
        except Exception:
            return "Unknown"

    def handle_exception(self, exc):
        """
        Override to use standardized error response for PermissionDenied.
        Other exceptions are handled by individual action methods.
        """
        if isinstance(exc, PermissionDenied):
            self._log_exception(exc)
            return self.error_response(
                message=str(exc.detail)
                if hasattr(exc, "detail")
                else "Permission denied",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return super().handle_exception(exc)


    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())

            # Only allow pagination if requested from frontend
            use_pagination = self.pagination_class is not None and (
                "page" in request.query_params or "per_page" in request.query_params
            )
            if use_pagination:
                # Use DRF's built-in pagination flow
                page = self.paginate_queryset(queryset)
                return self.paginated_response(
                    paginator=self.paginator,
                    queryset=queryset,
                    serializer_class=self.get_serializer_class(),
                    page=page,
                    context=self.get_serializer_context(),
                )
            else:
                # No pagination; limit large result sets
                if queryset.count() > 1000:
                    return self.error_response(
                        message="Result set too large. Please use pagination.",
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    )
                serializer = self.get_serializer(queryset, many=True)
                return self.success_response(serializer.data)
        except Exception as e:
            return self.exception_response(e)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return self.success_response(
                message=f"{self.model_name} created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return self.exception_response(e)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return self.success_response(
                message=f"{self.model_name} retrieved successfully",
                data=serializer.data,
            )
        except Exception as e:
            return self.exception_response(e)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return self.success_response(
                message=f"{self.model_name} updated successfully", data=serializer.data
            )
        except Exception as e:
            return self.exception_response(e)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if hasattr(instance, "is_deleted"):
                if instance.is_deleted:
                    return self.error_response(
                        message=f"{self.model_name} is already deleted",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
                instance.delete(user=request.user)
            elif hasattr(instance, "is_active"):
                instance.is_active = False
                instance.save(update_fields=["is_active"])
            else:
                return self.error_response(
                    message=f"{self.model_name} could not be deleted"
                )
            return self.success_response(
                message=f"{self.model_name} deleted successfully",
                status_code=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return self.exception_response(e)

    def perform_create(self, serializer):
        """
        Inject 'created_by' if the model supports it and user is authenticated.
        """
        model = serializer.Meta.model
        if (
            hasattr(model, "created_by")
            and self.request.user
            and self.request.user.is_authenticated
        ):
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        """
        Inject 'updated_by' if the model supports it and user is authenticated.
        """
        model = serializer.Meta.model
        if (
            hasattr(model, "updated_by")
            and self.request.user
            and self.request.user.is_authenticated
        ):
            serializer.save(updated_by=self.request.user)
        else:
            serializer.save()
