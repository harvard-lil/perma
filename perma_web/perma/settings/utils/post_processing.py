### settings post-checks
# here we do stuff that should be checked or fixed after ALL settings from any source are loaded
# this is called by __init__.py

from celery.schedules import crontab
from celery.task.control import inspect as celery_inspect

def post_process_settings(settings):

    # check secret key
    assert 'SECRET_KEY' in settings and settings['SECRET_KEY'] is not None, "Set DJANGO__SECRET_KEY env var!"

    # Deal with custom setting for CELERY_TASK_DEFAULT_QUEUE.
    # Changing CELERY_TASK_DEFAULT_QUEUE only changes the queue name,
    # but we need it to change the exchange and routing_key as well.
    # See http://celery.readthedocs.org/en/latest/userguide/routing.html#changing-the-name-of-the-default-queue
    try:
        default_queue = settings['CELERY_TASK_DEFAULT_QUEUE']
        if default_queue != "celery":
            from kombu import Exchange, Queue
            settings['CELERY_TASK_QUEUES'] = (Queue(default_queue, Exchange(default_queue), routing_key=default_queue),)
    except KeyError:
        # no custom setting for CELERY_TASK_DEFAULT_QUEUE
        pass

    # add the named celerybeat jobs
    celerybeat_job_options = {
        'cache_playback_status_for_new_links': {
            'task': 'perma.tasks.cache_playback_status_for_new_links',
            'schedule': crontab(hour='*', minute='30'),
        },
        'update-stats': {
            'task': 'perma.tasks.update_stats',
            'schedule': crontab(minute='*'),
        },
        'send-links-to-internet-archive': {
            'task': 'perma.tasks.upload_all_to_internet_archive',
            'schedule': crontab(minute='0', hour='*'),
        },
        'delete-links-from-internet-archive': {
            'task': 'perma.tasks.delete_all_from_internet_archive',
            'schedule': crontab(minute='0', hour='*'),
        },
        'send-js-errors': {
            'task': 'perma.tasks.send_js_errors',
            'schedule': crontab(hour='10', minute='0', day_of_week=1)
        },
        'run-next-capture': {
            'task': 'perma.tasks.run_next_capture',
            'schedule': crontab(minute='*'),
        },
        'sync_subscriptions_from_perma_payments': {
            'task': 'perma.tasks.sync_subscriptions_from_perma_payments',
            'schedule': crontab(hour='23', minute='0')
        },
        'verify_webrecorder_api_available': {
            'task': 'perma.tasks.verify_webrecorder_api_available',
            'schedule': crontab(minute='*')
        }
    }
    settings['CELERY_BEAT_SCHEDULE'] = dict(((job, celerybeat_job_options[job]) for job in settings.get('CELERY_BEAT_JOB_NAMES', [])),
                                           **settings.get('CELERY_BEAT_SCHEDULE', {}))

    # Count celery capture workers, by convention named w1, w2, etc.
    # At the moment, this is slow, so we do it once on application
    # start-up rather than at each load of the /manage/create page.
    # The call to inspector.active() takes almost two seconds.
    try:
        inspector = celery_inspect()
        active = inspector.active()
        settings['WORKER_COUNT'] = len([key for key in active.keys() if key.split('@')[0][0] == 'w']) if active else 0
    except TimeoutError:
        pass
