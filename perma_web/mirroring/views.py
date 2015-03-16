import json

from django.http import HttpResponse, HttpResponseBadRequest

from perma.utils import run_task
from perma.models import Link, Asset
from perma.views.common import single_linky

from .models import UpdateQueue
from .tasks import get_updates, background_media_sync, save_full_database, get_full_database
from .utils import may_be_mirrored, read_downstream_request, read_upstream_request


@read_downstream_request
def single_link_json(request, request_server, guid):
    """
        This is a version of the single link page that can only be called on the main server.
        It gets called as JSON (by the regular single link page on a mirror) and returns
        the data necessary for the mirror to render the page.
    """
    return single_linky(request, guid, send_downstream=True)


@may_be_mirrored
@read_downstream_request
def export_updates(request, request_server, last_known_update):
    """
        Return updates to database since last_known_update, if we still have that update stored,
        or else return 400 Bad Request.
    """
    try:
        last_known_update_id = int(last_known_update)
    except (KeyError, ValueError):
        return HttpResponseBadRequest('Invalid value for last_known_update.')
    updates = UpdateQueue.objects.filter(pk__gte=last_known_update_id).values('pk', 'action', 'json')
    if not updates or updates[0]['pk'] != last_known_update_id:
        return HttpResponseBadRequest('Delta from id %s not available.' % last_known_update_id)
    return HttpResponse(json.dumps(list(updates[1:])), content_type="application/json")


@may_be_mirrored
@read_downstream_request
def export_database(request, request_server):
    """
        Return JSON dump of mirrored portions of entire DB.
    """
    run_task(save_full_database, downstream_server=request_server)
    return HttpResponse("OK")


@may_be_mirrored
@read_upstream_request
def import_updates(request, request_server, updates):
    """
        Receive a set of updates and apply them.
    """
    print "MIRROR: Receiving %s updates." % len(updates)
    start_id = updates[0]['pk']
    existing_delta_count = UpdateQueue.objects.filter(pk__gte=start_id-1).count()
    if not existing_delta_count:
        print "MIRROR: Previous update not found; queuing delta fetch."
        run_task(get_updates)
        return HttpResponse("OK")
    if existing_delta_count > 1:
        print "MIRROR: Stripping %s deltas already received." % (existing_delta_count-1)
        updates = updates[existing_delta_count-1:]
    if updates:
        print "MIRROR: Importing %s updates." % (len(updates))
        UpdateQueue.import_updates(updates)
    return HttpResponse("OK")


@may_be_mirrored
@read_upstream_request
def media_sync(request, request_server, paths):
    """
        Receive a set of updates and apply them. We run this in a celery task so we can return immediately.
    """
    print "MIRROR: Receiving media sync"
    run_task(background_media_sync, paths=paths)
    return HttpResponse("OK")


@may_be_mirrored
@read_upstream_request
def import_database(request, request_server, file_path, update_id):
    """
        Receive a set of updates and apply them. We run this in a celery task so we can return immediately.
    """
    print "MIRROR: Asked to save full database -- %s" % file_path
    run_task(get_full_database, file_path=file_path, update_id=update_id)
    return HttpResponse("OK")


@may_be_mirrored
@read_upstream_request
def get_status(request, request_server):
    status = {
        'total_archives': Link.objects.count(),
        'verified_archives': Asset.objects.filter(integrity_check_succeeded=True).count(),
        'failed_archives': Asset.objects.filter(integrity_check_succeeded=False).count(),
    }
    return HttpResponse(json.dumps(status), content_type="application/json")