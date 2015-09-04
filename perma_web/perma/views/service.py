import json, logging, csv

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from perma.models import Link, Stat
from perma.utils import send_contact_email


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


def receive_feedback(request):
    """
    Take feedback data and send it off in an email
    """
    
    user_agent = ''
    if 'HTTP_USER_AGENT' in request.META:
        user_agent = request.META.get('HTTP_USER_AGENT')

    visited_page = request.POST.get('visited_page')
    feedback_text = request.POST.get('feedback_text')
    broken_link = request.POST.get('broken_link')
    broken_text = ""
    if(broken_link):
        broken_text = '''There was a problem creating the following Perma
    %s
        
    ''' %(broken_link)
    
    from_address = request.POST.get('user_email')
    content = '''
    Visited page: %s
    
    COMMENTS
    --------
    %s
    
    
    %s
    
    USER INFO
    ---------
    %s

''' % (visited_page, feedback_text, broken_text, user_agent)
    logger.debug(content)
    
    send_contact_email(
        "New Perma feedback",
        content,
        from_address
    )
        
    response_object = {'submitted': 'true', 'content': content}

    return HttpResponse(json.dumps(response_object), content_type="application/json", status=201)

def stats_users(request):
    """
    Retrieve nightly stats for users in the DB, dump them out here so that our D3 vis can render them, real-purty-like
    
    #TODO: rework this and its partnering D3 code. Writing CSV is gross. Serialize to JSON and update our D3 method in stats.html
    """
    
    # Get the 1000 most recent.
    # TODO: if we make it more than a 1000 days, implement some better interface.
    stats = Stat.objects.only(
        'creation_timestamp',
        'regular_user_count',
        'org_member_count',
        'registrar_member_count',
        'registry_member_count')[:1000]
    
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename="data.tsv"'
    
    headers = ['key', 'value', 'date']

    writer = csv.writer(response, delimiter='\t')
    writer.writerow(headers)
    
    for stat in stats:
        writer.writerow(['Regular user', stat.regular_user_count, stat.creation_timestamp.strftime('%d-%b-%y')])
        writer.writerow(['Organization member', stat.org_member_count, stat.creation_timestamp.strftime('%d-%b-%y')])
        writer.writerow(['Registrar member', stat.registrar_member_count, stat.creation_timestamp.strftime('%d-%b-%y')])
        writer.writerow(['Registry member', stat.registry_member_count, stat.creation_timestamp.strftime('%d-%b-%y')])
    
    return response
    
def stats_links(request):
    """
    Retrieve nightly stats for links in the DB, dump them out here so that our D3 vis can render them, real-purty-like

    #TODO: rework this and its partnering D3 code. Writing CSV is gross. Serialize to JSON and update our D3 method in stats.html
    """
    
    # Get the 1000 most recent.
    # TODO: if we make it more than a 1000 days, implement some better interface.
    stats = Stat.objects.only('creation_timestamp', 'vested_count', 'unvested_count')[:1000]

    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename="data.tsv"'

    headers = ['key', 'value', 'date']

    writer = csv.writer(response, delimiter='\t')
    writer.writerow(headers)

    for stat in stats:
        writer.writerow(['Vested', stat.vested_count, stat.creation_timestamp.strftime('%d-%b-%y')])
        writer.writerow(['Unvested', stat.unvested_count, stat.creation_timestamp.strftime('%d-%b-%y')])


    return response
    
def stats_darchive_links(request):
    """
    Retrieve nightly stats for darchived links, dump them out here so that our D3 vis can render them, real-purty-like

    #TODO: rework this and its partnering D3 code. Writing CSV is gross. Serialize to JSON and update our D3 method in stats.html
    """

    # Get the 1000 most recent.
    # TODO: if we make it more than a 1000 days, implement some better interface.
    stats = Stat.objects.only('creation_timestamp', 'darchive_takedown_count', 'darchive_robots_count')[:1000]

    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename="data.tsv"'

    headers = ['key', 'value', 'date']

    writer = csv.writer(response, delimiter='\t')
    writer.writerow(headers)

    for stat in stats:
        writer.writerow(['Darchive due to takedown', stat.darchive_takedown_count, stat.creation_timestamp.strftime('%d-%b-%y')])
        writer.writerow(['Darchive due to robots.txt', stat.darchive_robots_count, stat.creation_timestamp.strftime('%d-%b-%y')])


    return response
    
    
def stats_storage(request):
    """
    Retrieve nightly stats for storage totals in the DB, dump them out here so that our D3 vis can render them, real-purty-like

    #TODO: rework this and its partnering D3 code. Writing CSV is gross. Serialize to JSON and update our D3 method in stats.html
    """

    # Get the 1000 most recent.
    # TODO: if we make it more than a 1000 days, implement some better interface.
    stats = Stat.objects.only('disk_usage')[:1000]

    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename="data.tsv"'

    headers = ['date', 'close']

    writer = csv.writer(response, delimiter='\t')
    writer.writerow(headers)

    for stat in stats:
        in_gb = stat.disk_usage / 1024 / 1024 / 1024
        writer.writerow([stat.creation_timestamp.strftime('%d-%b-%y'), in_gb])


    return response
    
def stats_org(request):
    """
    Retrieve nightly stats for total number of orgs, dump them out here so that our D3 vis can render them, real-purty-like

    #TODO: rework this and its partnering D3 code. Writing CSV is gross. Serialize to JSON and update our D3 method in stats.html
    """

    # Get the 1000 most recent.
    # TODO: if we make it more than a 1000 days, implement some better interface.
    stats = Stat.objects.only('org_count')[:1000]

    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename="data.tsv"'

    headers = ['date', 'close']

    writer = csv.writer(response, delimiter='\t')
    writer.writerow(headers)

    for stat in stats:
        writer.writerow([stat.creation_timestamp.strftime('%d-%b-%y'), stat.org_count])

    return response
    
def stats_registrar(request):
    """
    Retrieve nightly stats for total number of registrars (libraries), dump them out here so that our D3 vis can render them, real-purty-like

    #TODO: rework this and its partnering D3 code. Writing CSV is gross. Serialize to JSON and update our D3 method in stats.html
    """

    # Get the 1000 most recent.
    # TODO: if we make it more than a 1000 days, implement some better interface.
    stats = Stat.objects.only('registrar_count')[:1000]

    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename="data.tsv"'

    headers = ['date', 'close']

    writer = csv.writer(response, delimiter='\t')
    writer.writerow(headers)

    for stat in stats:
        writer.writerow([stat.creation_timestamp.strftime('%d-%b-%y'), stat.registrar_count])


    return response

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