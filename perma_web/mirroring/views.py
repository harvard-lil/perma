import json

from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from perma.utils import run_task
from perma.views.common import single_linky

from .models import UpdateQueue, SYNCED_MODELS
from .tasks import get_updates, background_media_sync
from .utils import may_be_mirrored


def single_link_json(request, guid):
    """
        This is a version of the single link page that can only be called on the main server.
        It gets called as JSON (by the regular single link page on a mirror) and returns
        the data necessary for the mirror to render the page.
    """
    return single_linky(request, guid)


@may_be_mirrored
def export_updates(request):
    """
        Return updates to database since last_known_update, if we still have that update stored,
        or else return 400 Bad Request.
    """
    try:
        last_known_update_id = int(request.GET['last_known_update'])
    except (KeyError, ValueError):
        return HttpResponseBadRequest('Invalid value for last_known_update.')
    updates = UpdateQueue.objects.filter(pk__gte=last_known_update_id).values('pk', 'action', 'json')
    if not updates or updates[0]['pk'] != last_known_update_id:
        return HttpResponseBadRequest('Delta from id %s not available.' % last_known_update_id)
    return HttpResponse(json.dumps(list(updates[1:])), content_type="application/json")


@may_be_mirrored
def export_database(request):
    """
        Get JSON dump of entire DB.
    """
    try:
        update_index = UpdateQueue.objects.order_by('-pk')[0].pk
    except IndexError:
        update_index = 0
    out = {
        'update_index': update_index,
        'database': [(Model.__name__, serializers.serialize("json", Model.objects.all())) for Model in SYNCED_MODELS]
    }
    return HttpResponse(json.dumps(out), content_type="application/json")



# TODO: PGP sign all messages.


@may_be_mirrored
@csrf_exempt
def import_updates(request):
    """
        Receive a set of updates and apply them.
    """
    print "MIRROR: Receiving updates:"
    updates = json.loads(request.POST['updates'])
    print "%s updates." % len(updates)
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
@csrf_exempt
def media_sync(request):
    """
        Receive a set of updates and apply them. We run this in a celery task so we can return immediately.
    """
    print "MIRROR: Receiving media sync"
    run_task(background_media_sync, media_url=request.POST['media_url'], paths=json.loads(request.POST['paths']))
    return HttpResponse("OK")
