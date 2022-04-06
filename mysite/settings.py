"""
Django settings for mysite project.

Generated by 'django-admin startproject' using Django 3.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import json
import os.path
from pathlib import Path
import MySQLdb
import cx_Oracle
from django.urls import reverse_lazy
from django.core.management.utils import get_random_secret_key
from django.contrib.messages import constants as messages
from django.core.exceptions import ImproperlyConfigured

MESSAGE_TAGS = {
        messages.DEBUG: 'alert-secondary',
        messages.INFO: 'alert-info',
        messages.SUCCESS: 'alert-success',
        messages.WARNING: 'alert-warning',
        messages.ERROR: 'alert-danger',
}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

with open(os.path.join(BASE_DIR, 'secrets.json')) as secret_file:
    secrets = json.load(secret_file)

def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        raise ImproperlyConfigured(f"Set the {setting} setting")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_secret('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!

#develop
#DEBUG = True
#ALLOWED_HOSTS = []

#production
DEBUG = False
ALLOWED_HOSTS = ["www.bora.tec.br","www.bora.tec.br/portaria", "bora.tec.br", "bora.tec.br/portaria"]

# Application definition

INSTALLED_APPS = [
    'portaria',
    'django_summernote',
    'notifications',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'portaria/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

#develop
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
#}
CONNECTION = cx_Oracle.connect(get_secret('ORA_UID'),get_secret('ORA_PWD'), cx_Oracle.makedsn(get_secret('ORA_HOST'), '1521', None, get_secret('ORA_XE')))
#production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'bora',
        'USER': get_secret('DB_USER'),
        'PASSWORD': get_secret('DB_PASS'),
        'HOST': get_secret('DB_HOST'),
        'PORT': '3306',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

SESSION_COOKIE_AGE = 10800

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
DATETIME_FORMAT = 'd/m/Y H:i'

DATE_FORMAT = 'd/m/Y'

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_L10N = False

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = get_secret('STATIC_URL')
STATIC_ROOT = get_secret('STATIC_ROOT')

MEDIA_URL = get_secret('MEDIA_URL')
MEDIA_ROOT = get_secret('MEDIA_ROOT')


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


#auth redirects
LOGIN_URL = reverse_lazy('login')
LOGIN_REDIRECT_URL = '/portaria/'
LOGOUT_REDIRECT_URL = '/portaria/'

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


#EMAIL CONFIG
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = get_secret('E_HOST')
EMAIL_PORT = get_secret('E_PORT')
EMAIL_USE_TLS = True
EMAIL_HOST_USER = get_secret('E_UMAIL')
EMAIL_HOST_PASSWORD = get_secret('E_UPASS')

DJANGO_NOTIFICATIONS_CONFIG = { 'USE_JSONFIELD': True}

#summernote
X_FRAME_OPTIONS = 'SAMEORIGIN'

SUMMERNOTE_CONFIG = {
'iframe': True,

'summernote': {
        # As an example, using Summernote Air-mode
        'airMode': False,
        'disableResizeEditor': False,
        # Change editor size
        'width': '100%',
        'height': '300',
        # Toolbar customization
        # https://summernote.org/deep-dive/#custom-toolbar-popover
        'toolbar': [
            ['style', ['style']],
            ['fontname', ['fontname']],
        ],

        # Or, explicitly set language/locale for editor
        'lang': 'pt-BR',
        'codemirror': {
            'mode': 'htmlmixed',
            'lineNumbers': 'true',
            # You have to include theme file in 'css' or 'css_for_inplace' before using it.
            'theme': 'monokai',
        },
    }
}

