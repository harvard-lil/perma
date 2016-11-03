import json, logging, pytz
from werkzeug.security import safe_str_cmp

from django.core import serializers
from django.http import HttpResponse, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from perma.models import WeekStats, MinuteStats
from perma.utils import json_serial
from perma.email import sync_cm_list, send_admin_email, registrar_users_plus_stats


logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def cm_sync(request):
    '''
       Sync our current list of registrar users plus some associated metadata
       to Campaign Monitor.
    '''

    # Use something like this:
    # curl -i -X POST --data "key=<INTERNAL_SERVICES_KEY>" http://perma.dev:8000/service/cm-sync/
    if safe_str_cmp(request.POST.get('key',""), settings.INTERNAL_SERVICES_KEY):
        reports = sync_cm_list(settings.CAMPAIGN_MONITOR_REGISTRAR_LIST,
                               registrar_users_plus_stats(destination='cm'))
        if reports["import"]["duplicates_in_import_list"]:
            logger.error("Duplicate reigstrar users sent to Campaign Monitor. Check sync logic.")
        send_admin_email("Registrar Users Synced to Campaign Monitor",
                          settings.DEFAULT_FROM_EMAIL,
                          request,
                          'email/admin/sync_to_cm.txt',
                          {"reports": reports})
        return HttpResponse(json.dumps(reports), content_type="application/json", status=200)
    else:
        return HttpResponseForbidden("<h1>Forbidden</h1>")


def stats_sums(request):
    """
    Get all of our weekly stats and serve them up here. The visualizations
    in our stats dashboard consume these.
    """

    raw_data = serializers.serialize('python', WeekStats.objects.all().order_by('start_date'))

    # serializers.serialize wraps our key/value pairs in a 'fields' key. extract.
    extracted_fields = [d['fields'] for d in raw_data]

    return HttpResponse(json.dumps(extracted_fields, default=json_serial), content_type="application/json", status=200)


def stats_now(request):
    """
    Serve up our up-to-the-minute stats.
    Todo: make this time-zone friendly.
    """

    # Get all events since minute one of this day in NY
    # this is where we should get the timezone from the client's browser (JS post on stats page load)
    ny = pytz.timezone('America/New_York')
    ny_now = timezone.now().astimezone(ny)
    midnight_ny = ny_now.replace(hour=0, minute=0, second=0)

    todays_events = MinuteStats.objects.filter(creation_timestamp__gte=midnight_ny)

    # Package our data in a way that's easy to parse in our JS visualization
    links = []
    users = []
    organizations = []
    registrars = []

    for event in todays_events:
        tz_adjusted = event.creation_timestamp.astimezone(ny)
        if event.links_sum:
            links.append(tz_adjusted.hour * 60 + tz_adjusted.minute)

        if event.users_sum:
            users.append(tz_adjusted.hour * 60 + tz_adjusted.minute)

        if event.organizations_sum:
            organizations.append(tz_adjusted.hour * 60 + tz_adjusted.minute)

        if event.registrars_sum:
            registrars.append(tz_adjusted.hour * 60 + tz_adjusted.minute)

    return HttpResponse(json.dumps({'links': links, 'users': users, 'organizations': organizations,
        'registrars': registrars}), content_type="application/json", status=200)


def bookmarklet_create(request):
    '''Handle incoming requests from the bookmarklet.

    Currently, the bookmarklet takes two parameters:
    - v (version)
    - url

    This function accepts URLs like this:

    /service/bookmarklet-create/?v=[...]&url=[...]

    ...and passes the query string values to /manage/create/
    '''
    tocapture = request.GET.get('url', '')
    add_url = "{}?url={}".format(reverse('create_link'), tocapture)
    return redirect(add_url)

# @login_required
# def get_thumbnail(request, guid):
#     """
#         This is our thumbnailing service. Pass it the guid of an archive and get back the thumbnail.
#     """
#
#     link = get_object_or_404(Link, guid=guid)
#
#     if link.thumbnail_status == 'generating':
#         return HttpResponse(status=202)
#
#     thumbnail_contents = link.get_thumbnail()
#     if not thumbnail_contents:
#         raise Http404
#
#     return HttpResponse(thumbnail_contents.read(), content_type='image/png')
