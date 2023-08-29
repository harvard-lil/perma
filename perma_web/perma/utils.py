from contextlib import contextmanager
from collections import OrderedDict
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from functools import wraps, reduce
import hashlib
from hanzo import warctools
import itertools
import json
import logging
from nacl import encoding
from nacl.public import Box, PrivateKey, PublicKey
from netaddr import IPAddress, IPNetwork
import operator
import os
import requests
import ssl
import socket
import string
import surt
import tempdir
import tempfile
from ua_parser import user_agent_parser
import unicodedata
from urllib.parse import urlparse
from urllib3 import poolmanager
from warcio.warcwriter import BufferWARCWriter
from wsgiref.util import FileWrapper

from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseForbidden, Http404, StreamingHttpResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .exceptions import InvalidTransmissionException, ScoopAPIException

logger = logging.getLogger(__name__)
warn = logger.warn


def protocol():
    return "https://" if settings.SECURE_SSL_REDIRECT else "http://"


### requests helpers ###

class Sec1TLSAdapter(requests.adapters.HTTPAdapter):
    """
    Debian Buster and its version of OpenSSL evidently set a minimum TLS version of 1.2,
    and there's a problem that results in SSL: DH_KEY_TOO_SMALL errors, for some websites.
    Lower the security standard for our requests, per https://github.com/psf/requests/issues/4775
    """

    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')

        # for whatever reason, required for verify=False
        ctx.check_hostname = False
        self.poolmanager = poolmanager.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_version=ssl.PROTOCOL_TLS,
                ssl_context=ctx)

    def cert_verify(self, conn, url, verify, cert):
        super().cert_verify(conn, url, False, cert)


### login helpers ###

def user_passes_test_or_403(test_func):
    """
    Decorator for views that checks that the user passes the given test,
    raising PermissionDenied if not. Based on Django's user_passes_test.
    The test should be a callable that takes the user object and
    returns True if the user passes.
    """
    def decorator(view_func):
        @login_required()
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not test_func(request.user):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def cooloff_time():
    return timedelta(minutes=settings.AXES_COOLOFF_MINUTES)

### password helper ###

class AlphaNumericValidator:
    """
    Adapted from https://djangosnippets.org/snippets/2551/
    """

    @sensitive_variables()
    def validate(self, password, user=None):
        contains_number = contains_upper = contains_lower = False
        for char in password:
            if not contains_number:
                if char in string.digits:
                    contains_number = True
            if not contains_upper:
                if char in string.ascii_uppercase:
                    contains_upper = True
            if not contains_lower:
                if char in string.ascii_lowercase:
                    contains_lower = True
            if all((contains_number, contains_upper, contains_lower)):
                break

        if not all((contains_number, contains_upper, contains_lower)):
            raise ValidationError("This password must include an uppercase letter, \
                                   a lowercase letter, and a number.")

    def get_help_text(self):
        return "Your password must include an uppercase letter, \
                a lowercase letter, and a number."


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
    try:
        return paginator.page(page)
    except EmptyPage:
        return paginator.page(1)

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

            if request.user.is_authenticated:
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


def first_day_of_next_month(now):
    # use first of month instead of today to avoid issues w/ variable length months
    first_of_month = now.replace(day=1)
    return first_of_month + relativedelta(months=1)


def today_next_year(now):
    # relativedelta handles leap years: 2/29 -> 2/28
    return now + relativedelta(years=1)


### addresses ###

def get_lat_long(address):
    r = None
    try:
        r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', {'address': address, 'key':settings.GEOCODING_KEY})
    except Exception as e:
        warn(f"Error connecting to geocoding API: {e}")
    if r and r.status_code == 200:
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
            warn(f"Unknown response from geocoding API: {status}")
    else:
        warn(f"Error connecting to geocoding API: {r.status_code}")


def parse_user_agent(user_agent_str):
    # if user_agent_str is unparseable, will return:
    # {'brand': None, 'model': None, 'family': 'Other'}
    return user_agent_parser.ParseUserAgent(user_agent_str)

