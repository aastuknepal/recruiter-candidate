from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.users.views import (
    ChangeLogsViewSet,
    ErrorLogsViewSet,
    ActivityLogsViewSet,
    RoleViewSet,
    PermissionViewSet,
    SelfDetailFetchAPI,
    UserViewSet,
    ProfileDetailsApi,
)

router = DefaultRouter()
router.register("profile", UserViewSet, basename="user-profile")
router.register("roles", RoleViewSet, basename="role")
router.register("permissions", PermissionViewSet, basename="permission")
router.register("logs/change", ChangeLogsViewSet, basename="change-log")
router.register("logs/error", ErrorLogsViewSet, basename="error-log")
router.register("logs/activity", ActivityLogsViewSet, basename="activity-log")

urlpatterns = [
    path("self/", SelfDetailFetchAPI.as_view(), name="self-detail"),
    path("profile/me/", ProfileDetailsApi.as_view(), name="profile-detail"),

]

urlpatterns += router.urls
