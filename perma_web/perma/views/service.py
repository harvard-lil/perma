import json, logging, csv, pytz
from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core import serializers
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from perma.models import Link, WeekStats, MinuteStats
from perma.utils import send_contact_email, json_serial


logger = logging.getLogger(__name__)


def email_confirm(request):
    """
    A service that sends a message to a user about a perma link.
    """
    
    email_address = request.POST.get('email_address')
    link_url = request.POST.get('link_url')

    if not email_address or not link_url:
        return HttpResponse(status=400)

    send_mail(
        "The Perma link you requested",
        "%s \n\n(This link is the Perma link)" % link_url,
        settings.DEFAULT_FROM_EMAIL,
        [email_address]
    )

    response_object = {"sent": True}

    return HttpResponse(json.dumps(response_object), content_type="application/json", status=200)

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
    path = request.get_full_path()
    # Strip '/service/bookmarklet-create/
    querystring = path[28:]
    add_url = reverse('create_link')
    add_url = add_url + querystring
    return redirect(add_url)

def image_wrapper(request, guid):
    """
    When we display an image, our display logic is greatly simplified if we
    display our archived image in an iframe. That's all we do here, take
    an archived image and wrap it in a page that we server through an iframe
    """

    asset = Asset.objects.get(link__guid=guid)

    # find requested link and url
    try:
        asset = Asset.objects.get(link__guid=guid)
    except Link.DoesNotExist:
        print "COULDN'T FIND LINK"
        raise Http404

    return render_to_response('archive/image_wrapper.html', {'asset': asset}, RequestContext(request))

@login_required
def get_thumbnail(request, guid):
    """
        This is our thumbnailing service. Pass it the guid of an archive and get back the thumbnail.
    """

    link = get_object_or_404(Link, guid=guid)

    if link.thumbnail_status == 'generating':
        return HttpResponse(status=202)

    thumbnail_contents = link.get_thumbnail()
    if not thumbnail_contents:
        raise Http404

    return HttpResponse(thumbnail_contents.read(), content_type='image/png')