from contextlib import contextmanager
import operator
import os
import struct
import tempdir

from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings


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

def get_png_size(fh):
    data = fh.read(24)
    if len(data) < 24:
        raise IOError
    if data[:8] != '\211PNG\r\n\032\n' or data[12:16] != 'IHDR':
        raise ValueError("File is not a png.")
    w, h = struct.unpack('>LL', data[16:24])
    return int(w), int(h)

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

### email ###

def send_contact_email(title, content, from_address, request):
    """
        Send a message on behalf of a user to the admins.
        Use reply-to for the user address so we can use email services that require authenticated from addresses.
    """

    # append user agent and from email
    user_agent = ''
    if request:
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    content += """

----
User email: %s
User agent: %s
""" % (from_address, user_agent)

    # send message
    EmailMessage(
        title,
        content,
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
        headers={'Reply-To': from_address}
    ).send(fail_silently=False)