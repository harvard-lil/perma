from contextlib import contextmanager
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from functools import wraps
import hashlib
from hanzo import warctools
import json
import logging
from nacl import encoding
from nacl.public import Box, PrivateKey, PublicKey
from netaddr import IPAddress, IPNetwork
import operator
import os
import requests
import socket
import string
import tempdir
import tempfile
import time
from ua_parser import user_agent_parser
from urlparse import urlparse

from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.decorators import available_attrs
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .exceptions import InvalidTransmissionException


logger = logging.getLogger(__name__)
warn = logger.warn


### celery helpers ###


def run_task(task, *args, **kwargs):
    """
        Run a celery task either async or directly, depending on settings.RUN_TASKS_ASYNC.
    """
    options = kwargs.pop('options', {})
    if settings.RUN_TASKS_ASYNC:
        return task.apply_async(args, kwargs, **options)
    else:
        return task.apply(args, kwargs, **options)

### login helper ###
def user_passes_test_or_403(test_func):
    """
    Decorator for views that checks that the user passes the given test,
    raising PermissionDenied if not. Based on Django's user_passes_test.
    The test should be a callable that takes the user object and
    returns True if the user passes.
    """
    def decorator(view_func):
        @login_required()
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if not test_func(request.user):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

### password helper ###

class AlphaNumericValidator(object):
    """
    Adapted from https://djangosnippets.org/snippets/2551/
    """

    def validate(self, password, user=None):
        contains_number = contains_letter = False
        for char in password:
            if not contains_number:
                if char in string.digits:
                    contains_number = True
            if not contains_letter:
                if char in string.letters:
                    contains_letter = True
            if contains_number and contains_letter:
                break

        if not contains_number or not contains_letter:
            raise ValidationError("This password does not include at least \
                                   one letter and at least one number.")

    def get_help_text(self):
        return "Your password must include at least \
                one letter and at least one number."


### list view helpers ###

def apply_search_query(request, queryset, fields):
    """
        For the given `queryset`,
        apply consecutive .filter()s such that each word
        in request.GET['q'] appears in one of the `fields`.
    """
    search_string = request.GET.get('q', '')
    if not search_string:
        return queryset, ''

    # get words in search_string
    required_words = search_string.strip().split()
    if not required_words:
        return queryset

    for required_word in required_words:
        # apply the equivalent of queryset = queryset.filter(Q(field1__icontains=required_word) | Q(field2__icontains=required_word) | ...)
        query_parts = [Q(**{field+"__icontains":required_word}) for field in fields]
        query_parts_joined = reduce(operator.or_, query_parts, Q())
        queryset = queryset.filter(query_parts_joined)

    return queryset, search_string

def apply_sort_order(request, queryset, valid_sorts, default_sort=None):
    """
        For the given `queryset`,
        apply sort order based on request.GET['sort'].
    """
    if not default_sort:
        default_sort = valid_sorts[0]
    sort = request.GET.get('sort', default_sort)
    if sort not in valid_sorts:
        sort = default_sort
    return queryset.order_by(sort), sort

def apply_pagination(request, queryset):
    """
        For the given `queryset`,
        apply pagination based on request.GET['page'].
    """
    try:
        page = max(int(request.GET.get('page', 1)), 1)
    except ValueError:
        page = 1
    paginator = Paginator(queryset, settings.MAX_USER_LIST_SIZE)
    return paginator.page(page)

### form view helpers ###

def get_form_data(request):
    return request.POST if request.method == 'POST' else None

### debug toolbar ###

def show_debug_toolbar(request):
    """ Used by django-debug-toolbar in settings_dev.py to decide whether to show debug toolbar. """
    return settings.DEBUG

### image manipulation ###

@contextmanager
def imagemagick_temp_dir():
    """
        Inside this context manager, the environment variable MAGICK_TEMPORARY_PATH will be set to a
        temp path that gets deleted when the context closes. This stops Wand's calls to ImageMagick
        leaving temp files around.
    """
    temp_dir = tempdir.TempDir()
    old_environ = dict(os.environ)
    os.environ['MAGICK_TEMPORARY_PATH'] = temp_dir.name
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)
        temp_dir.dissolve()

### caching ###

# via: http://stackoverflow.com/a/9377910/313561
def if_anonymous(decorator):
    """ Returns decorated view if user is not admin. Un-decorated otherwise """

    def _decorator(view):

        decorated_view = decorator(view)  # This holds the view with cache decorator

        def _view(request, *args, **kwargs):

            if request.user.is_authenticated():
                return view(request, *args, **kwargs)  # view without @cache
            else:
                return decorated_view(request, *args, **kwargs) # view with @cache

        return _view

    return _decorator

### file manipulation ###

def copy_file_data(from_file_handle, to_file_handle, chunk_size=1024*100):
    """
        Copy data from first file handle to second file handle in memory-efficient way.
    """
    while True:
        data = from_file_handle.read(chunk_size)
        if not data:
            break
        to_file_handle.write(data)

