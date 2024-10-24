
# via http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
# this file has to be called celery.py so it will be found by the celery command

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perma.settings', )

app = Celery('perma')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(related_name="celery_tasks")
