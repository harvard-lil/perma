### settings post-checks
# here we do stuff that should be checked or fixed after ALL settings from any source are loaded
# this is called by __init__.py

from celery.schedules import crontab

def post_process_settings(settings):

    # check secret key
    assert 'SECRET_KEY' in settings and settings['SECRET_KEY'] is not None, "Set DJANGO__SECRET_KEY env var!"

    # Deal with custom setting for CELERY_DEFAULT_QUEUE.
    # Changing CELERY_DEFAULT_QUEUE only changes the queue name,
    # but we need it to change the exchange and routing_key as well.
    # See http://celery.readthedocs.org/en/latest/userguide/routing.html#changing-the-name-of-the-default-queue
    try:
        default_queue = settings['CELERY_DEFAULT_QUEUE']
        if default_queue != "celery":
            from kombu import Exchange, Queue
            settings['CELERY_QUEUES'] = (Queue(default_queue, Exchange(default_queue), routing_key=default_queue),)
    except KeyError:
        # no custom setting for CELERY_DEFAULT_QUEUE
        pass

    # add the named celerybeat jobs
    celerybeat_job_options = {
        # primary server
        'update-stats': {
            'task': 'perma.tasks.update_stats',
            'schedule': crontab(minute='*'),
        },
        'cleanup-screencap-monitoring': {
            'task': 'monitor.tasks.delete_screencaps',
            'schedule': crontab(minute='35', hour='*/2'),  # every other hour
        },
    }
    settings['CELERYBEAT_SCHEDULE'] = dict(((job, celerybeat_job_options[job]) for job in settings.get('CELERYBEAT_JOB_NAMES', [])),
                                           **settings.get('CELERYBEAT_SCHEDULE', {}))
