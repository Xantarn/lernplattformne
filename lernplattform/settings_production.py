"""
Production settings for lernplattform.
Load sensitive values from .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY: Get SECRET_KEY from environment, fail if not set
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY environment variable not set. "
        "Generate one and add it to .env file."
    )

# SECURITY: Must be False in production
DEBUG = False

# SECURITY: List all allowed hosts (domain + subdomains)
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS]

# CSRF and SSL settings
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
CSRF_TRUSTED_ORIGINS = [h.strip() for h in CSRF_TRUSTED_ORIGINS if h.strip()]

# Use HTTPS in production
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True') == 'True'
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True') == 'True'
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'True') == 'True'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_ckeditor_5',
    'quiz',
    'courses',
    'exams',
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

ROOT_URLCONF = 'lernplattform.urls'

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

WSGI_APPLICATION = 'lernplattform.wsgi.application'

# Database: PostgreSQL in production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'lernplattform_db'),
        'USER': os.getenv('DB_USER', 'lernplattform_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'de-de'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True

# Static files: use absolute path for production
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CKEDITOR_TABLE_COLOR_PALETTE = [
    {'color': '#ffffff', 'label': 'Weiss', 'hasBorder': True},
    {'color': '#f8fafc', 'label': 'Nebel'},
    {'color': '#e2e8f0', 'label': 'Hellgrau'},
    {'color': '#cbd5e1', 'label': 'Silber'},
    {'color': '#94a3b8', 'label': 'Schiefer'},
    {'color': '#1d4ed8', 'label': 'Blau'},
    {'color': '#0f766e', 'label': 'Teal'},
    {'color': '#16a34a', 'label': 'Gruen'},
    {'color': '#ea580c', 'label': 'Orange'},
    {'color': '#dc2626', 'label': 'Rot'},
]

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'underline', 'strikethrough', '|',
            'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', '|',
            'alignment', '|',
            'numberedList', 'bulletedList', '|',
            'outdent', 'indent', '|',
            'link', 'insertTable', 'blockQuote', '|',
            'undo', 'redo', 'removeFormat', '|',
            'sourceEditing'
        ],
        'height': '650px',
        'language': 'de',
        'table': {
            'contentToolbar': [
                'tableColumn', 'tableRow', 'mergeTableCells',
                'tableProperties', 'tableCellProperties'
            ],
            'tableProperties': {
                'borderColors': CKEDITOR_TABLE_COLOR_PALETTE,
                'backgroundColors': CKEDITOR_TABLE_COLOR_PALETTE,
                'defaultProperties': {
                    'borderStyle': 'solid',
                    'borderColor': '#94a3b8',
                    'borderWidth': '1px',
                    'backgroundColor': '#ffffff',
                },
            },
            'tableCellProperties': {
                'borderColors': CKEDITOR_TABLE_COLOR_PALETTE,
                'backgroundColors': CKEDITOR_TABLE_COLOR_PALETTE,
                'defaultProperties': {
                    'borderStyle': 'solid',
                    'borderColor': '#cbd5e1',
                    'borderWidth': '1px',
                    'backgroundColor': '#ffffff',
                },
            },
        },
        'htmlSupport': {
            'allow': [
                {
                    'name': '/.*/',
                    'attributes': True,
                    'classes': True,
                    'styles': True,
                },
            ],
        },
    },
}

# Code execution settings
CODE_EXECUTION_ENABLED = os.getenv('CODE_EXECUTION_ENABLED', 'True') == 'True'
CODE_EXECUTION_MAX_SOURCE_CHARS = 8000
CODE_EXECUTION_MAX_STDIN_CHARS = 4000
CODE_EXECUTION_MAX_EXPECTED_OUTPUT_CHARS = 6000
CODE_EXECUTION_MAX_STDOUT_CHARS = 6000
CODE_EXECUTION_MAX_STDERR_CHARS = 6000
CODE_EXECUTION_PYTHON_TIMEOUT_SECONDS = 3
CODE_EXECUTION_CPP_COMPILE_TIMEOUT_SECONDS = 8
CODE_EXECUTION_CPP_RUN_TIMEOUT_SECONDS = 3

CODE_EXECUTION_BLOCKED_PATTERNS = {
    "python": [
        "import os",
        "from os",
        "import subprocess",
        "from subprocess",
        "import socket",
        "from socket",
        "import ctypes",
        "from ctypes",
        "import pathlib",
        "from pathlib",
        "open(",
        "__import__(",
        "eval(",
        "exec(",
    ],
    "cpp": [
        "std::system",
        "system(",
        "popen(",
        "_popen(",
        "createprocess",
        "shellexecute",
        "winexec",
        "#include <filesystem>",
        "#include <fstream>",
        "#include <thread>",
    ],
}

# Topic PDF OCR settings
TOPIC_OCR_MAX_FILE_MB = 20
TOPIC_OCR_MAX_PAGES = 40
TOPIC_OCR_DPI = 300
TOPIC_OCR_LANG = "deu+eng"
TOPIC_OCR_MAX_TEXT_CHARS = 120000
# On Linux server, Tesseract should be in PATH, so these are optional
TOPIC_OCR_TESSERACT_CMD = os.getenv('TOPIC_OCR_TESSERACT_CMD', '/usr/bin/tesseract')
TOPIC_OCR_POPPLER_PATH = os.getenv('TOPIC_OCR_POPPLER_PATH', '/usr/bin')
TOPIC_OCR_TESSDATA_DIR = str(BASE_DIR / 'tessdata')

LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
CSRF_FAILURE_VIEW = "quiz.views.csrf_failure"

# Logging configuration
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
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}

# Ensure logs directory exists
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)
