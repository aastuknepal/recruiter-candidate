from django.conf import settings
from django.views.static import serve
from django.urls import include, path
from django.conf.urls.static import static

from apps.users.views import LoginView, LogoutView
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

raw_prefix = getattr(settings, "BASE_PREFIX", "")
prefix = raw_prefix.strip("/") if raw_prefix else ""

api_version = "v1"

api_v1_patterns = [
    path("users/",        include("apps.users.urls")),
    path("setup/",        include("apps.setup.urls")),
    path("profiles/",     include("apps.profiles.urls")),
    path("applications/", include("apps.applications.urls")),
    path("job-listings/", include("apps.job_listings.urls")),
    path("auth/login/",   LoginView.as_view(),        name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("auth/logout/",  LogoutView.as_view(),       name="logout"),
    path("swagger/schema/", SpectacularAPIView.as_view(),                              name="schema"),
    path("swagger/docs/",   SpectacularSwaggerView.as_view(url_name="schema"),        name="swagger-ui"),
]

if prefix:
    base_path = f"{prefix}/api/{api_version}"
    dev_path  = f"{prefix}/dev/{api_version}"
else:
    base_path = f"api/{api_version}"
    dev_path  = f"dev/{api_version}"

urlpatterns = [
    path(f"{dev_path}/",  include("apps._dev.urls")),
    path(f"{base_path}/", include(api_v1_patterns)),
]

urlpatterns += [
    path(
        f"{settings.MEDIA_URL.lstrip('/')}<path:path>",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
