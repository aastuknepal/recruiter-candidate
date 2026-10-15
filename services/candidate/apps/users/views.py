from common_utils.users.permission_mixin import ExplicitPermission
import traceback
from collections import defaultdict
from decouple import config
from rest_framework.views import APIView, PermissionDenied
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from common_utils.logs.error_log import log_activity_to_db
from common_utils.logs.filter_logs import ActivityLogFilterSet, ChangeLogFilterSet
from common_utils.pagination.default_pagination import CustomDefaultPagination
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Q
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)
from drf_spectacular.utils import extend_schema

from common_utils.response.response_mixin import ResponseHandlerMixin

from common_utils.views.base_views import AbstractViewSet
from common_utils.filtersets.filterset_backend import CustomFilterBackend
from apps.users.serializers import (
    UserSerializer,
    RoleSerializer,
    SelfDetailFetchSerializer,
    PermissionSerializer,
)
from apps.users.filters import UserFilterSet, RoleFilterSet
from apps.users.models import ActivityLog, ChangeLog, ErrorLog, Roles, Permissions, User
from apps.users.serializers.logs_serializers import ChangeLogSerializer, ErrorLogSerializer, ActivityLogSerializer

User = get_user_model()


@extend_schema(tags=["User Management"])
class RoleViewSet(AbstractViewSet):
    """
    ViewSet for managing custom Roles and assigning Permissions.
    """
    queryset = Roles.objects.all().prefetch_related('permissions')
    serializer_class = RoleSerializer
    permission_classes = [ExplicitPermission]
    filter_backends = [CustomFilterBackend]
    filterset_class = RoleFilterSet
    pagination_class = CustomDefaultPagination

    permission_map = {
        "list": "users.roles.view",
        "retrieve": "users.roles.view",
        "create": "users.roles.create",
        "update": "users.roles.edit",
        "partial_update": "users.roles.edit",
        "all_permissions": "users.roles.view",
        "search": "users.roles.search",
    }

    @action(detail=False, methods=['get'])
    def all_permissions(self, request):
        """
        Returns all system permissions grouped by module.
        Used by the frontend to build the 'Add/Edit Role' UI.
        """
        perms = Permissions.objects.all().order_by('module', 'name')

        grouped_perms = defaultdict(list)
        for p in perms:
            grouped_perms[p.module].append({
                "id": p.id,
                "name": p.name,
                "key": p.key,
                "module": p.module,
                "description": p.description
            })

        return self.success_response(grouped_perms)

    @action(
        detail=False, methods=["get"], permission_classes=[ExplicitPermission]
    )
    def search(self, request):
        """Search roles by name. Returns a list of roles matching the search term."""
        try:
            user = request.user
            if not user.is_superuser:
                user_keys=set(
                    user.roles.filter(is_active=True)
                    .values_list('permissions__key',flat=True)
                    .distinct()
                )
                if 'users.roles.search' not in user_keys:
                    raise PermissionDenied("You do not have permission to search roles")
            search = request.query_params.get("search", "").strip()
            results_qs = self.queryset.filter(
                name__icontains=search).order_by("id")[:10]
            data = self.serializer_class(results_qs, many=True).data
            return self.success_response({"results": data})
        except Exception as e:
            return self.exception_response(e)


@extend_schema(tags=["User Management"])
class PermissionViewSet(AbstractViewSet):
    """
    Simple list view for all custom permissions.
    """
    queryset = Permissions.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [ExplicitPermission]
    http_method_names = ["get"]

    permission_map = {
        "list": "users.roles.view",
        "retrieve": "users.roles.view",
    }

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            grouped_data = defaultdict(list)

            for perm in queryset:
                model_display = perm.module.replace('_', ' ').title()
                grouped_data[model_display].append(
                    {"id": perm.id, "name": perm.name, "key": perm.key,
                        "description": perm.description, "module": perm.module}
                )
            return self.success_response(grouped_data)
        except Exception as e:
            return self.exception_response(e)


