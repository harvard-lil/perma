import os
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.shortcuts import render
from perma.models import *
from api.tests.utils import *
from django.conf import settings
from warc_diff_tools.warc_diff_tools import expand_warcs, get_visual_diffs
import utils

@login_required
def main(request, guid):
    """
    here, we want to grab the guid coming in, and create a new archive of it
    we then do a diff on that archive using diff.warc_compare_text
    original archive: archive_one
    new archive: archive_two
    """
    # limitation: can only compare public links for now
    # maybe this is solved by temporarily allowing users to view, until archive gets deleted or transferred over

    # create link using diff_user@example.com's api key
    # move warc over the actual user if they want to keep it
    # all warcs should be deleted forever from diff user every 24 hours

    archive_one = Link.objects.get(guid=guid)
    api_url = "http://localhost:8000/api/v1/archives/?api_key=%s" % settings.DIFF_API_KEY
    response = requests.post(api_url, data={'url': archive_one.submitted_url})
    new_guid = response.json().get('guid')
    # archive_one = Link.objects.get(guid="AA3S-SQ55")
    archive_two = Link.objects.get(guid=new_guid)
    max_size = settings.MAX_ARCHIVE_FILE_SIZE / 1024 / 1024
    protocol = "https://" if settings.SECURE_SSL_REDIRECT else "http://"

    warc_one = os.path.join(default_storage.base_location, archive_one.warc_storage_file())
    warc_two = os.path.join(default_storage.base_location, archive_two.warc_storage_file())

    expanded_one, expanded_two = expand_warcs(warc_one, warc_two, archive_one.submitted_url, archive_two.submitted_url)

    html_one = archive_one.replay_url(archive_one.submitted_url).data
    html_two = archive_two.replay_url(archive_two.submitted_url).data

    rewritten_html_one = utils.rewrite_html(html_one, archive_one.guid)
    rewritten_html_two = utils.rewrite_html(html_two, archive_two.guid)

    deleted, inserted, combined = get_visual_diffs(rewritten_html_one, rewritten_html_two)

    utils.write_to_static(deleted, '_deleted_{0}_{1}.html'.format(archive_one.guid, archive_two.guid))
    utils.write_to_static(inserted, '_inserted_{0}_{1}.html'.format(archive_one.guid, archive_two.guid))
    utils.write_to_static(combined, '_combined_{0}_{1}.html'.format(archive_one.guid, archive_two.guid))

    context = {
        'archive_one': archive_one,
        'archive_two': archive_two,
        'archive_one_capture': archive_one.primary_capture,
        'this_page': 'single_link',
        'max_size': max_size,
        'link_url': settings.HOST + '/' + archive_one.guid,
        'protocol': protocol,
        'archive_two_capture': archive_two.primary_capture,
    }


    return render(request, 'comparison.html', context)
