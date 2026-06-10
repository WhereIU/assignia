from .base import *

# SECURITY
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# STATIC
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
