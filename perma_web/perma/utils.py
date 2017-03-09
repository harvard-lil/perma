import socket
from contextlib import contextmanager
import operator
from urlparse import urlparse
import os
import tempdir
from datetime import datetime
import logging
from netaddr import IPAddress, IPNetwork
from functools import wraps

from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.decorators import available_attrs
from django.contrib.auth.decorators import login_required


logger = logging.getLogger(__name__)


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

### read only mode ###

class ReadOnlyException(Exception):
    pass

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

def json_serial(obj):
        """
        JSON serializer for objects not serializable by default json code

        Thanks, http://stackoverflow.com/a/22238613
        """

        if isinstance(obj, datetime):
            serial = obj.isoformat()
            return serial
        raise TypeError ("Type not serializable")

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
    if settings.LIMIT_TO_TRUSTED_PROXY:
        proxy_ip = IPAddress(request.META['REMOTE_ADDR'])
        if any(proxy_ip in IPNetwork(trusted_ip_range) for trusted_ip_range in settings.TRUSTED_PROXIES):
            try:
                return request.META[settings.TRUSTED_PROXY_HEADER]
            except KeyError:
                raise PermissionDenied
        raise PermissionDenied
    else:
        return request.META.get('HTTP_X_FORWARDED_FOR', request.META['REMOTE_ADDR'])
