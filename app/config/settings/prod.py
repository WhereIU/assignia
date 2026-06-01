from .base import *

# MODE
DEBUG=1

# SECURITY
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# SESSIONS
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# STATIC
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
