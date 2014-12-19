from multiprocessing.pool import ThreadPool
import os
import os.path
import tempfile
from urlparse import urljoin
from celery import shared_task
import requests

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.core import serializers
from django.db import transaction, connection

from .utils import sign_post_data
from .models import UpdateQueue

### helpers ###

def send_request(target_server, url, method='GET', **request_kwargs):
    """
        target_server is a dict with 'address':'https://...' and optional 'request_kwargs':{<<stuff to pass to requests.request>>}.
    """
    request_kwargs.update(target_server.get('request_kwargs', {}))

    if url.startswith('//'):
        # if url has no protocol, default to https
        url = 'https:' + url
    elif not (url.startswith('http:') or url.startswith('https:')):
        # elif url is relative, prepend with target_server address
        url = urljoin(target_server['address'], url)

    return requests.request(method, urljoin(target_server['address'], url), **request_kwargs)

def post_message_upstream(relative_url, json_data={}, **request_kwargs):
    """ Make a request to the upstream server. """
    if 'data' not in request_kwargs:
        request_kwargs['data'] = sign_post_data(json_data)

    return send_request(settings.UPSTREAM_SERVER, relative_url, 'POST', **request_kwargs)

def post_message_downstream(relative_url, json_data={}, **request_kwargs):
    """ Make a request to all downstream requests in parallel threads, returning when all are finished. """

    if 'data' not in request_kwargs:
        request_kwargs['data'] = sign_post_data(json_data)

    def call_downstream_request(mirror):
        print "MAIN: Sending update to", mirror['address']
        send_request(mirror, relative_url, 'POST', **request_kwargs)

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
        post_message_downstream(reverse("mirroring:import_updates"), json_data={'updates': list(updates)})
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
        result = post_message_upstream(reverse('mirroring:export_updates'), json_data={'last_known_update':last_known_update_id}).json()
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

    def save_cache(obj_cache):
        if obj_cache:
            print "Saving %s objects of type %s." % (len(obj_cache), type(obj_cache[0]))
            Model = type(obj_cache[0])
            Model.objects.filter(pk__in=[obj.pk for obj in obj_cache]).delete()
            print "Deleted."
            Model.objects.bulk_create(obj_cache)
            print "Done saving."
            del obj_cache[:]


    temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    data_stream = post_message_upstream(reverse('mirroring:export_database'), stream=True)
    for chunk in data_stream.iter_content(chunk_size=1024):
        temp_file.write(chunk)
    temp_file.file.close()

    print "Got data file."

    # call_command("loaddata", temp_file.name)
    # temp_file.unlink(temp_file.name)
    #
    # print "Full DB loaded."


    with connection.constraint_checks_disabled():
        # update_index = None
        obj_cache = []
        for line in temp_file:
            obj = serializers.deserialize("json", line).next().object
            if len(obj_cache) > 1000 or (obj_cache and type(obj_cache[0]) != type(obj)):
                save_cache(obj_cache)
            if not obj_cache:
                print line
            obj_cache.append(obj)

        print "Final save."

        save_cache(obj_cache)

    print "Done!"

    # if update_index:
    #     UpdateQueue.objects.get_or_create(pk=update_index, defaults={'json': 'dummy'})


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

    post_message_downstream(reverse("mirroring:media_sync"), json_data={
        'paths': expanded_paths,
    })


@shared_task
def background_media_sync(*args, **kwargs):
    paths = kwargs['paths']
    upstream_media_url = settings.UPSTREAM_SERVER.get('media_url', settings.UPSTREAM_SERVER['address']+'/media/')
    for path in paths:
        request_url = urljoin(upstream_media_url, path)
        print "Storing ", request_url
        request = send_request(settings.UPSTREAM_SERVER, request_url, stream=True)
        default_storage.store_file(request.raw, path)
