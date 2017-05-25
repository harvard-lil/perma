import os, subprocess, uuid
from io import BytesIO
from StringIO import StringIO
from tempfile import NamedTemporaryFile

import requests
from PIL import Image, ImageOps, ImageEnhance
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.conf import settings

from compare.models import *
from compare.models import Compare
import compare.utils as utils

from perma.models import Link
from htmldiff import diff
#from htmldiff import settings as diff_settings
from warc_compare import WARCCompare


# ignore guids in html
diff_settings = {'EXCLUDE_STRINGS_A': [], 'EXCLUDE_STRINGS_B': [],
                 'STYLE_STR': '',
                 'DIFF_API_KEY': '5485b838d0745944383f38835a98d825affbb9d8',}

# add own style string
#diff_settings.STYLE_STR = settings.DIFF_STYLE_STR

@login_required
def capture_create(request, old_guid):
    """
    here, we want to grab the guid coming in, and create a new archive of it
    we then do a diff on that archive using diff.warc_compare_text
    OUTL"""

    old_archive = Link.objects.get(guid=old_guid)
    api_url = "http://localhost:8000/api/v1/archives/?api_key=%s" % '5485b838d0745944383f38835a98d825affbb9d8'
    response = requests.post(api_url, data={'url': old_archive.submitted_url})
    # limitation: can only compare public links for now
    # maybe this is solved by temporarily allowing users to view, until archive gets deleted or transferred over

    # create link using diff_user@example.com's api key
    # move warc over the actual user if they want to keep it
    # all warcs should be deleted forever from diff user every 24 hours

    # old_archive = Link.objects.get(guid=guid)

    new_guid = response.json().get('guid')
    compare = Compare(old_guid=old_guid, guid=new_guid, created_by=old_archive.created_by)
    compare.save()
    # old_archive = Link.objects.get(guid="AA3S-SQ55")
    # new_archive = Link.objects.get(guid=new_guid)

    # context = { 'old_guid': old_guid, 'new_guid': new_guid }
    return HttpResponseRedirect(reverse('capture_compare', kwargs={ 'old_guid': old_guid, 'new_guid': new_guid}))

def capture_compare(request, old_guid, new_guid):
    protocol = "https://" if settings.SECURE_SSL_REDIRECT else "http://"

    if request.GET.get('type'):
        # if type "image", serve here
        return
    else:
        # check if comparison directory exists yet
        old_archive = Link.objects.get(guid=old_guid)
        new_archive = Link.objects.get(guid=new_guid)
        old_warc_path = os.path.join(default_storage.base_location, old_archive.warc_storage_file())
        new_warc_path = os.path.join(default_storage.base_location, new_archive.warc_storage_file())
        wc = WARCCompare(old_warc_path, new_warc_path)

        if not utils.compare_dir_exists(old_guid, new_guid):
            """
            create new comparison directory for these two guids
            """
            utils.create_compare_dir(old_guid, new_guid)

            html_one = old_archive.replay_url(old_archive.submitted_url).data
            html_two = new_archive.replay_url(new_archive.submitted_url).data

            rewritten_html_one = utils.rewrite_html(html_one, old_archive.guid)
            rewritten_html_two = utils.rewrite_html(html_two, new_archive.guid)

            # ignore guids in html
            diff_settings.EXCLUDE_STRINGS_A.append(str(old_guid))
            diff_settings.EXCLUDE_STRINGS_B.append(str(new_guid))

            # add own style string
            diff_settings.STYLE_STR = settings.DIFF_STYLE_STR

            deleted, inserted, combined = diff.text_diff(rewritten_html_one, rewritten_html_two)

            utils.write_to_static(deleted, 'deleted.html', old_guid, new_guid)
            utils.write_to_static(inserted, 'inserted.html', old_guid, new_guid)
            utils.write_to_static(combined, 'combined.html', old_guid, new_guid)
        resource_count = {
            'missing': len(wc.resources['missing']),
            'added': len(wc.resources['added']),
            'modified': len(wc.resources['modified']),
            'unchanged': len(wc.resources['unchanged']),
        }
        context = {
            'old_archive': old_archive,
            'new_archive': new_archive,
            'old_archive_capture': old_archive.primary_capture,
            'new_archive_capture': new_archive.primary_capture,
            'this_page': 'comparison',
            'link_url': settings.HOST + '/' + old_archive.guid,
            'protocol': protocol,
            'resource_count': resource_count,
        }

        return render(request, 'comparison.html', context)

