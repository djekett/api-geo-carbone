import os
import dj_database_url
from .base import *

# ──────────────────────────────────────────────
# Production settings — Render
# ──────────────────────────────────────────────

DEBUG = False

# Render fournit l'URL du service via RENDER_EXTERNAL_HOSTNAME
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# ──────────────────────────────────────────────
# Database — Render PostgreSQL (PostGIS)
# ──────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        engine='django.contrib.gis.db.backends.postgis',
    )

# ──────────────────────────────────────────────
# Static files — WhiteNoise
# ──────────────────────────────────────────────
MIDDLEWARE.insert(
    MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
    'whitenoise.middleware.WhiteNoiseMiddleware',
)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ──────────────────────────────────────────────
# Security
# ──────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ──────────────────────────────────────────────
# CORS — restreindre en production
# ──────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')

# ──────────────────────────────────────────────
# CSRF trusted origins
# ──────────────────────────────────────────────
CSRF_TRUSTED_ORIGINS = []
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')
extra_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if extra_csrf:
    CSRF_TRUSTED_ORIGINS.extend(extra_csrf.split(','))

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
