from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import  TokenError

class JWTCookieAuthenticationBackend(JWTAuthentication):
    """
    Authenticate using JWT from cookie first, then fallback to header.
    
    """

    def authenticate(self, request):
        cookie_name = getattr(settings, "JWT_ACCESS", "housekeeping_access_token")
        raw_token = request.COOKIES.get(cookie_name)


        if raw_token:
            if isinstance(raw_token, str) and raw_token.startswith("Bearer "):
                raw_token = raw_token.split(" ", 1)[1]
            try:
                validated_token = self.get_validated_token(raw_token)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except TokenError:
                # Invalid token in cookie; fallback to header
                return None

        header = self.get_header(request)
        if header is not None:
            try:
                return super().authenticate(request)
            except TokenError:
                return None

        # No token found anywhere
        return None