def image_compare(request, old_guid):
    '''
    here we get the old guid, and the new guid and create two three different
    images that we'll display the user

    1  the new_guid - the old_guid with the additions in blue
    2  the old_giud - the new_guid with the subtractions in orange
    3  a thumbnail that is a summary of the changes that we can display the the user

    '''

    ####
    ## generate image described in 1
    ####

    # get old archive and if we have a screenshot, get the replay url
    # for that image and download it
    old_archive = Link.objects.get(guid=old_guid)
    old_screenshot_capture = old_archive.captures.filter(role='screenshot').first()

    if old_screenshot_capture.status == 'success':
        capture_replay_url = 'http:%s' % old_screenshot_capture.playback_url_with_access_token()
        r = requests.get(capture_replay_url)
        old_image = Image.open(StringIO(r.content))
        old_image_temp_file = NamedTemporaryFile(delete=False)
        old_image.save(old_image_temp_file, 'PNG', quality=98)

        # We now have our old_image, let's create a new image
        # of the same url

        api_url = "http://localhost:8000/api/v1/archives/?api_key=%s" % '5485b838d0745944383f38835a98d825affbb9d8'
        response = requests.post(api_url, data={'url': old_archive.submitted_url})
        new_guid = response.json().get('guid')

        new_archive = Link.objects.get(guid=new_guid)
        new_screenshot_capture = new_archive.captures.filter(role='screenshot').first()
        capture_replay_url = 'http:%s' % new_screenshot_capture.playback_url_with_access_token()
        r = requests.get(capture_replay_url)
        new_image = Image.open(StringIO(r.content))
        new_image_temp_file = NamedTemporaryFile(delete=False)
        new_image.save(new_image_temp_file, 'PNG', quality=98)

        # TODO: our images need to be the same size to compare
        #if old_image.height != new_image.height:

        # And we have our newly created png of the archive, let's create
        # a difference image
        diff_image_temp_file = NamedTemporaryFile(delete=False)
        print subprocess.call(['/usr/local/bin/convert', new_image_temp_file.name,
            old_image_temp_file.name, '-alpha', 'off', '+repage', '(',
            '-clone', '0', '-clone', '1', '-compose', 'difference', '-composite',
            '-threshold', '0', ')', '-delete', '1', '-fuzz', '70%', '-alpha', 'off', '-compose', 'copy_opacity',
            '-composite', diff_image_temp_file.name])

        # save our compare work into our model along wiht our newly created difference image
        compare = Compare(original_guid=old_guid, guid=new_guid, created_by=old_archive.created_by,)
        compare.save()
        compare.image_diff.save(diff_image_temp_file.name, ContentFile(diff_image_temp_file.read()))

        diff_image = Image.open(compare.image_diff)

        # our diff image appears too dark, lighten it up
        def tint_image(src, color="#FFFFFF"):
            src.load()
            r, g, b, alpha = src.split()
            gray = ImageOps.grayscale(src)
            result = ImageOps.colorize(gray, (0, 0, 0, 0), color)
            result.putalpha(alpha)
            return result

        diff_image = tint_image(diff_image, "#DD671A")

        # save our lightened diff image back to our model
        f = BytesIO()
        try:
            diff_image.save(f, format='png')
            compare.image_diff.save(compare.image_diff.name,  ContentFile(f.getvalue()))
        finally:
            f.close()

        # Now that we have a good diff image, let's create a good looking,
        # thumbnial of it
        background = old_image
        enhancer = ImageEnhance.Contrast(background)
        background = enhancer.enhance(.3)

        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(1.1)

        foreground = Image.open(compare.image_diff)
        background.paste(foreground, (0, 0), foreground)

        basewidth = 150
        wpercent = (basewidth/float(background.size[0]))
        hsize = int((float(background.size[1])*float(wpercent)))
        thumbed = background.resize((basewidth,hsize), Image.ANTIALIAS)

        # and again, save our claned up image (thumbnail) back our model
        f = BytesIO()
        try:
            thumbed.save(f, format='png')
            compare.image_diff_thumb.save(str(uuid.uuid4()), ContentFile(f.getvalue()))
        finally:
            f.close()

        new_image.close()
        old_image.close()
        diff_image_temp_file.close()

    # Done processing. files closed. return images to user

    protocol = "https://" if settings.SECURE_SSL_REDIRECT else "http://"

    context = {
        'old_archive': old_archive,
        'old_archive_capture': old_screenshot_capture.playback_url_with_access_token(),
        'new_archive': new_archive,
        'compare': compare,
        'link_url': settings.HOST + '/' + old_archive.guid,
        'protocol': protocol,
    }


    return render(request, 'comparison-single-pane.html', context)

def list(request, old_guid):
    protocol = "https://" if settings.SECURE_SSL_REDIRECT else "http://"

    compared_archives = Compare.objects.filter(original_guid=old_guid)
    old_archive = Link.objects.get(pk=old_guid)

    context = {
        'old_archive': old_archive,
        'archives': compared_archives,
        'protocol': protocol,
    }

    return render(request, 'list.hcomtml', context)

def get_resource_list(request, old_guid, new_guid):
    old_archive = Link.objects.get(guid=old_guid)
    new_archive = Link.objects.get(guid=new_guid)
    old_warc_path = os.path.join(default_storage.base_location, old_archive.warc_storage_file())
    new_warc_path = os.path.join(default_storage.base_location, new_archive.warc_storage_file())
    wc = WARCCompare(old_warc_path, new_warc_path)

    ### TODO: ordering

    similarity = wc.calculate_similarity()
    resources = []
    for status in wc.resources:
        for content_type in wc.resources[status]:
            urls = wc.resources[status][content_type]
            for url in urls:
                resource = {
                    'url':url,
                    'content_type': content_type,
                    'status': status,
                }

                if status == 'modified' and 'image' not in content_type:
                    resource['simhash'] = similarity[url]['simhash']
                    resource['minhash'] = similarity[url]['minhash']

                if url == old_archive.submitted_url:
                    resources.insert(0, resource)
                else:
                    resources.append(resource)


    return JsonResponse(resources, safe=False)
