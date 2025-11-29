"""
Django production settings for diaken project.

SECURITY: Este archivo contiene configuraciones específicas para producción.
Las configuraciones sensibles deben cargarse desde variables de entorno.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'CHANGE-THIS-IN-PRODUCTION-USE-ENV-VARIABLE')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY: Configure allowed hosts
ALLOWED_HOSTS_STR = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_STR:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',') if host.strip()]
else:
    # Fallback for development/testing
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# SECURITY: CSRF trusted origins
CSRF_TRUSTED_ORIGINS_STR = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '')
if CSRF_TRUSTED_ORIGINS_STR:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in CSRF_TRUSTED_ORIGINS_STR.split(',') if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

# SECURITY: Allowed networks (CIDR ranges)
# Example: 10.104.10.0/24,10.100.5.0/24,192.168.1.0/24
ALLOWED_NETWORKS_STR = os.environ.get('DJANGO_ALLOWED_NETWORKS', '')
if ALLOWED_NETWORKS_STR:
    ALLOWED_NETWORKS = [network.strip() for network in ALLOWED_NETWORKS_STR.split(',') if network.strip()]
else:
    # Fallback: Empty list - must be configured in .env for production
    ALLOWED_NETWORKS = []

# SECURITY: Network validation strategy
# The middleware validates IPs against ALLOWED_NETWORKS CIDR ranges
# ALLOWED_HOSTS validates hostnames
# We add '*' ONLY if ALLOWED_NETWORKS is configured, otherwise it's insecure
if ALLOWED_NETWORKS:
    # Safe to add wildcard because middleware will validate IPs
    ALLOWED_HOSTS.append('*')
else:
    # No networks configured - do not add wildcard
    # Only hostnames in ALLOWED_HOSTS will be accepted
    pass

# Application definition
INSTALLED_APPS = [    
    'deploy',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'login',
    'settings',
    'inventory',
    'history',
    'playbooks',
    'scheduler',
    'users',
    'dashboard',
    'snapshots',
    'scripts',
    'notifications',
]

LOGIN_URL = '/login/'

STATIC_URL = '/static/'

MIDDLEWARE = [
    # Custom middleware for network-based host validation (CIDR support)
    'security_fixes.network_allowed_hosts.NetworkAllowedHostsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'diaken.urls'

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

WSGI_APPLICATION = 'diaken.wsgi.application'

# Database
# Database Configuration
# Use environment variables for database configuration
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'unix_socket': os.environ.get('DB_SOCKET', ''),
        } if os.environ.get('DB_ENGINE') == 'django.db.backends.mysql' else {},
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (User uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Scripts directory configuration
SCRIPTS_ROOT = MEDIA_ROOT / 'scripts'

# Ansible configuration
ANSIBLE_PLAYBOOK_PATH = str(BASE_DIR / 'venv' / 'bin' / 'ansible-playbook')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ========================================
# SECURITY SETTINGS FOR PRODUCTION
# ========================================

# Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS/SSL Settings (uncomment when using HTTPS)
# SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'False') == 'True'
# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# Session Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Security
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Data Upload Limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB

# ========================================
# LOGGING CONFIGURATION
# ========================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_django': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/opt/www/logs/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'file_deployment': {
            'level': 'INFO',  # Changed from DEBUG for production
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/opt/www/logs/deployment.log',
            'maxBytes': 1024 * 1024 * 15,  # 15 MB
            'backupCount': 20,
            'formatter': 'verbose',
        },
        'file_security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/opt/www/logs/security.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_django', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'deploy': {
            'handlers': ['file_deployment', 'console'],
            'level': 'INFO',  # Changed from DEBUG for production
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file_security'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['file_django'],
        'level': 'INFO',
    },
}

# ========================================
# EMAIL CONFIGURATION (for error notifications)
# ========================================

# Uncomment and configure for production
# ADMINS = [('Admin', 'admin@example.com')]
# SERVER_EMAIL = 'django@your-server.example.com'
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# ========================================
# CELERY CONFIGURATION
# ========================================

# Celery broker and result backend (Redis)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Celery task settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Bogota'

# Celery task time limits
CELERY_TASK_TIME_LIMIT = 5400  # 90 minutes hard limit (for Windows)
CELERY_TASK_SOFT_TIME_LIMIT = 5100  # 85 minutes soft limit
