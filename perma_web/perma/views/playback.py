from datetime import timedelta
from link_header import Link as Rel, LinkHeader
from ratelimit.decorators import ratelimit
from warcio.timeutils import datetime_to_http_date
from waffle import flag_is_active

from django.conf import settings
from django.core.files.storage import storages
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.cache import cache_control

from perma.celery_tasks import convert_warc_to_wacz
from perma.models import Link
from perma.utils import (if_anonymous, ratelimit_ip_key,
    memento_url, timemap_url, timegate_url,
    protocol, remove_control_characters, stream_warc_if_permissible)
from perma.wsgi_utils import retry_on_exception

import logging

logger = logging.getLogger(__name__)
valid_serve_types = ['image', 'warc_download', 'standard']


@if_anonymous(cache_control(max_age=settings.CACHE_MAX_AGES['single_permalink']))
@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.HOUR_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.DAY_LIMIT, block=True, key=ratelimit_ip_key)
def single_permalink(request, guid):
    """
    Given a Perma ID, serve it up.
    """
    # raw_user_agent = request.META.get('HTTP_USER_AGENT', '')

    # Create a canonical version of guid (non-alphanumerics removed, hyphens every 4 characters, uppercase),
    # and forward to that if it's different from current guid.
    canonical_guid = Link.get_canonical_guid(guid)

    # We only do the redirect if the correctly-formatted GUID actually exists --
    # this prevents actual 404s from redirecting with weird formatting.
    link = get_object_or_404(Link.objects.all_with_deleted(), guid=canonical_guid)

    if canonical_guid != guid:
        return HttpResponsePermanentRedirect(reverse('single_permalink', args=[canonical_guid]))

    # Forward to replacement link if replacement_link is set.
    if link.replacement_link_id:
        return HttpResponseRedirect(reverse('single_permalink', args=[link.replacement_link_id]))

    # If we get an unrecognized archive type (which could be an old type like 'live' or 'pdf'), forward to default version
    serve_type = request.GET.get('type')
    if serve_type is None:
        if link.default_to_screenshot_view:
            serve_type = 'image'
        else:
            serve_type = 'standard'
    elif serve_type not in valid_serve_types:
        return HttpResponsePermanentRedirect(reverse('single_permalink', args=[canonical_guid]))

    # serve raw WARC
    if serve_type == 'warc_download':
        return stream_warc_if_permissible(link, request.user)

    # handle requested capture type
    if serve_type == 'image':
        capture = link.screenshot_capture

        # not all Perma Links have screenshots; if no screenshot is present,
        # forward to primary capture for playback or for appropriate error message
        if (not capture or capture.status != 'success') and link.primary_capture:
            return HttpResponseRedirect(reverse('single_permalink', args=[guid])+"?type=standard")
    else:
        capture = link.primary_capture

        # if primary capture did not work, but screenshot did work, forward to screenshot
        if (not capture or capture.status != 'success') and link.screenshot_capture and link.screenshot_capture.status == 'success':
            return HttpResponseRedirect(reverse('single_permalink', args=[guid])+"?type=image")

    try:
        capture_mime_type = capture.mime_type()
    except AttributeError:
        # If capture is deleted, then mime type does not exist. Catch error.
        capture_mime_type = None

    # Special handling for mobile pdf viewing because it can be buggy
    # Redirecting to a download page if on mobile
    # redirect_to_download_view = redirect_to_download(capture_mime_type, raw_user_agent)
    # [!] TEMPORARY WORKAROUND (07-07-2023):
    # Users reported not being able to download PDFs on mobile.
    # Trying to playback PDFs on mobile instead until this is sorted out (seems to be working ok).
    redirect_to_download_view = False

    # If this record was just created by the current user, we want to do some special-handling:
    # for instance, show them a message in the template, and give the playback extra time to initialize
    new_record = request.user.is_authenticated and link.created_by_id == request.user.id and not link.user_deleted \
                 and link.creation_timestamp > timezone.now() - timedelta(seconds=300)

    # Provide the max upload size, in case the upload form is used
    max_size = settings.MAX_ARCHIVE_FILE_SIZE / 1024 / 1024

    if not link.submitted_description:
        link.submitted_description = f"This is an archive of {link.submitted_url} from {link.creation_timestamp.strftime('%A %d, %B %Y')}"

    logger.debug(f"Preparing context for {link.guid}")
    context = {
        'link': link,
        'redirect_to_download_view': redirect_to_download_view,
        'mime_type': capture_mime_type,
        'can_view': request.user.can_view(link),
        'can_edit': request.user.can_edit(link),
        'can_delete': request.user.can_delete(link),
        'can_toggle_private': request.user.can_toggle_private(link),
        'capture': capture,
        'serve_type': serve_type,
        'new_record': new_record,
        'this_page': 'single_link',
        'max_size': max_size,
        'link_url': settings.HOST + '/' + link.guid,
        'protocol': protocol(),
    }

    playback_type = request.GET.get('playback')
    if flag_is_active(request, 'wacz-playback') and link.has_wacz_version() and not playback_type == 'warc':
        context["playback_url"] = link.wacz_presigned_url_relative()
    else:
        context["playback_url"] = link.warc_presigned_url_relative()

    if context['can_view'] and link.can_play_back():

        # Prepare a WACZ for the next attempted playback, if appropriate
        if (
            settings.WARC_TO_WACZ_ON_DEMAND and
            link.warc_size and
            link.warc_size < settings.WARC_TO_WACZ_ON_DEMAND_SIZE_LIMIT and
            not link.wacz_size and
            not link.is_user_uploaded
        ):
            convert_warc_to_wacz.delay(link.guid)

        if new_record:
            logger.debug(f"Ensuring warc for {link.guid} has finished uploading.")
            def assert_exists(filename):
                assert storages[settings.WARC_STORAGE].exists(filename)
            try:
                retry_on_exception(assert_exists, args=[link.warc_storage_file()], exception=AssertionError, attempts=settings.WARC_AVAILABLE_RETRIES)
            except AssertionError:
                logger.error(f"Made {settings.WARC_AVAILABLE_RETRIES} attempts to get {link.guid}'s warc; still not available.")
                # Let's consider this a HTTP 200, I think...
                return render(request, 'archive/playback-delayed.html', context,  status=200)

        logger.info(f'Preparing client-side playback for {link.guid}')
        context['client_side_playback_host'] = settings.PLAYBACK_HOST
        context['embed'] = False if request.GET.get('embed') == 'False' else True

    response = render(request, 'archive/single-link.html', context)

    # Adjust status code
    if link.user_deleted:
        response.status_code = 410
    elif not context['can_view'] and link.is_private:
        response.status_code = 403

    # Add memento headers, when appropriate
    logger.debug(f"Deciding whether to include memento headers for {link.guid}")
    if link.is_visible_to_memento():
        logger.debug(f"Including memento headers for {link.guid}")
        response['Memento-Datetime'] = datetime_to_http_date(link.creation_timestamp)
        # impose an arbitrary length-limit on the submitted URL, so that this header doesn't become illegally large
        url = link.submitted_url[:500]
        # strip control characters from url, if somehow they slipped in prior to https://github.com/harvard-lil/perma/commit/272b3a79d94a795142940281c9444b45c24a05db
        url = remove_control_characters(url)
        response['Link'] = str(
            LinkHeader([
                Rel(url, rel='original'),
                Rel(timegate_url(request, url), rel='timegate'),
                Rel(timemap_url(request, url, 'link'), rel='timemap', type='application/link-format'),
                Rel(timemap_url(request, url, 'json'), rel='timemap', type='application/json'),
                Rel(timemap_url(request, url, 'html'), rel='timemap', type='text/html'),
                Rel(memento_url(request, link), rel='memento', datetime=datetime_to_http_date(link.creation_timestamp)),
            ])
        )

    # Prevent browser caching
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"

    logger.debug(f"Returning response for {link.guid}")
    return response
