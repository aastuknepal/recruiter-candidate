# =============================================================================
# base.py
# =============================================================================
from datetime import timedelta
from pathlib import Path
import sys

from decouple import config


# =============================================================================
# BASE CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',')]
)


# =============================================================================
# INSTALLED APPLICATIONS
# =============================================================================

BASE_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

PROJECT_APPS = [
    'apps.users',
    'apps.setup',
    'apps._dev',
    # 'apps.public_api',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'corsheaders',
    'django_crontab',
]

INSTALLED_APPS = BASE_APPS + PROJECT_APPS + THIRD_PARTY_APPS


# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps._dev.middleware.DevMiddleware',
]


# =============================================================================
# URL & WSGI CONFIGURATION
# =============================================================================

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'


# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# =============================================================================
# DATABASES
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE':   config('DB_ENGINE'),
        'NAME':     config('DB_NAME'),
        'USER':     config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST':     config('DB_HOST'),
        'PORT':     config('DB_PORT'),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================================
# AUTHENTICATION
# =============================================================================

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =============================================================================
# REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'common_utils.auth.authentication.JWTCookieAuthenticationBackend',
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


# =============================================================================
# JWT AUTHENTICATION (Simple JWT)
# =============================================================================

JWT_SECRET_KEY = config('SECRET_KEY')

JWT_REFRESH = config('JWT_REFRESH', default='dartachalani_refresh_token')
JWT_ACCESS  = config('JWT_ACCESS',  default='dartachalani_access_token')

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM':   'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# =============================================================================
# CORS & CSRF
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    origin for origin in config('CORS_ALLOWED_ORIGINS').split(',') if origin
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    origin for origin in config('CSRF_TRUSTED_ORIGINS', default='').split(',') if origin
]

SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SAMESITE    = 'None'


# =============================================================================
# INTERNATIONALIZATION & TIMEZONE
# =============================================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kathmandu'

USE_I18N = True

USE_TZ = True


# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

BASE_PREFIX = config('BASE_PREFIX', default='')

STATIC_URL  = BASE_PREFIX + config('STATIC_URL', default='static/')
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL  = BASE_PREFIX + config('MEDIA_URL', default='media/')
MEDIA_ROOT = BASE_DIR / 'media'


# =============================================================================
# CRON JOBS (django-crontab)
# =============================================================================

CRON_LOGS_DIR = BASE_DIR.resolve() / 'cron_logs'
CRON_LOGS_DIR.mkdir(exist_ok=True)

CRONTAB_PYTHON_EXECUTABLE = sys.executable

CRONTAB_COMMAND_PREFIX = ''

CRONJOBS = [
    # (
    #     '0 0 * * *',
    #     'apps.inventory.tasks.expire_reservations',
    #     f'>> {CRON_LOGS_DIR}/expire_reservations.log 2>&1',
    # ),
    # (
    #     '* * * * *',
    #     'apps.inventory.tasks.expire_blood_components',
    #     f'>> {CRON_LOGS_DIR}/expire_blood_components.log 2>&1',
    # ),
]

# =============================================================================
# =============================================================================
X_FRAME_OPTIONS = "DENY"
