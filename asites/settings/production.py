"""
Production environment settings and globals.
Environment vars are defined in a .env file stored in the settings directory.
"""

from asites.settings.base import *

########## SECURITY CONFIGURATION
#SESSION_COOKIE_SECURE = True
#CSRF_COOKIE_SECURE = True
########## END SECURITY CONFIGURATION

########## SITE CONFIGURATION
ALLOWED_HOSTS = [env('ALLOWED_HOSTS')]
########## END SITE CONFIGURATION


########## EMAIL CONFIGURATION
ADMINS = [(env('ADMIN_NAME'), env('ADMIN_EMAIL'))]

EMAIL_HOST = env('EMAIL_HOST')
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

MAILER_LIST = [env('MAILER_LIST')]
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
########## END EMAIL CONFIGURATION


########## APPLICATION CONFIGURATION
INSTALLED_APPS = [
    'pm.apps.PmConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dbbackup',
#    'csvimport.app.CSVImportConf',
]
########## END APPLICATION CONFIGURATION


########## BACKUP CONFIGURATION
DBBACKUP_STORAGE = env('DBBACKUP_STORAGE')
DBBACKUP_STORAGE_OPTIONS = {
    'access_key': env('DB_ACCESS_KEY'),
    'secret_key': env('DB_SECRET_KEY'),
    'bucket_name': env('DB_BUCKET_NAME')
}
########## END BACKUP CONFIGURATION


########## DATABASE CONFIGURATION
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'projectmatica',
	'USER': env('DB_USER'),
	'PASSWORD': env('DB_PASSWORD'),
	'HOST': env('DB_HOST'),
	'PORT': '',
    }
}
########## END DATABASE CONFIGURATION


########## STATIC FILES CONFIGURATION
# STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATIC_ROOT = os.path.join(DJANGO_ROOT, 'static/')
########## END STATIC FILES CONFIGURATION
