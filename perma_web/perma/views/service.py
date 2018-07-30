import pytz
from datetime import timedelta, datetime

from django.core import serializers
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils import timezone

from perma.models import WeekStats, MinuteStats
from perma.utils import get_lat_long, user_passes_test_or_403
from django.http import JsonResponse


def stats_sums(request):
    """
    Get all of our weekly stats and serve them up here. The visualizations
    in our stats dashboard consume these.
    """

    raw_data = serializers.serialize('python', WeekStats.objects.all().order_by('start_date'))

    # serializers.serialize wraps our key/value pairs in a 'fields' key. extract.
    extracted_fields = [d['fields'] for d in raw_data]

    return JsonResponse(
        extracted_fields,
        safe=False  # tell Django not to worry about security risk of delivering JSON array -- see https://security.stackexchange.com/a/110552
    )


def stats_now(request):
    """
    Serve up our up-to-the-minute stats.
    """

    # Get all events since minute one of this day

    # if our request comes with a utcoffset, use that
    offset_param = request.GET.get('offset', '')
    offset_value = 0

    if offset_param:
        offset_value = int(offset_param)
        offset_time = datetime.utcnow() + timedelta(minutes=offset_value)
        midnight = offset_time.replace(hour=0, minute=0, second=0)

    else:
        ny = pytz.timezone('America/New_York')
        ny_now = timezone.now().astimezone(ny)
        offset_value = ny_now.utcoffset().seconds // 60
        midnight = ny_now.replace(hour=0, minute=0, second=0)

    todays_events = MinuteStats.objects.filter(creation_timestamp__gte=midnight)

    # Package our data in a way that's easy to parse in our JS visualization
    links = []
    users = []
    organizations = []
    registrars = []

    for event in todays_events:
        tz_adjusted = event.creation_timestamp + timedelta(minutes=offset_value)

        if event.links_sum:
            links.append(tz_adjusted.hour * 60 + tz_adjusted.minute)

        if event.users_sum:
            users.append(tz_adjusted.hour * 60 + tz_adjusted.minute)

        if event.organizations_sum:
            organizations.append(tz_adjusted.hour * 60 + tz_adjusted.minute)

        if event.registrars_sum:
            registrars.append(tz_adjusted.hour * 60 + tz_adjusted.minute)

    return JsonResponse({'links': links, 'users': users, 'organizations': organizations, 'registrars': registrars})


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
    add_url = u"{}?url={}".format(reverse('create_link'), tocapture)
    return redirect(add_url)

@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user())
def coordinates_from_address(request):
    """ Return {lat:#, lng:#, success: True} of any address or {success: False} if lookup fails."""
    address = request.GET.get('address', '')
    if address:
        try:
            (lat, lng) = get_lat_long(address)
            return JsonResponse({'lat': lat, 'lng': lng, 'success': True})
        except TypeError:
            pass
    return JsonResponse({'success': False})
