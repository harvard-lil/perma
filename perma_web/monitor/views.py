import uuid, json
from django.conf import settings
from monitor.tasks import get_screencap
from django.http import HttpResponse

# Create your views here.
def monitor_archive(request):
    """
    We want our monitoring tool to keep on eye or our ability
    to create archives. Sometimes things break and this rough
    test can help us know when things break.

    We expect a url GET parameter

    TODO: This simply creates an image. We should be monitoring
    more. Do it.
    """

    file_name = "%s.png" % uuid.uuid4()

    get_screencap.delay(request.GET['url'], file_name)

    # Hopefully we have a sreencap task running. Let's send the path to the user
    url_to_image = getattr(settings, 'MONITOR_URL') + file_name

    return HttpResponse(json.dumps({'url_to_image': url_to_image}), content_type="application/json")