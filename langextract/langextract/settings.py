"""
Django settings for langextract project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    # 'django.contrib.admin',      # Disabled - not needed for API service
    # 'django.contrib.auth',       # Disabled - not needed for API service
    # 'django.contrib.contenttypes', # Disabled - not needed for API service
    # 'django.contrib.sessions',   # Disabled - not needed for API service
    # 'django.contrib.messages',   # Disabled - not needed for API service
    'django.contrib.staticfiles', # Enabled for document chat interface
    'rest_framework',
    'api',
    'core',
    'document_api',
    'document_processor',
]

MIDDLEWARE = [
    'core.middleware.StatelessMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'langextract.urls'

# Templates - Enabled for document chat interface
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'langextract.wsgi.application'

# Database - Not needed for stateless API service
DATABASES = {}

# Password validation - Disabled for stateless API service
# AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files - not needed for stateless API service
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Migrations - Not needed for stateless API service
MIGRATION_MODULES = {}

# REST Framework settings - Minimal configuration
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_THROTTLE_CLASSES': [],
    'UNAUTHENTICATED_USER': None,
}

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'text-embedding-3-small')
MAX_TOKENS_PER_REQUEST = int(os.getenv('MAX_TOKENS_PER_REQUEST', '8000'))

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Vector Storage Configuration
VECTOR_STORAGE_ENABLED = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

# Schema Configuration
SCHEMA_DIR = BASE_DIR / 'schemas'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
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
        'level': 'INFO',
    },
}

# Initialize vector storage service
try:
    from core.vector_storage import VectorStorage
    from core.supabase_client import SupabaseClient
    
    # Initialize Supabase client
    supabase_client = SupabaseClient()
    
    # Initialize vector storage
    vector_storage = VectorStorage()
    
except ImportError as e:
    print(f"Warning: Could not import vector storage modules: {e}")
    vector_storage = None
except Exception as e:
    print(f"Warning: Could not initialize vector storage: {e}")
    vector_storage = None
