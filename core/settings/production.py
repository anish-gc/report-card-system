from .common import *
DEBUG = False

CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = ["*"]

CORS_ALLOWED_ORIGINS = ["https://ingtech.com"]

CSRF_TRUSTED_ORIGINS = ["http://api.ingtech.com"]
ALLOWED_HOSTS = [
            
    "127.0.0.1",              
    "api.ingtech.com",   
    "ingtech.com",
    
]

# Development-specific settings
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_DOMAIN = ".ingtech.com"
CSRF_COOKIE_SECURE = True

SECRET_KEY = config("SECRET_KEY")

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

# STATIC_URL = "static/"
# STATIC_ROOT = BASE_DIR/"static/"
