from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.conf import settings

from ..models import Link, CaptureJob

valid_link_sorts = ['-creation_timestamp', 'creation_timestamp', 'submitted_title', '-submitted_title']


###### LINK CREATION ######

@login_required
def create_link(request):

    deleted = request.GET.get('deleted', '')
    if deleted:
        try:
            link = Link.objects.all_with_deleted().get(guid=deleted)
        except Link.DoesNotExist:
            link = None
        if link:
            messages.add_message(request, messages.INFO, 'Deleted - ' + link.submitted_title)

    # approximate 'average' capture time during last 24 hrs
    # based on manage/stats
    capture_time_fields = CaptureJob.objects.filter(
        link__creation_timestamp__gt=(timezone.now() - timedelta(days=1)), link__creation_timestamp__lt=(timezone.now())
    ).values(
        'capture_start_time', 'link__creation_timestamp', 'capture_end_time'
    ).exclude(capture_start_time=None).exclude(capture_end_time=None)
    if capture_time_fields:
        ctf_len = len(capture_time_fields)
        capture_times = sorted(c['capture_end_time']-c['capture_start_time'] for c in capture_time_fields)
        average = capture_times[int(ctf_len*.5)].total_seconds()
    else:
        average = 1

    links_remaining = request.user.get_links_remaining()
    return render(request, 'user_management/create-link.html', {
        'this_page': 'create_link',
        'links_remaining': 'Infinity' if links_remaining[0] == float('inf') else links_remaining[0] + links_remaining[2],
        'links_remaining_period': links_remaining[1],
        'link_creation_allowed': request.user.link_creation_allowed(),
        'suppress_reminder': 'true' if 'url' in request.GET else request.COOKIES.get('suppress_reminder'),
        'max_size': settings.MAX_ARCHIVE_FILE_SIZE / 1024 / 1024,
        'workers': settings.WORKER_COUNT,
        'average': average
    })


###### LINK BROWSING ######

@login_required
def user_delete_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    if not request.user.can_delete(link):
        raise Http404

    return render(request, 'archive/confirm/link-delete-confirm.html', {
        'link': link,
    })

