import json
from multiprocessing.pool import ThreadPool
import os
import os.path
from urlparse import urljoin
from celery import shared_task
from celery.contrib import rdb
import requests

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.core import serializers
from django.db import transaction

from .utils import sign_post_data
from .models import UpdateQueue

### helpers ###

def upstream_request(relative_url, json_data={}, **request_kwargs):
    """ Make a request to the upstream server. """
    request_kwargs.setdefault('headers', settings.UPSTREAM_SERVER.get('headers', {}))
    if 'data' not in request_kwargs:
        request_kwargs['data'] = sign_post_data(json_data)
    return requests.request('POST', urljoin(settings.UPSTREAM_SERVER['address'], relative_url), **request_kwargs)

def downstream_request(downstream_server, relative_url, json_data={}, **request_kwargs):
    """ Make a request to the downstream server. """
    request_kwargs.setdefault('headers', downstream_server.get('headers', {}))
    if 'data' not in request_kwargs:
        request_kwargs['data'] = sign_post_data(json_data)
    return requests.request('POST', urljoin(downstream_server['address'], relative_url), **request_kwargs)

def parallel_downstream_request(relative_url, json_data={}, **request_kwargs):
    """ Make a request to all downstream requests in parallel threads, returning when all are finished. """
    if 'data' not in request_kwargs:
        request_kwargs['data'] = sign_post_data(json_data)

    def call_downstream_request(mirror):
        print "MAIN: Sending update to", mirror['address']
        downstream_request(mirror, relative_url, **request_kwargs)

    pool = ThreadPool(processes=min(len(settings.DOWNSTREAM_SERVERS), 10))
    return pool.map(call_downstream_request, settings.DOWNSTREAM_SERVERS)

def get_update_queue_lock():
    """
        Get a lock on the UpdateQueue database, using the select_for_update function.
        Successive calls to this function will block until the previous return value is destroyed.
    """
    _get_lock = lambda: UpdateQueue.objects.select_for_update().get(pk=1)
    try:
        return _get_lock()
    except UpdateQueue.DoesNotExist:
        UpdateQueue(json='dummy', pk=1).save()
        return _get_lock()


### tasks ###

@shared_task
@transaction.atomic
def send_updates():
    updates = UpdateQueue.objects.select_for_update().filter(sent=False).values('pk', 'action', 'json')
    if updates:
        print "MAIN: Sending updates %s" % ", ".join(str(update['pk']) for update in updates)
        UpdateQueue.objects.filter(pk__in=[update['pk'] for update in updates]).update(sent=True)
        parallel_downstream_request(reverse("mirroring:import_updates"), json_data={'updates': list(updates)})
    else:
        print "MAIN: Nothing to send."

@shared_task
@transaction.atomic
def get_updates():
    """
        Fetch any database updates from upstream.
    """
    lock = get_update_queue_lock()

    # fetch updates
    print "MIRROR: Fetching updates"
    try:
        last_known_update_id = UpdateQueue.objects.filter(pk__gt=1).order_by('-pk')[0].pk
    except IndexError:
        # we have no existing deltas; fetch the whole database
        print "MIRROR: No known updates, fetching whole database."
        lock = None
        return get_full_database.apply()

    try:
        result = upstream_request(reverse('mirroring:export_updates'), json_data={'last_known_update':last_known_update_id}).json()
    except Exception as e:  # TODO: narrow this down
        # upstream server doesn't have the updates we need; fetch whole database
        print "MIRROR: Error fetching updates: %s. Fetching whole database." % e
        lock = None
        return get_full_database.apply()

    # import updates
    if result:
        print "MIRROR: Got %s updates. Updating." % len(result)
        UpdateQueue.import_updates(result)
    else:
        print "MIRROR: No results received from upstream."


@shared_task
@transaction.atomic
def get_full_database():
    """
        Fetch full database from upstream.
    """
    lock = get_update_queue_lock()

    try:
        print "MIRROR: Importing full database."
        result = upstream_request(reverse('mirroring:export_database')).json()
        for model_class, serialized_models in result['database']:
            for obj in serializers.deserialize("json", serialized_models):
                obj.object.save()
        if result['update_index'] != '0':
            UpdateQueue(pk=int(result['update_index']), json='dummy').save()
    except Exception as e:
        print e
        rdb.set_trace()


@shared_task
def trigger_media_sync(*args, **kwargs):
    # replace paths that end with '/' with a list of all files inside
    print "Trigger called with", args, kwargs
    expanded_paths = []
    for path in kwargs['paths']:
        if path.endswith('/'):
            for root, dirs, files in default_storage.walk(path):
                for file in files:
                    expanded_paths.append(os.path.join(root, file))
        else:
            expanded_paths.append(path)

    parallel_downstream_request(reverse("mirroring:media_sync"), json_data={
        'paths': expanded_paths,
        'media_url': settings.DIRECT_MEDIA_URL,
    })


@shared_task
def background_media_sync(*args, **kwargs):
    paths = kwargs['paths']
    upstream_media_url = kwargs['media_url']
    for path in paths:
        request_url = urljoin(upstream_media_url, path)
        print "Storing ", request_url
        request = requests.get(request_url, stream=True)
        default_storage.store_file(request.raw, path)
