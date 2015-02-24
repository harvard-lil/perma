import gzip
from multiprocessing.pool import ThreadPool
import os
import os.path
import tempfile
from urlparse import urljoin
from celery import shared_task
from celery.contrib import rdb
import requests

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.core import serializers
from django.db import transaction, connection

from .utils import sign_post_data, get_gpg, get_fingerprint
from .models import UpdateQueue
import perma.models

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
    pool.map(call_downstream_request, settings.DOWNSTREAM_SERVERS)
    pool.close()

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
        post_message_upstream(reverse('mirroring:export_database'))
        return

    try:
        result = post_message_upstream(reverse('mirroring:export_updates'), json_data={'last_known_update':last_known_update_id}).json()
    except Exception as e:  # TODO: narrow this down
        # upstream server doesn't have the updates we need; fetch whole database
        print "MIRROR: Error fetching updates: %s. Fetching whole database." % e
        post_message_upstream(reverse('mirroring:export_database'))
        return

    # import updates
    if result:
        print "MIRROR: Got %s updates. Updating." % len(result)
        UpdateQueue.import_updates(result)
    else:
        print "MIRROR: No results received from upstream."


@shared_task
@transaction.atomic
def save_full_database(*args, **kwargs):
    lock = get_update_queue_lock()

    # helpers
    def send_database_dump_downstream(file_path, update_id):
        post_message_downstream(reverse("mirroring:import_database"),
                                json_data={'file_path': file_path, 'update_id': update_id})

    # first check if there is an existing dump we can send
    downstream_server = kwargs['downstream_server']
    downstream_key = get_fingerprint(downstream_server['public_key'])
    dump_dir = 'database_dumps/%s' % (downstream_key)
    if default_storage.exists(dump_dir):
        files = default_storage.listdir(dump_dir)[1]
        for file_name in files:
            file_path = os.path.join(dump_dir, file_name)
            try:
                UpdateQueue.objects.get(pk=file_name)
                send_database_dump_downstream(file_path, int(file_name))
                return
            except UpdateQueue.DoesNotExist:
                # dump is no longer useful -- doesn't catch us up to existing deltas
                default_storage.delete(file_path)

    # no existing dump, let's create one ...

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    gzip_temp_file = gzip.GzipFile(temp_file.name, mode='wb', compresslevel=1)
    encrypted_temp_file = tempfile.NamedTemporaryFile(delete=False)
    encrypted_temp_file.close()

    try:
        update_index = UpdateQueue.objects.order_by('-pk')[0]
    except IndexError:
        update_index = None

    for attr in dir(perma.models):
        Model = getattr(perma.models, attr)
        if hasattr(Model, 'mirror_fields'):
            print "SENDING %s objects." % Model.objects.count()
            for obj in Model.objects.all():
                gzip_temp_file.write(serializers.serialize("json", [obj], fields=Model.mirror_fields, ensure_ascii=False).encode('utf8')+"\n")

    if update_index:
        gzip_temp_file.write(serializers.serialize("json", [update_index], fields=['action', 'json'], ensure_ascii=False).encode('utf8')+"\n")

    gzip_temp_file.close()

    get_gpg().encrypt_file(open(temp_file.name, 'rb'),
                           recipients=[downstream_key],
                           sign=get_fingerprint(settings.GPG_PRIVATE_KEY),
                           armor=False,
                           output=encrypted_temp_file.name,
                           always_trust=True)  # trust that our keys are valid

    update_id = update_index.pk if update_index else 0
    file_path = 'database_dumps/%s/%s' % (downstream_key, update_id)
    default_storage.store_file(open(encrypted_temp_file.name, 'rb'), file_path, overwrite=True, send_signal=False)

    os.remove(encrypted_temp_file.name)
    os.remove(temp_file.name)

    send_database_dump_downstream(file_path, update_id)


@shared_task
@transaction.atomic
def get_full_database(*args, **kwargs):
    """
        Fetch full database from upstream.
    """
    lock = get_update_queue_lock()

    # first check that we still need this update
    file_path = kwargs['file_path']
    update_id = kwargs['update_id']
    if UpdateQueue.objects.filter(pk__gte=update_id).count():
        return

    # download encrypted file
    upstream_media_url = settings.UPSTREAM_SERVER.get('media_url', settings.UPSTREAM_SERVER['address']+'/media/')
    data_stream = send_request(settings.UPSTREAM_SERVER, urljoin(upstream_media_url, file_path), stream=True)
    # encrypted_temp_file = tempfile.TemporaryFile()
    # for chunk in data_stream.iter_content(1024):
    #     encrypted_temp_file.write(chunk)
    # encrypted_temp_file.seek(0)

    # decrypt
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    get_gpg().decrypt_file(data_stream.raw, output=temp_file.name, always_trust=True)
    gzip_temp_file = gzip.GzipFile(temp_file.name, mode='rb')

    print "Got data file."

    def save_cache(obj_cache):
        if obj_cache:
            print "Saving %s objects of type %s." % (len(obj_cache), type(obj_cache[0]))
            Model = type(obj_cache[0])
            Model.objects.filter(pk__in=[obj.pk for obj in obj_cache]).delete()
            print "Deleted."
            Model.objects.bulk_create(obj_cache)
            print "Done saving."
            del obj_cache[:]

    with connection.constraint_checks_disabled():
        # update_index = None
        obj_cache = []
        for line in gzip_temp_file:
            obj = serializers.deserialize("json", line.decode('utf8')).next().object
            if len(obj_cache) > 1000 or (obj_cache and type(obj_cache[0]) != type(obj)):
                save_cache(obj_cache)
            if not obj_cache:
                print line
            obj_cache.append(obj)

        print "Final save."

        save_cache(obj_cache)

    gzip_temp_file.close()
    os.remove(temp_file.name)

    print "Done!"


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
        # TODO: might be better to buffer this to a local file instead of storing it in RAM
        try:
            response = send_request(settings.UPSTREAM_SERVER, request_url)
            assert response.ok
        except (requests.ConnectionError, AssertionError):
            print "Warning: unable to fetch file %s" % request_url
            continue
        default_storage.store_data_to_file(response.content, path)


@shared_task
def integrity_check(*args, **kwargs):
    check_count = max(1, perma.models.Asset.objects.count()/30/24/12)
    for asset in perma.models.Asset.objects.order_by('last_integrity_check')[:check_count]:
        print "Verifying %s" % asset.link_id
        asset.verify_media()