### rate limiting ###

def ratelimit_ip_key(group, request):
    return get_client_ip(request)

### monitoring ###

import opbeat

class opbeat_trace(opbeat.trace):
    """ Subclass of opbeat.trace that does nothing if settings.USE_OPBEAT is false. """
    def __call__(self, func):
        if settings.USE_OPBEAT:
            return super(opbeat_trace, self).__call__(func)
        return func

    def __enter__(self):
        if settings.USE_OPBEAT:
            try:
                return super(opbeat_trace, self).__enter__()
            except Exception as e:
                logger.exception("Error entering opbeat_trace context manager: %s" % e)

    def __exit__(self, *args, **kwargs):
        if settings.USE_OPBEAT:
            try:
                return super(opbeat_trace, self).__exit__(*args, **kwargs)
            except Exception as e:
                logger.exception("Error exiting opbeat_trace context manager: %s" % e)

### security ###

def ip_in_allowed_ip_range(ip):
    """ Return False if ip is blocked. """
    if not ip:
        return False
    ip = IPAddress(ip)
    for banned_ip_range in settings.BANNED_IP_RANGES:
        if IPAddress(ip) in IPNetwork(banned_ip_range):
            return False
    return True

def url_in_allowed_ip_range(url):
    """ Return False if url resolves to a blocked IP. """
    hostname = urlparse(url).netloc.split(':')[0]
    try:
        ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        return False
    return ip_in_allowed_ip_range(ip)

def get_client_ip(request):
    return request.META[settings.CLIENT_IP_HEADER]

### dates and times ###

def tz_datetime(*args, **kwargs):
    return timezone.make_aware(datetime(*args, **kwargs))


def to_timestamp(dt):
    """
    Replicate python3 datetime.timestamp() method (https://docs.python.org/3.3/library/datetime.html#datetime.datetime.timestamp)
    https://stackoverflow.com/a/30021134
    """
    return int((time.mktime(dt.timetuple())+ dt.microsecond/1e6))


def first_day_of_next_month(now):
    # use first of month instead of today to avoid issues w/ variable length months
    first_of_month = now.replace(day=1)
    return first_of_month + relativedelta(months=1)


def today_next_year(now):
    # relativedelta handles leap years: 2/29 -> 2/28
    return now + relativedelta(years=1)


### addresses ###

def get_lat_long(address):
    r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', {'address': address, 'key':settings.GEOCODING_KEY})
    if r.status_code == 200:
        rj = r.json()
        status = rj['status']
        if status == 'OK':
            results = rj['results']
            if len(results) == 1:
                (lat, lng) = (results[0]['geometry']['location']['lat'], results[0]['geometry']['location']['lng'])
                return (lat, lng)
            else:
                warn("Multiple locations returned for address.")
        elif status == 'ZERO_RESULTS':
            warn("No location returned for address.")
        elif status == 'REQUEST_DENIED':
            warn("Geocoding API request denied.")
        elif status == 'OVER_QUERY_LIMIT':
            warn("Geocoding API request over query limit.")
        else:
            warn("Unknown response from geocoding API: %s" % status)
    else:
        warn("Error connecting to geocoding API: %s" % r.status_code)


def parse_user_agent(user_agent_str):
    return user_agent_parser.ParseUserAgent(user_agent_str)


### pdf handling on mobile ###

def redirect_to_download(capture_mime_type, user_agent_str):
    # redirecting to a page with a download button (and not attempting to display)
    # if mobile apple device, and the request is a pdf
    parsed_agent = parse_user_agent(user_agent_str)

    return "Mobile" in parsed_agent["family"] and "pdf" in capture_mime_type


### playback

def protocol():
    return "https://" if settings.SECURE_SSL_REDIRECT else "http://"


### perma payments

# communication

@sensitive_variables()
def prep_for_perma_payments(dictionary):
    return encrypt_for_perma_payments(stringify_data(dictionary))


@sensitive_variables()
def process_perma_payments_transmission(transmitted_data, fields):
    # Transmitted data should contain a single field, 'encrypted data', which
    # must be a JSON dict, encrypted by Perma-Payments and base64-encoded.
    encrypted_data = transmitted_data.get('encrypted_data', '')
    if not encrypted_data:
        raise InvalidTransmissionException('No encrypted_data in POST.')
    try:
        post_data = unstringify_data(decrypt_from_perma_payments(encrypted_data))
    except Exception as e:
        logger.warning('Problem with transmitted data. {}'.format(format_exception(e)))
        raise InvalidTransmissionException(format_exception(e))

    # The encrypted data must include a valid timestamp.
    try:
        timestamp = post_data['timestamp']
    except KeyError:
        logger.warning('Missing timestamp in data.')
        raise InvalidTransmissionException('Missing timestamp in data.')
    if not is_valid_timestamp(timestamp, settings.PERMA_PAYMENTS_TIMESTAMP_MAX_AGE_SECONDS):
        logger.warning('Expired timestamp in data.')
        raise InvalidTransmissionException('Expired timestamp in data.')

    return retrieve_fields(post_data, fields)


