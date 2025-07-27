"""
WasteWise - Smart Waste Management System Settings
Django settings for WasteWise backend project.

This configuration supports:
- IoT sensor data collection via MQTT
- Real-time WebSocket communication
- Geographic data with PostGIS
- Task queues with Celery
- Comprehensive analytics and reporting
"""

from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Security Configuration
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "your-secret-key-here")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# API Keys and External Services
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")

# Application Definition - WasteWise Apps
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",  # Geographic support
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "channels",
    "django_filters",
    "drf_spectacular",
    "django_celery_beat",
    "django_celery_results",
    "django_extensions",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
]

# WasteWise Core Apps
WASTEWISE_APPS = [
    "apps.wastewise.bins",          # Waste bin management
    "apps.wastewise.sensors",       # IoT sensor data
    "apps.wastewise.routes",        # Collection routes
    "apps.wastewise.alerts",        # Alert system
    "apps.wastewise.analytics",     # Data analytics
    "apps.wastewise.zones",         # Geographic zones
    "apps.wastewise.vehicles",      # Collection vehicles
    "apps.wastewise.users",         # User management
    "apps.wastewise.notifications", # Push notifications
    "apps.wastewise.reports",       # Reporting system
]

# Legacy Apps (keeping for backward compatibility)
LEGACY_APPS = [
    "apps.Authentication",
    "apps.User",
    "apps.Notification",
    "apps.Message",
    "utils",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + WASTEWISE_APPS + LEGACY_APPS

# Middleware Configuration
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

ROOT_URLCONF = "backend.urls"

# Template Configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

# WSGI and ASGI Configuration
WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"

# Database Configuration - PostgreSQL with PostGIS
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("DB_NAME", "wastewise"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "password"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# PostGIS/GDAL Configuration
import ctypes.util

# Geographic libraries configuration
if os.name == "nt":  # Windows
    OSGEO4W = r"C:\OSGeo4W"
    if os.path.isdir(OSGEO4W):
        os.environ["OSGEO4W_ROOT"] = OSGEO4W
        os.environ["GDAL_DATA"] = os.path.join(OSGEO4W, "share", "gdal")
        os.environ["PROJ_LIB"] = os.path.join(OSGEO4W, "share", "proj")
        os.environ["PATH"] = os.path.join(OSGEO4W, "bin") + ";" + os.environ["PATH"]
        GDAL_LIBRARY_PATH = os.path.join(OSGEO4W, "bin", "gdal310.dll")
        GEOS_LIBRARY_PATH = os.path.join(OSGEO4W, "bin", "geos_c.dll")
else:  # Linux/Unix
    GDAL_LIBRARY_PATH = ctypes.util.find_library("gdal")
    GEOS_LIBRARY_PATH = ctypes.util.find_library("geos_c")

# Cache Configuration - Redis
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://localhost:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Session Configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 86400  # 24 hours

# Channels Configuration for WebSocket
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://localhost:6379/2")],
        },
    },
}

# Celery Configuration for Background Tasks
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/3")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/3")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# MQTT Configuration for IoT Sensors
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPICS = {
    "sensor_data": "wastewise/sensors/+/data",
    "alerts": "wastewise/alerts/+",
    "status": "wastewise/sensors/+/status",
}

# Authentication Configuration
AUTH_USER_MODEL = "users.WasteWiseUser"

AUTHENTICATION_BACKENDS = [
    "apps.wastewise.users.backends.EmailPhoneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

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

# Django REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "burst": "60/min",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# API Documentation with drf-spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "WasteWise API",
    "DESCRIPTION": "Smart Waste Management System for Accra, Ghana",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
    "COMPONENT_SPLIT_REQUEST": True,
}

# CORS Configuration
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
else:
    CORS_ALLOWED_ORIGINS = [
        "https://wastewise.gh",
        "https://dashboard.wastewise.gh",
        "https://api.wastewise.gh",
    ]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-refresh-token",
]

# Internationalization
LANGUAGE_CODE = "en"
TIME_ZONE = "Africa/Accra"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("tw", "Twi"),
    ("ga", "Ga"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Static and Media Files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Default Auto Field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email Configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@wastewise.gh")

# Push Notifications Configuration
PUSH_NOTIFICATIONS_SETTINGS = {
    "FCM_API_KEY": os.getenv("FCM_API_KEY", ""),
    "APNS_CERTIFICATE": os.getenv("APNS_CERTIFICATE", ""),
}

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "wastewise.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "wastewise": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / "logs").mkdir(exist_ok=True)

# Security Settings for Production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"

# WasteWise Specific Settings
WASTEWISE_SETTINGS = {
    # Sensor Configuration
    "SENSOR_DATA_RETENTION_DAYS": 365,
    "SENSOR_OFFLINE_THRESHOLD_MINUTES": 60,
    "SENSOR_BATTERY_LOW_THRESHOLD": 20,
    
    # Alert Configuration
    "BIN_FULL_THRESHOLD": 85,  # Percentage
    "BIN_OVERFLOW_THRESHOLD": 95,  # Percentage
    "ALERT_ESCALATION_HOURS": 4,
    
    # Route Optimization
    "ROUTE_OPTIMIZATION_ALGORITHM": "genetic_algorithm",
    "MAX_ROUTE_DURATION_HOURS": 8,
    "VEHICLE_CAPACITY_LITERS": 5000,
    
    # Analytics
    "ANALYTICS_REFRESH_INTERVAL_MINUTES": 15,
    "PREDICTION_MODEL_RETRAIN_DAYS": 7,
    
    # Mobile App
    "MOBILE_API_VERSION": "v1",
    "MOBILE_UPDATE_REQUIRED_VERSION": "1.0.0",
    
    # Integration
    "WEATHER_API_REFRESH_HOURS": 6,
    "GOOGLE_MAPS_GEOCODING_ENABLED": True,
}

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    from .settings_production import *
elif os.getenv("ENVIRONMENT") == "staging":
    from .settings_staging import *

# Print configuration summary (only in DEBUG mode)
if DEBUG:
    print("=== WasteWise Configuration Summary ===")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Database: {DATABASES['default']['NAME']}@{DATABASES['default']['HOST']}")
    print(f"Redis: {CACHES['default']['LOCATION']}")
    print(f"MQTT Broker: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    print(f"Debug Mode: {DEBUG}")
    print("=====================================")
