from .common import *

DEBUG = True

ALLOWED_HOSTS = ['*']

SECRET_KEY = config("SECRET_KEY")

CORS_ORIGIN_ALLOW_ALL = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config("DB_NAME"), 
        'USER': config("DB_USER"),
        'PASSWORD': config("DB_PASSWORD"),
        'HOST': config("DB_HOST"),
        'PORT': config("DB_PORT"),
    }
}

STATIC_URL = "static/"


 