# helpers

def format_exception(e):
    return "{}: {}".format(type(e).__name__, e)


@sensitive_variables()
def retrieve_fields(transmitted_data, fields):
    try:
        data = {}
        for field in fields:
            data[field] = transmitted_data[field]
    except KeyError as e:
        msg = 'Incomplete data received: missing {}'.format(e)
        logger.warning(msg)
        raise InvalidTransmissionException(msg)
    return data


def is_valid_timestamp(stamp, max_age):
    return stamp <= to_timestamp(datetime.utcnow() + timedelta(seconds=max_age))


@sensitive_variables()
def stringify_data(data):
    """
    Takes any json-serializable data. Converts to a bytestring, suitable for passing to an encryption function.
    """
    return json.dumps(data, cls=DjangoJSONEncoder, encoding='utf-8')


@sensitive_variables()
def unstringify_data(data):
    """
    Reverses stringify_data. Takes a bytestring, returns deserialized json.
    """
    return json.loads(data, 'utf-8')


@sensitive_variables()
def encrypt_for_perma_payments(message, encoder=encoding.Base64Encoder):
    """
    Basic public key encryption ala pynacl.
    """
    box = Box(
        PrivateKey(
            settings.PERMA_PAYMENTS_ENCRYPTION_KEYS['perma_secret_key'], encoder=encoder
        ),
        PublicKey(
            settings.PERMA_PAYMENTS_ENCRYPTION_KEYS['perma_payments_public_key'], encoder=encoder
        )
    )
    return box.encrypt(message, encoder=encoder)


@sensitive_variables()
def decrypt_from_perma_payments(ciphertext, encoder=encoding.Base64Encoder):
    """
    Decrypt bytes encrypted by perma-payments.
    """
    box = Box(
        PrivateKey(
            settings.PERMA_PAYMENTS_ENCRYPTION_KEYS['perma_secret_key'], encoder=encoder
        ),
        PublicKey(
            settings.PERMA_PAYMENTS_ENCRYPTION_KEYS['perma_payments_public_key'], encoder=encoder
        )
    )
    return box.decrypt(ciphertext, encoder=encoder)

#
# warc writing
#

@contextmanager
def open_warc_for_writing(guid, timestamp, destination):
    """
        Inside this context manager, the environment variable MAGICK_TEMPORARY_PATH will be set to a
        temp path that gets deleted when the context closes. This stops Wand's calls to ImageMagick
        leaving temp files around.
    """
    out = tempfile.TemporaryFile()
    write_perma_warc_header(out, guid, timestamp)
    try:
        yield out
    finally:
        out.flush()
        out.seek(0)
        default_storage.store_file(out, destination, overwrite=True)
        out.close()

def write_perma_warc_header(out_file, guid, timestamp):
    # build warcinfo header
    headers = [
        (warctools.WarcRecord.ID, warctools.WarcRecord.random_warc_uuid()),
        (warctools.WarcRecord.TYPE, warctools.WarcRecord.WARCINFO),
        (warctools.WarcRecord.DATE, warctools.warc.warc_datetime_str(timestamp))
    ]
    warcinfo_fields = [
        b'operator: Perma.cc',
        b'format: WARC File Format 1.0',
        b'Perma-GUID: %s' % guid,
    ]
    data = b'\r\n'.join(warcinfo_fields) + b'\r\n'
    warcinfo_record = warctools.WarcRecord(headers=headers, content=(b'application/warc-fields', data))
    warcinfo_record.write_to(out_file, gzip=True)


def write_warc_records_recorded_from_web(source_file_handle, out_file):
    """
    Copies a series of pre-recorded WARC Request/Response records to out_file
    """
    copy_file_data(source_file_handle, out_file)


def write_resource_record_from_asset(data, url, content_type, out_file, extra_headers=None):
    """
    Constructs a single WARC resource record from an asset (screenshot, uploaded file, etc.)
    and writes to out_file.
    """
    warc_date = warctools.warc.warc_datetime_str(timezone.now()).replace('+00:00Z', 'Z')
    headers = [
        (warctools.WarcRecord.TYPE, warctools.WarcRecord.RESOURCE),
        (warctools.WarcRecord.ID, warctools.WarcRecord.random_warc_uuid()),
        (warctools.WarcRecord.DATE, warc_date),
        (warctools.WarcRecord.URL, url),
        (warctools.WarcRecord.BLOCK_DIGEST, b'sha1:%s' % hashlib.sha1(data).hexdigest())
    ]
    if extra_headers:
        headers.extend(extra_headers)
    record = warctools.WarcRecord(headers=headers, content=(content_type, data))
    record.write_to(out_file, gzip=True)
