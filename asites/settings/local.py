"""
Development environment settings and globals.
Environment vars are defined in a .env file stored in the settings directory.
"""

from asites.settings.base import *

########## DATABASE CONFIGURATION
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DJANGO_ROOT, 'db.sqlite3'),
    }
}
########## END DATABASE CONFIGURATION
