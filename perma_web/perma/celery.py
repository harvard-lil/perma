# via http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
# this file has to be called celery.py so it will be found by the celery command

from __future__ import absolute_import

import os

from celery import Celery

from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perma.settings')

app = Celery('perma')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# configure opbeat
# Imports have to come after DJANGO_SETTINGS_MODULE

if settings.USE_OPBEAT:
    from opbeat.contrib.django.models import client, logger, register_handlers
    from opbeat.contrib.celery import register_signal

    try:
        register_signal(client)
    except Exception as e:
        logger.exception('Failed installing celery hook: %s' % e)

    register_handlers()