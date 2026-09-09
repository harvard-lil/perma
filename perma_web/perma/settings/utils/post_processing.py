### settings post-checks
# here we do stuff that should be checked or fixed after ALL settings from any source are loaded
# this is called by __init__.py

from celery.schedules import crontab
import os

def post_process_settings(settings):

    # Set up Sentry instrumentation
    if settings['USE_SENTRY']:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration

        sentry_sdk.init(
            environment=settings['SENTRY_ENVIRONMENT'],
            dsn=settings['SENTRY_DSN'],
            integrations=[
                DjangoIntegration(),
                CeleryIntegration(),
            ],
            enable_tracing=True,

            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=settings['SENTRY_TRACES_SAMPLE_RATE'],

            # If you wish to associate users to errors (assuming you are using
            # django.contrib.auth) you may enable sending PII data.
            send_default_pii=settings['SENTRY_SEND_DEFAULT_PII']
        )

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
            'task': 'perma.celery_tasks.cache_playback_status_for_new_links',
            'schedule': crontab(hour='*', minute='30'),
        },
        'run-next-capture': {
            'task': 'perma.celery_tasks.run_next_capture',
            'schedule': crontab(minute='*'),
        },
        'sync_subscriptions_from_perma_payments': {
            'task': 'perma.celery_tasks.sync_subscriptions_from_perma_payments',
            'schedule': crontab(hour='23', minute='0')
        },
        'queue_internet_archive_pending_work': {
            'task': 'perma.celery_tasks.queue_internet_archive_pending_work',
            'schedule': crontab(minute="*/5"),
            'args': (
                os.environ.get('IA_UPLOAD_START_DATESTRING') or None,
                os.environ.get('IA_UPLOAD_END_DATESTRING') or None
            )
        },
        'queue_internet_archive_privacy_toggled_still_pending': {
            'task': 'perma.celery_tasks.queue_internet_archive_privacy_toggled_still_pending',
            'schedule': crontab(hour='3', minute='0'),
        },
        'confirm_files_uploaded_to_internet_archive': {
            'task': 'perma.celery_tasks.queue_file_uploaded_confirmation_tasks',
            'schedule': crontab(minute="2-59/5"),
        },
        'confirm_files_deleted_from_internet_archive': {
            'task': 'perma.celery_tasks.queue_file_deleted_confirmation_tasks',
            'schedule': crontab(minute="2-59/5"),
        },
        'deactivate_expired_sponsored_users': {
            'task': 'perma.celery_tasks.deactivate_expired_sponsored_users',
            'schedule': crontab(hour='6', minute='0'),
        },
        'warn_expiring_sponsored_users': {
            'task': 'perma.celery_tasks.warn_expiring_sponsored_users',
            'schedule': crontab(hour='6', minute='0'),
        },
        'remove_expired_organization_user_affiliations': {
            'task': 'perma.celery_tasks.remove_expired_organization_user_affiliations',
            'schedule': crontab(hour='6', minute='15'),
        },
        'warn_expiring_organization_users': {
            'task': 'perma.celery_tasks.warn_expiring_organization_users',
            'schedule': crontab(hour='6', minute='15'),
        }
    }
    settings['CELERY_BEAT_SCHEDULE'] = dict(((job, celerybeat_job_options[job]) for job in settings.get('CELERY_BEAT_JOB_NAMES', [])),
                                           **settings.get('CELERY_BEAT_SCHEDULE', {}))


    # set up Payments App URLS
    assert 'STRIPE_PAYMENTS_APP_EXTERNAL_URL' in settings and settings['STRIPE_PAYMENTS_APP_EXTERNAL_URL'] is not None, "Set DJANGO__STRIPE_PAYMENTS_APP_EXTERNAL_URL env var!"
    assert 'STRIPE_PAYMENTS_APP_INTERNAL_URL' in settings and settings['STRIPE_PAYMENTS_APP_INTERNAL_URL'] is not None, "Set DJANGO__STRIPE_PAYMENTS_APP_INTERNAL_URL env var!"
    settings['PAYMENTS_APP_URLS'] = {
        'purchase': f"{settings['STRIPE_PAYMENTS_APP_EXTERNAL_URL']}/purchase/",
        'purchase_history': f"{settings['STRIPE_PAYMENTS_APP_INTERNAL_URL']}/purchase-history/",
        'acknowledge_purchase': f"{settings['STRIPE_PAYMENTS_APP_INTERNAL_URL']}/acknowledge-purchase/",
        'subscribe': f"{settings['STRIPE_PAYMENTS_APP_EXTERNAL_URL']}/subscribe/",
        'subscription_status': f"{settings['STRIPE_PAYMENTS_APP_INTERNAL_URL']}/subscription/",
        'update': f"{settings['STRIPE_PAYMENTS_APP_EXTERNAL_URL']}/update/",
        'change': f"{settings['STRIPE_PAYMENTS_APP_EXTERNAL_URL']}/change/",
        'billing': f"{settings['STRIPE_PAYMENTS_APP_EXTERNAL_URL']}/billing/",
    }