def user_agent_for_domain(target_domain):
    capture_user_agent = settings.CAPTURE_USER_AGENT
    if any(domain in target_domain for domain in settings.DOMAINS_REQUIRING_UNIQUE_USER_AGENT):
        capture_user_agent = capture_user_agent + f" {settings.PERMA_USER_AGENT_SUFFIX}"
    if any(domain in target_domain for domain in settings.DOMAINS_REQUIRING_BOT_USER_AGENT):
        capture_user_agent = capture_user_agent + f" {settings.PERMABOT_USER_AGENT_SUFFIX}"
    return capture_user_agent

### pdf handling on mobile ###

def redirect_to_download(capture_mime_type, user_agent_str):
    # redirecting to a page with a download button (and not attempting to display)
    # if mobile apple device, and the request is a pdf
    parsed_agent = parse_user_agent(user_agent_str)

    return parsed_agent["family"] and capture_mime_type and \
           "Mobile" in parsed_agent["family"] and "pdf" in capture_mime_type

### memento

def url_with_qs_and_hash(url, qs_and_hash=None):
    if qs_and_hash:
        url = f"{url}?{qs_and_hash}"
    return url

def url_split(url):
    """ Separate into base and query + hash"""
    return url.split('?', 1)

def timemap_url(request, url, response_format):
    base, *qs_and_hash = url_split(url)
    return url_with_qs_and_hash(
        request.build_absolute_uri(reverse('timemap', args=[response_format, base])),
        qs_and_hash[0] if qs_and_hash else ''
    )

def timegate_url(request, url):
    base, *qs_and_hash = url_split(url)
    return url_with_qs_and_hash(
        request.build_absolute_uri(reverse('timegate', args=[base])),
        qs_and_hash[0] if qs_and_hash else ''
    )

def memento_url(request, link):
    return request.build_absolute_uri(reverse('single_permalink', args=[link.guid]))

def memento_data_for_url(request, url, qs=None, hash=None):
    from perma.models import Link  #noqa
    try:
        canonicalized = surt.surt(url)
    except ValueError:
        return {}
    mementos = [
        {
            'uri': memento_url(request, link),
            'datetime': link.creation_timestamp,
        } for link in Link.objects.visible_to_memento().filter(submitted_url_surt=canonicalized).order_by('creation_timestamp')
    ]
    if not mementos:
        return {}
    return {
        'self': request.build_absolute_uri(),
        'original_uri': url,
        'timegate_uri': timegate_url(request, url),
        'timemap_uri': {
            'json_format': timemap_url(request, url, 'json'),
            'link_format': timemap_url(request, url, 'link'),
            'html_format': timemap_url(request, url, 'html'),
        },
        'mementos': {
            'first': mementos[0],
            'last': mementos[-1],
            'list': mementos,
        }
    }


def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

def remove_whitespace(s):
    return ''.join(s.split())


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
        logger.warning(f'Problem with transmitted data. {format_exception(e)}')
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

def pp_date_from_post(posted_value):
    if posted_value:
        return datetime.strptime(posted_value, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
    return None


def format_exception(e):
    return f"{type(e).__name__}: {e}"


@sensitive_variables()
def retrieve_fields(transmitted_data, fields):
    try:
        data = {}
        for field in fields:
            data[field] = transmitted_data[field]
    except KeyError as e:
        msg = f'Incomplete data received: missing {e}'
        logger.warning(msg)
        raise InvalidTransmissionException(msg)
    return data


def is_valid_timestamp(stamp, max_age):
    return stamp <= (datetime.utcnow() + timedelta(seconds=max_age)).timestamp()


@sensitive_variables()
def stringify_data(data):
    """
    Takes any json-serializable data. Converts to a bytestring, suitable for passing to an encryption function.
    """
    return bytes(json.dumps(data, cls=DjangoJSONEncoder), 'utf-8')


@sensitive_variables()
def unstringify_data(data):
    """
    Reverses stringify_data. Takes a bytestring, returns deserialized json.
    """
    return json.loads(str(data, 'utf-8'))


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
def preserve_perma_warc(guid, timestamp, destination, warc_size):
    """
    Context manager for opening a perma warc, ready to receive warc records.
    Safely closes and saves the file to storage when context is exited.
    """
    # mode set to 'ab+' as a workaround for https://bugs.python.org/issue25341
    out = tempfile.TemporaryFile('ab+')
    write_perma_warc_header(out, guid, timestamp)
    try:
        yield out
    finally:
        out.flush()
        warc_size.append(out.tell())
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
        bytes(f'Perma-GUID: {guid}', 'utf-8')
    ]
    data = b'\r\n'.join(warcinfo_fields) + b'\r\n'
    warcinfo_record = warctools.WarcRecord(headers=headers, content=(b'application/warc-fields', data))
    warcinfo_record.write_to(out_file, gzip=True)


