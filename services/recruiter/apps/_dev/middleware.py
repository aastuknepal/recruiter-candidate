from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.shortcuts import redirect
from apps.setup.utils.configurations import ConfigService

User = get_user_model()


class DevMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        token = request.COOKIES.get("dartachalani_access_token")

        request.user = None

        if token:
            try:
                access_token = AccessToken(token)
                user_id = access_token["user_id"]
                request.user = User.objects.get(id=user_id)
            except (InvalidToken, TokenError, User.DoesNotExist):
                request.user = None

        path = request.path
        redirect_url = "/dartachalani/"
        request._allow_iframe = False


        # if "/dev/" in path:
        #     if not request.user or not request.user.is_authenticated:
        #         return redirect(redirect_url)
            
        #     if "debugger" in path:
        #         allowed = ConfigService.get("allow_debug_toolbar", False)
        #         if not allowed or not request.user.has_explicit_perm("dev.view.debugger"):
        #             return redirect(redirect_url)
        #         else:
        #             request._allow_iframe = True

        #     if "swagger" in path or "redoc" in path:
        #         allowed = ConfigService.get("allow_swagger_url", False)
        #         if not allowed:
        #             return redirect(redirect_url)

        response = self.get_response(request)

        if getattr(request, "_allow_iframe", False):
            response.headers["X-Frame-Options"] = "ALLOWALL"

        return response