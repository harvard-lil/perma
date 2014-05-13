import os, uuid, json
from django.conf import settings
from perma.tasks import test_screencap
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

    relative_file_path = ['monitor', "%s.png" % uuid.uuid4()]

    path_elements = [getattr(settings, 'MEDIA_ROOT')] + relative_file_path
    disk_path = os.path.join(*path_elements)

    test_screencap.delay(request.GET['url'], disk_path)

    # Hopefully we have a sreencap task running. Let's send the path to the user
    url_to_image = getattr(settings, 'MEDIA_URL') + '/'.join(relative_file_path)

    return HttpResponse(json.dumps({'url_to_image': url_to_image}), content_type="application/json")