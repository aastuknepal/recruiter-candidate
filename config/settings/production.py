from .base import *

# =============================================================================
# BASE OVERRIDES
# =============================================================================

DEBUG = False


# =============================================================================
# SECURITY
# =============================================================================

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST    = True

SECURE_SSL_REDIRECT    = True
SESSION_COOKIE_SECURE  = True
CSRF_COOKIE_SECURE     = True