def make_detailed_warcinfo(filename, guid, coll_title, coll_desc, rec_title, pages):
    # #
    # Thank you! Rhizome/Webrecorder.io/Ilya Kreymer
    # #

    coll_metadata = {'type': 'collection',
                     'title': coll_title,
                     'desc': coll_desc}

    rec_metadata = {'type': 'recording',
                    'title': rec_title,
                    'pages': pages}

    # Coll info
    writer = BufferWARCWriter(gzip=True)
    params = OrderedDict([('operator', 'Perma.cc download'),
                          ('Perma-GUID', guid),
                          ('format', 'WARC File Format 1.0'),
                          ('json-metadata', json.dumps(coll_metadata))])

    record = writer.create_warcinfo_record(filename, params)
    writer.write_record(record)

    # Rec Info
    params['json-metadata'] = json.dumps(rec_metadata)

    record = writer.create_warcinfo_record(filename, params)
    writer.write_record(record)

    return writer.get_contents()


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
    warc_date = warctools.warc.warc_datetime_str(timezone.now()).replace(b'+00:00Z', b'Z')
    headers = [
        (warctools.WarcRecord.TYPE, warctools.WarcRecord.RESOURCE),
        (warctools.WarcRecord.ID, warctools.WarcRecord.random_warc_uuid()),
        (warctools.WarcRecord.DATE, warc_date),
        (warctools.WarcRecord.URL, bytes(url, 'utf-8')),
        (warctools.WarcRecord.BLOCK_DIGEST, bytes(f'sha1:{hashlib.sha1(data).hexdigest()}', 'utf-8'))
    ]
    if extra_headers:
        headers.extend(extra_headers)
    record = warctools.WarcRecord(headers=headers, content=(bytes(content_type, 'utf-8'), data))
    record.write_to(out_file, gzip=True)

def get_warc_stream(link, stream=True):
    filename = f"{link.guid}.warc.gz"

    timestamp = link.creation_timestamp.strftime('%Y%m%d%H%M%S')

    warcinfo = make_detailed_warcinfo(
        filename = filename,
        guid = link.guid,
        coll_title = f'Perma Archive, {link.submitted_title}',
        coll_desc = link.submitted_description,
        rec_title = f'Perma Archive of {link.submitted_title}',
        pages= [{
            'title': link.submitted_title,
            'url': link.submitted_url,
            'timestamp': timestamp
        }]
    )

    warc_stream = FileWrapper(default_storage.open(link.warc_storage_file()))
    warc_stream = itertools.chain([warcinfo], warc_stream)
    if stream:
        response = StreamingHttpResponse(warc_stream, content_type="application/gzip")
    else:
        response = HttpResponse(warc_stream, content_type="application/gzip")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def stream_warc(link, stream=True):
    # `link.user_deleted` is checked here for dev convenience:
    # it's easy to forget that deleted links/warcs aren't truly deleted,
    # and easy to accidentally permit the downloading of "deleted" warcs.
    # Users of stream_warc shouldn't have to worry about / remember this.
    if link.user_deleted or not link.can_play_back():
        raise Http404
    return get_warc_stream(link, stream)

