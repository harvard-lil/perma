import os
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.shortcuts import render
from compare.models import *
from perma.models import Link
from compare.models import Compare
from django.conf import settings
import htmldiff
from warc_diff_tools.warc_diff_tools import expand_warcs, get_visual_diffs
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
import requests
import utils

@login_required
def capture_create(request, original_guid):
    """
    here, we want to grab the guid coming in, and create a new archive of it
    we then do a diff on that archive using diff.warc_compare_text
    original archive: archive_one
    new archive: archive_two
    """

    archive_one = Link.objects.get(guid=original_guid)
    api_url = "http://localhost:8000/api/v1/archives/?api_key=%s" % settings.DIFF_API_KEY
    response = requests.post(api_url, data={'url': archive_one.submitted_url})
    # limitation: can only compare public links for now
    # maybe this is solved by temporarily allowing users to view, until archive gets deleted or transferred over

    # create link using diff_user@example.com's api key
    # move warc over the actual user if they want to keep it
    # all warcs should be deleted forever from diff user every 24 hours

    # archive_one = Link.objects.get(guid=guid)

    new_guid = response.json().get('guid')
    compare = Compare(original_guid=original_guid, guid=new_guid, created_by=archive_one.created_by)
    compare.save()
    # archive_one = Link.objects.get(guid="AA3S-SQ55")
    # archive_two = Link.objects.get(guid=new_guid)

    # context = { 'original_guid': original_guid, 'new_guid': new_guid }
    return HttpResponseRedirect(reverse('capture_compare', kwargs={ 'original_guid': original_guid, 'new_guid': new_guid}))

def capture_compare(request, original_guid, new_guid):
    protocol = "https://" if settings.SECURE_SSL_REDIRECT else "http://"

    if request.GET.get('type'):
        # if type "image", serve here
        return
    else:

        archive_one = Link.objects.get(guid=original_guid)
        archive_two = Link.objects.get(guid=new_guid)

        warc_one = os.path.join(default_storage.base_location, archive_one.warc_storage_file())
        warc_two = os.path.join(default_storage.base_location, archive_two.warc_storage_file())

        expanded_one, expanded_two = expand_warcs(warc_one, warc_two, archive_one.submitted_url, archive_two.submitted_url)

        html_one = archive_one.replay_url(archive_one.submitted_url).data
        html_two = archive_two.replay_url(archive_two.submitted_url).data

        rewritten_html_one = utils.rewrite_html(html_one, archive_one.guid)
        rewritten_html_two = utils.rewrite_html(html_two, archive_two.guid)

        # ignore guids in html
        htmldiff.settings.EXCLUDE_STRINGS_A.append(str(original_guid))
        htmldiff.settings.EXCLUDE_STRINGS_B.append(str(new_guid))

        # add own style string
        htmldiff.settings.STYLE_STR = settings.DIFF_STYLE_STR

        deleted, inserted, combined = get_visual_diffs(rewritten_html_one, rewritten_html_two)

        utils.write_to_static(deleted, '_deleted_{0}_{1}.html'.format(archive_one.guid, archive_two.guid))
        utils.write_to_static(inserted, '_inserted_{0}_{1}.html'.format(archive_one.guid, archive_two.guid))
        utils.write_to_static(combined, '_combined_{0}_{1}.html'.format(archive_one.guid, archive_two.guid))

        context = {
            'original_archive': archive_one,
            'new_archive': archive_two,
            'original_archive_capture': archive_one.primary_capture,
            'new_archive_capture': archive_two.primary_capture,
            'this_page': 'comparison',
            'link_url': settings.HOST + '/' + archive_one.guid,
            'protocol': protocol,
        }

        return render(request, 'comparison.html', context)

def image_compare(request, original_guid, new_guid):
    return render(request)

def list(request, original_guid):
    protocol = "https://" if settings.SECURE_SSL_REDIRECT else "http://"

    compared_archives = Compare.objects.filter(original_guid=original_guid)
    original_archive = Link.objects.get(pk=original_guid)

    context = {
        'original_archive': original_archive,
        'archives': compared_archives,
        'protocol': protocol,
    }

    return render(request, 'list.html', context)
