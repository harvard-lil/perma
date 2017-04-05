import os
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
import requests
from django.shortcuts import render
from perma.models import *
from api.tests.utils import *
from django.conf import settings
from diff.warc_compare_text import *

@login_required
def diff_entry(request, guid):
    """
    here, we want to grab the guid coming in, and create a new archive of it
    we then do a diff on that archive using diff.warc_compare_text.*
    """
    # limitation: can only compare public links for now
        # maybe this is solved by temporarily allowing users to view, until archive gets deleted or transferred over

    # create link using diff_user@example.com's api key
    # move warc over the actual user if they want to keep it
    # all warcs should be deleted forever from diff user every 24 hours

    diff_user = LinkUser.objects.get(email='diff_user@example.com')
    # old_archive = Link.objects.get(guid=guid)
    api_url = "http://localhost:8000/api/v1/archives/?api_key=%s" % settings.DIFF_API_KEY

    # response = requests.post(api_url, data={'url': old_archive.submitted_url})
    # new_guid = response.json().get('guid')
    old_archive = Link.objects.get(guid="AA3S-SQ55")
    new_archive = Link.objects.get(guid="U75F-W8DK")
    max_size = settings.MAX_ARCHIVE_FILE_SIZE / 1024 / 1024
    protocol = "https://" if settings.SECURE_SSL_REDIRECT else "http://"

    warc_one = os.path.join(default_storage.base_location, old_archive.warc_storage_file())
    warc_two = os.path.join(default_storage.base_location, new_archive.warc_storage_file())
    compare_warcs(warc_one, warc_two, old_archive.submitted_url, new_archive.submitted_url)

    context = {
        'old_archive': old_archive,
        'can_view': request.user.can_view(old_archive),
        'can_delete': request.user.can_delete(old_archive),
        'can_toggle_private': request.user.can_toggle_private(old_archive),
        'old_archive_capture': old_archive.primary_capture,
        'serve_type': 'sdfsdf',
        'this_page': 'single_link',
        'max_size': max_size,
        'link_url': settings.HOST + '/' + old_archive.guid,
        'protocol': protocol,
        'new_archive_capture': new_archive.primary_capture,
    }


    response = render(request, 'panoramic.html', context)
    return response
