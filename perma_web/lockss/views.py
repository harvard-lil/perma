from urllib.parse import urljoin
from wsgiref.util import FileWrapper
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging

from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import HttpResponse, HttpResponseBadRequest, Http404, StreamingHttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from perma.models import Link
from perma.utils import get_client_ip
from .models import *

logger = logging.getLogger(__name__)

### HELPERS ###

def django_url_prefix(request):
    http_prefix = "s" if settings.SECURE_SSL_REDIRECT else ""
    return "http%s://%s" % (http_prefix, request.get_host())

def allow_by_ip(view_func):
    def authorize(request, *args, **kwargs):
        user_ip = get_client_ip(request)
        if settings.LOCKSS_DEBUG_IPS:
            logger.warn("CACHED MIRRORS: {}".format(Mirror.get_cached_mirrors()))
            logger.warn("CLIENT IP: {}".format(user_ip))
            logger.warn("request.META: {}\n".format(request.META))
        for mirror in Mirror.get_cached_mirrors():
            if user_ip == mirror['ip']:
                return view_func(request, *args, **kwargs)
        return HttpResponseForbidden()
    return authorize


### VIEWS ###

@allow_by_ip
def search(request):
    updates = Link.objects.visible_to_lockss().order_by('archive_timestamp')

    # apply from_date
    if 'updates_since' in request.GET:
        try:
            from_date = datetime.utcfromtimestamp(int(request.GET['updates_since']))
        except ValueError:
            return HttpResponseBadRequest("updates_since must be an integer and a valid timestamp.")
        updates = updates.filter(archive_timestamp__gte=from_date)

    # apply Archival Unit limits
    try:
        month = int(request.GET['creation_month'])
        year = int(request.GET['creation_year'])
    except (KeyError, ValueError):
        return HttpResponseBadRequest("creation_month and creation_year must be integers.")
    updates = updates.filter(creation_timestamp__year=year, creation_timestamp__month=month)

    # apply offset
    try:
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        return HttpResponseBadRequest("offset must be an integer.")
    updates = updates[offset:offset+1000]

    # export file names
    files_to_index = []
    for update in updates:
        files_to_index.append(update.warc_storage_file().split(settings.WARC_STORAGE_DIR+'/')[1])

    return HttpResponse("\n".join(files_to_index), content_type="text/plain")


@allow_by_ip
def fetch_warc(request, path, guid):
    # fetch link and check path is correct
    link = get_object_or_404(Link, pk=guid)
    if path.rstrip('/') != link.guid_as_path() or link.archive_timestamp is None or link.archive_timestamp > timezone.now():
        raise Http404

    # deliver warc file
    response = StreamingHttpResponse(FileWrapper(default_storage.open(link.warc_storage_file()), 1024 * 8),
                                     content_type="application/gzip")
    response['Content-Disposition'] = "attachment; filename=%s.warc.gz" % link.guid
    return response


@allow_by_ip
def permission(request):
    return HttpResponse("LOCKSS system has permission to collect, preserve, and serve this open access Archival Unit")


@allow_by_ip
def titledb(request):
    # build list of all year/month combos since we started, in the form [[2014, "01"],[2014, "02"],...]
    first_archive_date = Link.objects.order_by('creation_timestamp')[0].creation_timestamp
    start_month = date(year=first_archive_date.year, month=first_archive_date.month, day=1)
    today = date.today()
    archival_units = []
    while start_month <= today:
        archival_units.append([start_month.year, '%02d' % start_month.month])
        start_month += relativedelta(months=1)

    return render(request, 'lockss/titledb.xml', {
        'archival_units': archival_units,
        'django_url_prefix': django_url_prefix(request),
    })


@allow_by_ip
def daemon_settings(request):
    """ Generate settings files for our PLN nodes. """

    url_prefix = django_url_prefix(request)
    static_url_prefix = urljoin(url_prefix, settings.STATIC_URL)

    return render(request, 'lockss/daemon_settings.txt', {
        'django_url_prefix': url_prefix,
        'static_url_prefix': static_url_prefix,
        'mirrors': list(Mirror.objects.filter(enabled=True)),
        'content_ips': settings.LOCKSS_CONTENT_IPS,
        'quorum': settings.LOCKSS_QUORUM,
        'crawl_interval': settings.LOCKSS_CRAWL_INTERVAL,
    }, content_type="text/plain")
