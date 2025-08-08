from __future__ import absolute_import, unicode_literals
# projectname/celery.py
from django.conf import settings
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

app = Celery('report_card_system')


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Optional: Configure task routes for better organization

app.conf.task_routes = {
    'students.tasks.calculate_report_card_aggregates': {'queue': 'calculations'},
    'students.tasks.calculate_student_grade': {'queue': 'calculations'},
    'students.tasks.calculate_class_averages': {'queue': 'calculations'},
    'students.tasks.bulk_calculate_report_cards': {'queue': 'bulk_operations'},
}
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')