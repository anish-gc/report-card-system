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
import os
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'reportcard_cache',
        'TIMEOUT': 3600,  # 1 hour default timeout
    }
}

# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'  # Different DB for results
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes timeout
CELERY_ENABLE_UTC = True


CELERY_TASK_ROUTES = {
    'students.tasks.calculate_report_card_aggregates': {'queue': 'calculations'},
    'students.tasks.calculate_student_grade': {'queue': 'calculations'},
    'students.tasks.calculate_class_averages': {'queue': 'calculations'},
    'students.tasks.bulk_calculate_report_cards': {'queue': 'bulk_operations'},
    'students.tasks.cleanup_old_cache': {'queue': 'maintenance'},
}

# Define queues
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUES = {
    'default': {
        'exchange': 'default',
        'exchange_type': 'direct',
        'routing_key': 'default',
    },
    'calculations': {
        'exchange': 'calculations',
        'exchange_type': 'direct',
        'routing_key': 'calculations',
    },
    'bulk_operations': {
        'exchange': 'bulk_operations',
        'exchange_type': 'direct',
        'routing_key': 'bulk_operations',
    },
    'maintenance': {
        'exchange': 'maintenance',
        'exchange_type': 'direct',
        'routing_key': 'maintenance',
    },
}

# Worker configuration
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Task time limits
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes

# Result backend settings
CELERY_RESULT_EXPIRES = 3600  # 1 hour

# Task retry configuration
CELERY_TASK_RETRY_DELAY = 60  # 1 minute
CELERY_TASK_MAX_RETRIES = 3

# Beat schedule for periodic tasks
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-cache': {
        'task': 'students.tasks.cleanup_old_cache',
        'schedule': crontab(minute=0, hour=2),  # Run daily at 2 AM
        'options': {'queue': 'maintenance'}
    },
    'calculate-daily-class-averages': {
        'task': 'students.tasks.calculate_class_averages',
        'schedule': crontab(minute=30, hour=1),  # Run daily at 1:30 AM
        'args': [2024],  # Current year - should be dynamic
        'options': {'queue': 'calculations'}
    },
}
 