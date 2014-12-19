import json

from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest, StreamingHttpResponse

from perma.utils import run_task
from perma.views.common import single_linky
import perma.models

from .models import UpdateQueue
from .tasks import get_updates, background_media_sync
from .utils import may_be_mirrored, read_downstream_request, read_upstream_request


# cache models to sync downstream, based on whether they have a 'mirror_fields' attribute
SYNCED_MODELS = []
for attr in dir(perma.models):
    item = getattr(perma.models, attr)
    if hasattr(item, 'mirror_fields'):
        SYNCED_MODELS.append(item)


def single_link_json(request, guid):
    """
        This is a version of the single link page that can only be called on the main server.
        It gets called as JSON (by the regular single link page on a mirror) and returns
        the data necessary for the mirror to render the page.
    """
    return single_linky(request, guid)


@may_be_mirrored
@read_downstream_request
def export_updates(request, last_known_update):
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
def export_database(request):
    """
        Return JSON dump of mirrored portions of entire DB.
    """
    try:
        update_index = UpdateQueue.objects.order_by('-pk')[0]
    except IndexError:
        update_index = None

    def generate_lines():
        for Model in SYNCED_MODELS:
            print "SENDING %s objects." % Model.objects.count()
            for obj in Model.objects.all():
                yield serializers.serialize("json", [obj], fields=Model.mirror_fields, ensure_ascii=False)+"\n"

        if update_index:
            yield serializers.serialize("json", [update_index], fields=['action', 'json'], ensure_ascii=False)+"\n"

    return StreamingHttpResponse(generate_lines(), content_type="application/json")


@may_be_mirrored
@read_upstream_request
def import_updates(request, updates):
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
def media_sync(request, paths):
    """
        Receive a set of updates and apply them. We run this in a celery task so we can return immediately.
    """
    print "MIRROR: Receiving media sync"
    run_task(background_media_sync, paths=paths)
    return HttpResponse("OK")
