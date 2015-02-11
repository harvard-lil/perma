from datetime import timedelta
import logging, json
from datetime import datetime

from django.shortcuts import HttpResponse, get_object_or_404

from perma.models import Link


logger = logging.getLogger(__name__)


def get_url(request):
    """
    Return a GUID for an arbitrary URL
    Usage:    /api/linky/urldump/get?url=<whatever you want>
    Response: {guid: "XXX"}
    """
    ### XXX some day we should probably cache this and/or use some
    ### sort of sweet checkpointing system, but this is a start
    link_object = get_object_or_404(Link, submitted_url=request.GET.__getitem__('url'))
    return HttpResponse(json.dumps({'guid': link_object.guid}), 'application/json')

def urldump(request, since=None):
    """
    Give basic JSON encoding of GUID/URL pairs created since 'since'
    """
    ### XXX some day we should probably cache this and/or use some
    ### sort of sweet checkpointing system, but this is a start
    if since is None:
        dt = datetime.now() - timedelta(days=1)
    else:
        dt = datetime.strptime(since, "%Y-%m-%d")
    links = Link.objects.filter(creation_timestamp__gte=dt)
    data = []
    for link in links:
        datum = {'guid': link.guid, 'url': link.submitted_url}
        data.append(datum)
    response = json.dumps(data)
    return HttpResponse(response, 'application/json')
