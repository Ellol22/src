"""
Django settings for your project.
"""

import os
from pathlib import Path
import re
from django.http import JsonResponse
from django.conf import settings
from dotenv import load_dotenv
from datetime import timedelta
from urllib.parse import urlparse
from corsheaders.defaults import default_headers, default_methods

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
SECRET_KEY = os.getenv('SECRET_KEY', '9eadf54afe12de795a409fc8a0e8c950e923521100f0396c377b40de6a2c539a')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
SITE_DOMAIN = os.getenv('SITE_DOMAIN', 'https://clicking-appointment-coordinates-hang.trycloudflare.com')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'helwanuniversity82@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'kxcp kryq kbut kolg')

# Extract hostname from SITE_DOMAIN
site_hostname = urlparse(SITE_DOMAIN).hostname if SITE_DOMAIN else 'localhost'

print('SITE_DOMAIN:', SITE_DOMAIN)
print('FRONTEND_URL:', FRONTEND_URL)

# Allowed hosts
ALLOWED_HOSTS = [
    site_hostname,
    'localhost',
    '127.0.0.1',
    'clicking-appointment-coordinates-hang.trycloudflare.com',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'accounts',
    'attendance',
    'structure',
    'courses',
    'grades',
    'dashboard',
    'schedule',
    'chatbot',
    'recommendation',
    'upload_center',
    'quiz',
    'django_extensions',
]

# Custom middleware
def mobile_origin_allow_middleware(get_response):
    def middleware(request):
        origin = request.META.get('HTTP_ORIGIN')
        host = request.META.get('HTTP_HOST')
        client_type = request.META.get('HTTP_X_CLIENT_TYPE')
        method = request.method

        print(f"Request Path: {request.path}, Method: {method}, Origin: {origin}, Host: {host}, Client-Type: {client_type}")

        # Allow requests from mobile app (X-Client-Type: mobile_app)
        if client_type == 'mobile_app':
            response = get_response(request)
            response["Access-Control-Allow-Origin"] = origin or '*'
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-CSRFToken, X-Client-Type"
            response["Access-Control-Allow-Credentials"] = "true"
            return response

        # Allow local origins in debug mode
        if settings.DEBUG and origin and re.match(r'^http://(localhost|127\.0\.0\.1):3000$', origin):
            response = get_response(request)
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-CSRFToken, X-Client-Type"
            response["Access-Control-Allow-Credentials"] = "true"
            return response

        allowed = [
            SITE_DOMAIN,
            FRONTEND_URL,
            'http://localhost:3000',
            'http://127.0.0.1:3000',
            'https://clicking-appointment-coordinates-hang.trycloudflare.com',
            'clicking-appointment-coordinates-hang.trycloudflare.com',
        ]

        if method == 'OPTIONS':
            response = get_response(request)
            response["Access-Control-Allow-Origin"] = origin or '*'
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-CSRFToken, X-Client-Type"
            response["Access-Control-Allow-Credentials"] = "true"
            return response

        if origin and any(x in origin for x in allowed):
            return get_response(request)
        elif host and any(x in host for x in allowed):
            return get_response(request)
        elif 'api/' in request.path or request.path.endswith('.json'):
            return get_response(request)
        elif settings.DEBUG:
            # ✅ السماح في وضع التطوير حتى لو مفيش Origin
            return get_response(request)
        else:
            return JsonResponse({'detail': 'Blocked Origin'}, status=403)


    return middleware

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'project.settings.mobile_origin_allow_middleware',
]

# CORS settings
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    SITE_DOMAIN,
    FRONTEND_URL,
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://clicking-appointment-coordinates-hang.trycloudflare.com',
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    'content-type',
    'authorization',
    'x-csrftoken',
    'x-client-type',
    'accept',
    'origin',
]

CORS_ALLOW_METHODS = list(default_methods) + [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

# CSRF and session settings
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_SAMESITE = 'None' if not DEBUG else 'Lax'
SESSION_COOKIE_SAMESITE = 'None' if not DEBUG else 'Lax'

CSRF_TRUSTED_ORIGINS = [
    SITE_DOMAIN,
    FRONTEND_URL,
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://clicking-appointment-coordinates-hang.trycloudflare.com',
    'http://127.0.0.1:8000'
]

# Security settings
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = not DEBUG

# JWT settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ALGORITHM': 'HS256',
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# settings.py

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Cairo'  # ✅ غيّرها من 'UTC' لـ 'Africa/Cairo'
USE_I18N = True
USE_TZ = True  # خليه True علشان Django يشتغل بالـ UTC داخليًا، لكن يعرض بالتوقيت المحلي


# Static and media files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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