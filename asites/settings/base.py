"""
Common settings and globals (local and production).
Environment vars are defined in a .env file stored in the settings directory.
django-environ is a dependency. install instructions: http://django-environ.readthedocs.io/en/latest/index.html
see env variable config instructions at http://django-environ.readthedocs.io/en/latest/
"""

import os
from os import environ
from os.path import abspath, basename, dirname, join, normpath
from sys import path
import environ
env = environ.Env(DEBUG=(bool, False),) # set default values and casting
environ.Env.read_env() # reading .env file


########## PATH CONFIGURATION
# Absolute filesystem path to the Django project directory:
DJANGO_ROOT = dirname(dirname(dirname(abspath(__file__))))

# Absolute filesystem path to the top-level project folder:
SITE_ROOT = dirname(DJANGO_ROOT)

# Site name:
SITE_NAME = basename(DJANGO_ROOT)

# Add our project to our pythonpath, this way we don't need to type our project
# name in our dotted import paths:
path.append(DJANGO_ROOT)
########## END PATH CONFIGURATION


########## SITE CONFIGURATION
SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env('DEBUG') # False if not in os.environ
# ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
ALLOWED_HOSTS = []
########## END SITE CONFIGURATION


########## APPLICATION CONFIGURATION
INSTALLED_APPS = [
    'pm.apps.PmConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'csvimport.app.CSVImportConf',
    # 'mathfilters',
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
ROOT_URLCONF = 'asites.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(DJANGO_ROOT, 'templates')],
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
WSGI_APPLICATION = 'asites.wsgi.application'
LOGIN_REDIRECT_URL = '/'
########## END APPLICATION CONFIGURATION


########## PASSWORD CONFIGURATION
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators
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
########## END PASSWORD CONFIGURATION


########## INTERNATIONALIZATION
# https://docs.djangoproject.com/en/1.10/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Vancouver'
USE_I18N = True
USE_L10N = True
USE_TZ = True
########## END INTERNATIONALIZATION


########## STATIC FILES CONFIGURATION (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
STATIC_URL = '/static/'
########## END STATIC FILES CONFIGURATION


########## REDMINE CONFIGURATION
REDMINE_URL = env('REDMINE_URL')
REDMINE_VER = env('REDMINE_VER')
REDMINE_KEY = env('REDMINE_KEY')
########## END REDMINE CONFIGURATION