def stream_warc_if_permissible(link, user, stream=True):
    if user.can_view(link):
        return stream_warc(link, stream)
    return HttpResponseForbidden('Private archive.')


#
# Internet Archive
#

def get_ia_session():
    import internetarchive
    patch_internet_archive(internetarchive)

    config = {"s3": {"access": settings.INTERNET_ARCHIVE_ACCESS_KEY, "secret": settings.INTERNET_ARCHIVE_SECRET_KEY}}
    return internetarchive.get_session(config=config, http_adapter_kwargs={"max_retries": 0})


def patch_internet_archive(ia_module):
    """
    Patch a custom method into the Internet Archive's `ArchiveSession`.
    """

    def get_s3_load_info(self, identifier=None, access_key=None, request_kwargs=None):
        """
        This is identical to the IA session's s3_is_overloaded method, except
        it also returns the complete response, which is expected to be JSON of the form:
            {
                'bucket': '<identifier>'|None,
                'detail': {
                    'accesskey_ration': <int>,
                    'accesskey_tasks_queued': <int>,
                    'bucket_ration': <int>,
                    'bucket_tasks_queued': <int>,
                    'limit_reason': <str>,
                    'rationing_engaged': <int>,
                    'rationing_level': <int>,
                    'total_global_limit': <int>,
                    'total_tasks_queued': <int>
                },
                'over_limit': 0|1
            }

        https://github.com/jjjake/internetarchive/blob/8c13eb021bd3afb52d56b49151be24317f0cdca6/internetarchive/session.py#L325-L344
        """
        request_kwargs = request_kwargs or {}
        if 'timeout' not in request_kwargs:
            request_kwargs['timeout'] = 12

        u = f'{self.protocol}//s3.us.archive.org'
        p = {
            'check_limit': 1,
            'accesskey': access_key,
            'bucket': identifier,
        }
        try:
            r = self.get(u, params=p, **request_kwargs)
        except Exception:
            return (True, {})
        try:
            j = r.json()
        except ValueError:
            return (True, {})
        # remove our access key, if present, from the response
        try:
            del j['accesskey']
        except KeyError:
            pass
        return (j.get('over_limit') != 0, j)

    ia_module.ArchiveSession.get_s3_load_info = get_s3_load_info