@extend_schema(tags=["auth"])
class LoginView(ResponseHandlerMixin, TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email_or_username = request.data.get("email") or request.data.get("username", "")
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError, AuthenticationFailed) as exc:
            if isinstance(exc, AuthenticationFailed):
                failure_reason = str(exc.detail) if hasattr(exc, "detail") else "Invalid credentials"
            else:
                failure_reason = "Invalid payload or parameters"

            log_activity_to_db(
                request=request,
                email_or_username=email_or_username,
                activity_type="LOGIN_FAILED",
                is_successful=False,
                failure_reason=failure_reason,
            )
            return self.error_response(
                message=getattr(exc, "detail", str(exc)),
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.user

        if getattr(user, "is_deleted", False) or not user.is_active:
            log_activity_to_db(
                request=request,
                email_or_username=email_or_username,
                activity_type="LOGIN_FAILED",
                is_successful=False,
                failure_reason="Account deactivated",
            )
            return self.error_response(
                message="Your account has been deactivated. Please contact an administrator.",
                status=status.HTTP_403_FORBIDDEN,
            )

        tokens = serializer.validated_data
        access_token = tokens.get("access")
        refresh_token = tokens.get("refresh")
        access_token_expiry = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        refresh_token_expiry = settings.SIMPLE_JWT[
            "REFRESH_TOKEN_LIFETIME"
        ].total_seconds()
        cookie_domain = config("COOKIE_DOMAIN", default=None)

        log_activity_to_db(
            request=request,
            user=user,
            activity_type="LOGIN_SUCCESS",
            is_successful=True,
        )

        if isinstance(settings.DEBUG, bool) and settings.DEBUG:
            secure_status = False
            response = self.success_response(
                data=[{"access": access_token, "refresh": refresh_token}],
                message="Login successful",
                status=status.HTTP_200_OK,
            )
        else:
            secure_status = True
            response = self.success_response()

        response.set_cookie(
            domain=cookie_domain,
            key=settings.JWT_ACCESS,
            value=access_token,
            max_age=access_token_expiry,
            httponly=True,
            secure=secure_status,
        )
        response.set_cookie(
            domain=cookie_domain,
            key=settings.JWT_REFRESH,
            value=refresh_token,
            max_age=refresh_token_expiry,
            httponly=True,
            secure=secure_status,
        )
        return response
@extend_schema(tags=["auth"])
class LogoutView(ResponseHandlerMixin, APIView):
    """
    View to handle user logout and JWT token blacklisting.
    Deletes JWT tokens from HttpOnly cookies upon logout.
    """

    permission_classes = [IsAuthenticated]

    def _delete_cookie(self, response, cookie_name, domain=None, samesite=None):
        response.delete_cookie(
            key=cookie_name,
            path="/",
            domain=domain,
            samesite=samesite,
        )

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.COOKIES.get(
                settings.JWT_REFRESH
            ) or request.data.get("refresh_token")
            # access_token = request.COOKIES.get(settings.JWT_ACCESS) or request.data.get("access_token")

            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except TokenError:
                    pass  # already invalid or expired

            cookies_to_delete = {
                settings.JWT_ACCESS: {"samesite": "Lax"},
                settings.JWT_REFRESH: {"samesite": "Lax"},
                "csrftoken": {},
                "sessionid": {},
            }

            cookie_domain = config("COOKIE_DOMAIN", default=None)

            response = self.success_response(
                message="Logged out successfully",
                status=status.HTTP_200_OK,
            )

            # activity log
            log_activity_to_db(
                request=request,
                user=request.user,
                activity_type="LOGOUT",
                is_successful=True,
            )

            for cookie, options in cookies_to_delete.items():
                if cookie in request.COOKIES:
                    self._delete_cookie(
                        response,
                        cookie,
                        domain=cookie_domain,
                        samesite=options.get("samesite"),
                    )

            return response

        except Exception as e:
            traceback.print_exc()
            return self.exception_response(e)


@extend_schema(tags=["Users"])
class UserViewSet(AbstractViewSet):
    queryset = User.objects.defer(
        "password",
        "last_login",
        "created_by_id",
        "updated_by_id",
        "deleted_at",
        "created_at",
        "updated_at",
    ).prefetch_related("roles").order_by("-id")
    serializer_class = UserSerializer
    permission_classes = [ExplicitPermission]
    permission_map = {
        "list": "users.view",
        "retrieve":"users.view",
        "create": "users.create",
        "update": "users.edit",
        "partial_update": "users.edit",
        "toggle_status": "users.activate_deactivate",
    }
    pagination_class = CustomDefaultPagination
    filter_backends = [CustomFilterBackend]
    filterset_class = UserFilterSet

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)
        return queryset

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, *args, **kwargs):
        try:
            instance = self.get_object()

            if instance == request.user:
                return self.error_response(
                    message="You cannot deactivate your own account.",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            instance.is_active = not instance.is_active
            instance.save(update_fields=["is_active"])

            state = "activated" if instance.is_active else "deactivated"
            return self.success_response(
                message=f"User {state} successfully."
            )
        except Exception as e:
            return self.exception_response(e)


@extend_schema(tags=["Users"])
class SelfDetailFetchAPI(generics.ListAPIView, ResponseHandlerMixin):
    queryset = User.objects.defer(
        "password",
        "last_login",
        "created_by_id",
        "updated_by_id",
        "deleted_at",
        "created_at",
        "updated_at",
        "is_deleted",
    ).prefetch_related("roles", "roles__permissions")
    serializer_class = SelfDetailFetchSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            user = self.get_queryset().filter(id=request.user.id).first()
            if not user:
                return self.exception_response("User not found")
            serializer = self.get_serializer(user)
            return self.success_response(serializer.data)
        except Exception as e:
            return self.exception_response(e)


@extend_schema(tags=["Logs"], description="", methods=["GET"])
class ChangeLogsViewSet(AbstractViewSet):
    queryset = ChangeLog.objects.select_related("user").all().order_by("-id")
    serializer_class = ChangeLogSerializer
    permission_classes = [ExplicitPermission]
    permission_map = {"list": "setup.view.change_logs",
                      "retrieve": "setup.view.change_logs"}
    pagination_class = CustomDefaultPagination
    filter_backends = [CustomFilterBackend]
    filterset_class = ChangeLogFilterSet


@extend_schema(tags=["Logs"], description="Error Logs ViewSet", methods=["GET"])
class ErrorLogsViewSet(AbstractViewSet):
    queryset = ErrorLog.objects.select_related("user").all().order_by("-id")
    serializer_class = ErrorLogSerializer
    permission_classes = [ExplicitPermission]
    permission_map = {"list": "setup.view.error_logs",
                      "retrieve": "setup.view.error_logs"}
    pagination_class = CustomDefaultPagination
    filter_backends = [CustomFilterBackend]


@extend_schema(tags=["Logs"], description="Activity Logs ViewSet", methods=["GET"])
class ActivityLogsViewSet(AbstractViewSet):
    queryset = ActivityLog.objects.select_related("user").all().order_by("-id")
    serializer_class = ActivityLogSerializer
    permission_classes = [ExplicitPermission]
    permission_map = {"list": "setup.view.activity_logs",
                      "retrieve": "setup.view.activity_logs"}
    pagination_class = CustomDefaultPagination
    filter_backends = [CustomFilterBackend]
    filterset_class = ActivityLogFilterSet


class ProfileDetailsApi(ResponseHandlerMixin, generics.RetrieveUpdateAPIView):
    """Api for the currently logged-in user to view and update their own profile
    No id is required in the url
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Returns the currently authenticated user
        return self.request.user

    def check_permissions(self, request):
        super().check_permissions(request)
        if getattr(request.user, "is_deleted", False) or not request.user.is_active:
            self.permission_denied(
                request,
                message="Your account has been deactivated. Please contact an administrator."
            )

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        serializer.fields.pop("role_ids", None)
        return serializer

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, context={"request": request})
            return self.success_response(serializer.data)
        except Exception as e:
            return self.exception_response(e)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial, context={"request": request})
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return self.success_response(
                data=serializer.data,
                message="Profile updated successfully"
            )
        except Exception as e:
            return self.exception_response(e)
