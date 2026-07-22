import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default=0):
    value = os.getenv(name)

    if value is None or value == "":
        return default

    return int(value)


def env_list(name, default=None):
    value = os.getenv(name)

    if value is None or value.strip() == "":
        return default or []

    return [item.strip() for item in value.split(",") if item.strip()]


# Base settings

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "local-dev-only-change-this-secret-key-in-env-file-please-123456789",
)

DEBUG = env_bool("DJANGO_DEBUG", default=True)

# پیدا کن ALLOWED_HOSTS و اضافه کن testserver:

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']  # ✅ testserver اضافه شد


# Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "operations_hub.apps.OperationsHubConfig",
    "accounts",
    "orders",
    "catalog",
    "projects",
    "notifications",
    "payments",
    "control_panel",
]


SMARTBASE_APPS = [
    "easy_thumbnails",
    "widget_tweaks",
    "ckeditor",
    "ckeditor_uploader",
    "django_smartbase_admin.audit",
    # Keep this last: it discovers ModelAdmin classes already registered
    # by Retoucher's local applications.
    "django_smartbase_admin",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS + SMARTBASE_APPS


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "operations_hub.middleware.PanelAuditMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "control_panel.context_processors.panel_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database: PostgreSQL

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "retoucher_db")),
        "USER": os.getenv("POSTGRES_USER", os.getenv("DB_USER", "retoucher_user")),
        "PASSWORD": os.getenv(
            "POSTGRES_PASSWORD",
            os.getenv("DB_PASSWORD", "retoucher_pass"),
        ),
        "HOST": os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost")),
        "PORT": os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5432")),
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Celery Configuration
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"

CELERY_BEAT_SCHEDULE = {
    "check-project-expirations": {
        "task": "projects.tasks.check_project_expirations",
        "schedule": 900.0,  # Every 15 minutes in seconds
    },
    "check-proposal-deadlines": {
        "task": "projects.tasks.check_proposal_deadlines",
        "schedule": 900.0,  # Every 15 minutes in seconds
    },
    "check-sla-violations": {
        "task": "orders.tasks.check_sla_violations",
        "schedule": 3600.0,  # Every hour
    },
    "check-workflow-deadlines": {
        "task": "orders.tasks.check_workflow_deadlines",
        "schedule": 300.0,
    },
}

# اگر LOGGING config داری، تبدیل کن به:

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "projects.expiration_handler": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}


# Internationalization

LANGUAGE_CODE = "fa-ir"

TIME_ZONE = "Asia/Tehran"

USE_I18N = True

USE_TZ = True


# Static files

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"


# Django REST Framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# JWT Settings

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# CORS / CSRF

CORS_ALLOWED_ORIGINS = env_list(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
)

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=[],
)


# Production security settings

SECURE_SSL_REDIRECT = env_bool(
    "DJANGO_SECURE_SSL_REDIRECT",
    default=not DEBUG,
)

SESSION_COOKIE_SECURE = env_bool(
    "DJANGO_SESSION_COOKIE_SECURE",
    default=not DEBUG,
)

CSRF_COOKIE_SECURE = env_bool(
    "DJANGO_CSRF_COOKIE_SECURE",
    default=not DEBUG,
)

SECURE_HSTS_SECONDS = env_int(
    "DJANGO_SECURE_HSTS_SECONDS",
    default=31536000 if not DEBUG else 0,
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=not DEBUG,
)

SECURE_HSTS_PRELOAD = env_bool(
    "DJANGO_SECURE_HSTS_PRELOAD",
    default=not DEBUG,
)

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# Swagger / OpenAPI

SPECTACULAR_SETTINGS = {
    "TITLE": "Retoucher API",
    "DESCRIPTION": """
Retoucher backend API.

This API manages the full photo retouching workflow:

- JWT authentication
- Order creation and submission
- Image upload
- Editor assignment
- Editor work and delivery
- Supervisor review and QC
- Client review and revision requests
- Settlement and payment workflow
- Order comments, threaded replies, rich annotations
- Comment resolve/unresolve workflow
- Activity logs
- Notifications
- Dashboard and summary endpoints
""",
    "VERSION": "1.0.0-phase1",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/",
    "TAGS": [
        {
            "name": "Orders",
            "description": "Order CRUD and main order workflow.",
        },
        {
            "name": "Order Workflow",
            "description": "Submit, review, assignment, delivery, approval, settlement.",
        },
        {
            "name": "Order Comments",
            "description": "Comments, replies, annotations, resolve/unresolve.",
        },
        {
            "name": "Order Activity Logs",
            "description": "Audit trail and order history.",
        },
        {
            "name": "Order Notifications",
            "description": "User notifications related to order activity.",
        },
        {
            "name": "Order Dashboard",
            "description": "Dashboard, workload, status and settlement summaries.",
        },
    ],
}


# SmartBase Admin
SB_ADMIN_CONFIGURATION = "config.sbadmin_config.SBAdminConfiguration"

# Required by django-ckeditor uploader.
CKEDITOR_UPLOAD_PATH = "ckeditor/"

# Keep thumbnail handling deterministic for uploaded admin assets.
THUMBNAIL_HIGH_RESOLUTION = True
LOGIN_URL = "/panel/login/"
LOGIN_REDIRECT_URL = "/panel/"

STATICFILES_DIRS = [BASE_DIR / "static"]


# Legacy SmartBase is retained temporarily; Velzon is the operational panel.
SILENCED_SYSTEM_CHECKS = ["sbadmin.W003"]
