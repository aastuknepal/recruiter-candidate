from django.urls import path, include
from drf_spectacular.views import (
    SpectacularRedocView,
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from django.contrib import admin

urlpatterns = [
    # Docs URLs
    path(
        "redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]