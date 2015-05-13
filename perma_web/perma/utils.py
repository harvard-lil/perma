from contextlib import contextmanager
import operator
import os

from django.db.models import Q
from django.conf import settings
import struct
import tempdir


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

### simple search ###

def get_search_query(target, search_string, fields):
    """
        For the given `target` (either a Model or QuerySet),
        apply consecutive .filter()s such that each word
        in `search_string` appears in one of the `fields`.
    """
    # get words in search_string
    required_words = search_string.strip().split()
    if not required_words:
        return target

    # if we got a Model, turn into a QuerySet
    if hasattr(target, 'objects'):
        target = target.objects

    for required_word in required_words:
        # apply the equivalent of target = target.filter(Q(field1__icontains=required_word) | Q(field2__icontains=required_word) | ...)
        query_parts = [Q(**{field+"__icontains":required_word}) for field in fields]
        query_parts_joined = reduce(operator.or_, query_parts, Q())
        target = target.filter(query_parts_joined)

    return target
    
### url manipulation ###

def absolute_url(request, url):
    """
        Get absolute URL for relative URL based on request.
        We wrap Django's version to also check for '//' absolute links.
    """
    if url.startswith('//'):
        return url
    return request.build_absolute_uri(url)

def direct_media_url(url):
    """
        Given a URL that includes MEDIA_URL, convert it to include DIRECT_MEDIA_URL instead if that is set.
    """
    if not settings.DIRECT_MEDIA_URL:
        return url
    return url.replace(settings.MEDIA_URL, settings.DIRECT_MEDIA_URL, 1)

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