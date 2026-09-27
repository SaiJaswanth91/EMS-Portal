import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')
load_dotenv(BASE_DIR.parent / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-eelms-default-key-change-in-prod-12345')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [host.strip() for host in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',') if host.strip()]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Application definition
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party packages
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'drf_spectacular',

    # EELMS Domain Apps
    'apps.accounts.apps.AccountsConfig',
    'apps.departments.apps.DepartmentsConfig',
    'apps.employees.apps.EmployeesConfig',
    'apps.attendance.apps.AttendanceConfig',
    'apps.leaves.apps.LeavesConfig',
    'apps.notifications.apps.NotificationsConfig',
    'apps.documents.apps.DocumentsConfig',
    'apps.reports.apps.ReportsConfig',
    'apps.audit.apps.AuditConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.notifications.context_processors.notification_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database Configuration (PostgreSQL with SQLite fallback)
from urllib.parse import urlparse, parse_qs, unquote


def _get_postgres_sslmode(host):
    """Return sslmode='require' for remote hosts unless explicitly overridden by environment variable."""
    sslmode_env = os.getenv('DATABASE_SSLMODE', os.getenv('PGSSLMODE', os.getenv('POSTGRES_SSLMODE', ''))).strip()
    if sslmode_env:
        return sslmode_env
    if host and host.lower() not in ('localhost', '127.0.0.1', '0.0.0.0', 'db'):
        return 'require'
    return None


database_url = os.getenv('DATABASE_URL', os.getenv('POSTGRES_URL', '')).strip()
pg_host = os.getenv('PGHOST', '').strip()
pg_db = os.getenv('PGDATABASE', '').strip()
postgres_host = os.getenv('POSTGRES_HOST', '').strip()
postgres_db = os.getenv('POSTGRES_DB', os.getenv('POSTGRES_DATABASE', '')).strip()
use_postgres_flag = os.getenv('USE_POSTGRES', 'False').lower() in ('true', '1', 'yes')

db_config = None

# Priority 1: DATABASE_URL / POSTGRES_URL
if database_url:
    parsed_url = urlparse(database_url)
    if parsed_url.scheme in ('postgres', 'postgresql'):
        db_name = unquote(parsed_url.path.lstrip('/'))
        db_user = unquote(parsed_url.username) if parsed_url.username else ''
        db_password = unquote(parsed_url.password) if parsed_url.password else ''
        db_host = parsed_url.hostname or ''
        db_port = str(parsed_url.port) if parsed_url.port else ''

        options = {}
        query_params = parse_qs(parsed_url.query)
        if 'sslmode' in query_params:
            options['sslmode'] = query_params['sslmode'][0]
        else:
            sslmode = _get_postgres_sslmode(db_host)
            if sslmode:
                options['sslmode'] = sslmode

        db_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': db_user,
            'PASSWORD': db_password,
            'HOST': db_host,
            'PORT': db_port,
        }
        if options:
            db_config['OPTIONS'] = options

# Priority 2: PG* variables
if not db_config and (pg_host or pg_db):
    db_host = pg_host or 'localhost'
    db_port = os.getenv('PGPORT', '5432').strip()
    db_user = os.getenv('PGUSER', 'postgres').strip()
    db_password = os.getenv('PGPASSWORD', '').strip()
    db_name = pg_db or 'eelms_db'

    options = {}
    sslmode = _get_postgres_sslmode(db_host)
    if sslmode:
        options['sslmode'] = sslmode

    db_config = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': db_host,
        'PORT': db_port,
    }
    if options:
        db_config['OPTIONS'] = options

# Priority 3: POSTGRES_* variables
if not db_config and (postgres_host or postgres_db):
    db_host = postgres_host or 'localhost'
    db_port = os.getenv('POSTGRES_PORT', '5432').strip()
    db_user = os.getenv('POSTGRES_USER', 'postgres').strip()
    db_password = os.getenv('POSTGRES_PASSWORD', '').strip()
    db_name = postgres_db or 'eelms_db'

    options = {}
    sslmode = _get_postgres_sslmode(db_host)
    if sslmode:
        options['sslmode'] = sslmode

    db_config = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': db_host,
        'PORT': db_port,
    }
    if options:
        db_config['OPTIONS'] = options

# Priority 4: Existing USE_POSTGRES=True + DATABASE_* variables
if not db_config and use_postgres_flag:
    db_host = os.getenv('DATABASE_HOST', 'localhost').strip()
    db_port = os.getenv('DATABASE_PORT', '5432').strip()
    db_user = os.getenv('DATABASE_USER', 'postgres').strip()
    db_password = os.getenv('DATABASE_PASSWORD', 'postgres').strip()
    db_name = os.getenv('DATABASE_NAME', 'eelms_db').strip()

    options = {}
    sslmode = _get_postgres_sslmode(db_host)
    if sslmode:
        options['sslmode'] = sslmode

    db_config = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': db_host,
        'PORT': db_port,
    }
    if options:
        db_config['OPTIONS'] = options

# Priority 5: SQLite fallback
if not db_config:
    db_config = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

DATABASES = {'default': db_config}

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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (User uploads, profile photos, documents)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms Config
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Django REST Framework Config
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# DRF Spectacular Settings (Swagger UI)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Enterprise Employee & Leave Management System (EELMS) API',
    'DESCRIPTION': 'Production-grade REST APIs for EELMS platform.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Redis & Celery Config
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Login/Logout Redirect URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Email Config
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'EELMS Admin <noreply@eelms.com>')