def get_complete_ia_rate_limiting_info(include_buckets=True, include_max_buckets=100):
    """
    Return information on all known Internet Archive rate limits and their current status.
    """
    # import here to prevent circular references; lots of files import from utils.py
    from perma.models import InternetArchiveItem  # noqa
    import internetarchive  # noqa
    patch_internet_archive(internetarchive)

    ia_session = get_ia_session()

    def get_task_info(cmd):
        # Some available tasks are listed at https://archive.org/developers/tasks.html#supported-tasks,
        # but information about others, such as modify_xml.php, is also exposed by this API.
        #
        # Uploads and deletes, handled by the S3-like API (https://archive.org/developers/ias3.html)
        # are also subject to rate limiting, but their limits are described by a different API:
        # see `get_s3_load_info`.
        try:
            data = ia_session.get_tasks_api_rate_limit(cmd=cmd)
        except requests.exceptions.ConnectionError:
            return None
        return {
            "tasks_limit": data["value"]["tasks_limit"],
            "tasks_inflight": data["value"]["tasks_inflight"],
            "tasks_blocked_by_offline": data["value"]["tasks_blocked_by_offline"]
        }

    def update_general_s3_info(output, s3_details):
        output["general_s3"]["accesskey_ration"] = s3_details.get("detail", {}).get("accesskey_ration")
        output["general_s3"]["accesskey_tasks_queued"] = s3_details.get("detail", {}).get("accesskey_tasks_queued")
        output["general_s3"]["total_global_limit"] = s3_details.get("detail", {}).get('total_global_limit')
        output["general_s3"]["total_tasks_queued"] = s3_details.get("detail", {}).get('total_tasks_queued')

    def add_bucket_info(output, bucket, s3_details):
        output["buckets"][bucket] = {
            "bucket_ration": s3_details.get("detail", {}).get("bucket_ration"),
            "bucket_tasks_queued": s3_details.get("detail", {}).get("bucket_tasks_queued")
        }

    def record_over_limit_details(output, s3_is_overloaded, s3_details):
        # Until we understand better how these rate limits work and how information is
        # communicated, keep a copy of the complete response whenever it looks like a
        # rate limit has been exceeded or is approaching. May be empty: when the API
        # is truly overloaded, it sometimes fails to return a response at all, in which
        # case s3_is_overloaded is True and s3_details is {}.
        if s3_is_overloaded or s3_details.get("detail", {}).get("rationing_engaged"):
            output["over_limit_details"].append(s3_details)

    output = {
        "modify_xml": get_task_info('modify_xml.php'),
        "derive": get_task_info('derive.php'),
        "general_s3": {},
        "buckets": {},
        "over_limit_details": []
    }

    # check s3 accesskey and global limits first, without specifying a bucket
    s3_is_overloaded, s3_details = ia_session.get_s3_load_info(access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY)
    update_general_s3_info(output, s3_details)
    record_over_limit_details(output, s3_is_overloaded, s3_details)

    # check for bucket-specific limits
    if include_buckets:
        buckets = InternetArchiveItem.objects.filter(tasks_in_progress__gt=0).values_list('identifier', flat=True).order_by('identifier')
        if include_max_buckets:
            buckets = buckets[:include_max_buckets]
        for bucket in buckets:
            s3_is_overloaded, s3_details = ia_session.get_s3_load_info(identifier=bucket, access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY)
            add_bucket_info(output, bucket, s3_details)
            # each bucket-specific response will include updated general rate limit info
            update_general_s3_info(output, s3_details)
            record_over_limit_details(output, s3_is_overloaded, s3_details)

    return output


def ia_global_task_limit_approaching(s3_details):
    if not s3_details:
        # if the API is so hampered that it didn't return a response, assume it's too overloaded for us
        return True
    return s3_details['detail']['total_global_limit'] - s3_details['detail']['total_tasks_queued'] - settings.INTERNET_ARCHIVE_PERMITTED_PROXIMITY_TO_GLOBAL_RATE_LIMIT <= 0


def ia_perma_task_limit_approaching(s3_details):
    if not s3_details:
        # if the API is so hampered that it didn't return a response, assume it's too overloaded for us
        return True
    return s3_details['detail']['accesskey_ration'] - s3_details['detail']['accesskey_tasks_queued'] - settings.INTERNET_ARCHIVE_PERMITTED_PROXIMITY_TO_RATE_LIMIT <= 0


def ia_bucket_task_limit_approaching(s3_details):
    if not s3_details:
        # if the API is so hampered that it didn't return a response, assume it's too overloaded for us
        return True
    return s3_details['detail']['bucket_ration'] - s3_details['detail']['bucket_tasks_queued'] - settings.INTERNET_ARCHIVE_PERMITTED_PROXIMITY_TO_RATE_LIMIT <= 0


def date_range(start_date, end_date, delta):
    current = start_date
    while current <= end_date:
        yield current
        current += delta


#
# Scoop Helpers
#

def safe_get_response_json(response):
    try:
        data = response.json()
    except ValueError:
        data = {}
    return data

def send_to_scoop(method, path, valid_if, json=None, stream=False):
    # Make the request
    try:
        response = requests.request(
            method,
            settings.SCOOP_API_URL + path,
            json=json,
            headers={
                "Access-Key": settings.SCOOP_API_KEY
            },
            timeout=10,
            allow_redirects=False,
            stream=stream
        )
    except requests.exceptions.RequestException as e:
        raise ScoopAPIException() from e

    # Validate the response
    try:
        data = safe_get_response_json(response)
        assert valid_if(response.status_code, data)
    except AssertionError:
        raise ScoopAPIException(f"{response.status_code}: {str(data)}")

    return response, data
