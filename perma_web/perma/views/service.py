from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse

import smtplib, json, logging, csv
from perma.models import Link, Asset, Stat
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def email_confirm(request):
    """
    A service that sends a linky message.
    """
    
    email_address = request.POST.get('email_address')
    linky_link = request.POST.get('linky_link')
    
    if not email_address and not linky_link:
        return HttpResponse(status=400)
    
    from_address = "info@perma.cc"
    to_address = email_address
    content = "%s \n\n(This link is the Perma link)" % linky_link

    msg = MIMEText(content)
    msg['Subject'] = "The Perma link you requested"
    msg['From'] = from_address
    msg['To'] = to_address

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()

    response_object = {"sent": True}

    return HttpResponse(json.dumps(response_object), content_type="application/json", status=200)


def receive_feedback(request):
    """
    Take feedback data and send it off in an email
    """
    
    submitted_url = request.POST.get('submitted_url')
    visited_page = request.POST.get('visited_page')
    feedback_text = request.POST.get('feedback_text')
    
    from_address = "lil@law.harvard.edu"
    to_address = request.POST.get('user_email')
    content = '''Visited page: %s
    Feedback text
    _______________________________________
    %s
    _______________________________________

''' % (visited_page, feedback_text)
    logger.debug(content)

    msg = MIMEText(content)
    msg['Subject'] = "New Perma feedback"
    msg['From'] = from_address
    msg['To'] = to_address
        
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    #s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()
        
    response_object = {'submitted': 'true', 'content': content}

    return HttpResponse(json.dumps(response_object), content_type="application/json", status=201)


def link_status(request, guid):
    """
    A service that provides the state of a perma.
    TODO: this should obviously become part of an API, we probably also want to evaluate some long polling
    apporach?
    """

    target_link = get_object_or_404(Link, guid=guid)
    target_asset = get_object_or_404(Asset, link__guid=guid)
    
    response_object = {"text_capture": target_asset.text_capture, "source_capture": target_asset.warc_capture,
        "image_capture": target_asset.image_capture, "pdf_capture": target_asset.pdf_capture}

    return HttpResponse(json.dumps(response_object), content_type="application/json", status=200)



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
        'vesting_member_count',
        'vesting_manager_count',
        'registrar_member_count',
        'registry_member_count')[:1000]
    
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename="data.csv"'
    
    headers = ['key', 'value', 'date']

    writer = csv.writer(response)
    writer.writerow(headers)
    
    for stat in stats:
        writer.writerow(['Regular user', stat.regular_user_count, stat.creation_timestamp])
        writer.writerow(['Vesting member', stat.vesting_member_count, stat.creation_timestamp])
        writer.writerow(['Vesting manager', stat.vesting_manager_count, stat.creation_timestamp])
        writer.writerow(['Registrar member', stat.registrar_member_count, stat.creation_timestamp])
        writer.writerow(['Registry member', stat.registry_member_count, stat.creation_timestamp])
    
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
    response['Content-Disposition'] = 'attachment; filename="data.csv"'

    headers = ['key', 'value', 'date']

    writer = csv.writer(response)
    writer.writerow(headers)

    for stat in stats:
        writer.writerow(['Vested', stat.vested_count, stat.creation_timestamp])
        writer.writerow(['Unvested', stat.unvested_count, stat.creation_timestamp])


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
    response['Content-Disposition'] = 'attachment; filename="data.csv"'

    headers = ['key', 'value', 'date']

    writer = csv.writer(response)
    writer.writerow(headers)

    for stat in stats:
        writer.writerow(['Darchive due to takedown', stat.darchive_takedown_count, stat.creation_timestamp])
        writer.writerow(['Darchive due to robots.txt', stat.darchive_robots_count, stat.creation_timestamp])


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
    response['Content-Disposition'] = 'attachment; filename="data.csv"'

    headers = ['date', 'close']

    writer = csv.writer(response)
    writer.writerow(headers)

    for stat in stats:
        in_gb = stat.disk_usage / 1024 / 1024 / 1024
        writer.writerow([stat.creation_timestamp, in_gb])


    return response
    
def stats_vesting_org(request):
    """
    Retrieve nightly stats for total number of vesting orgs, dump them out here so that our D3 vis can render them, real-purty-like

    #TODO: rework this and its partnering D3 code. Writing CSV is gross. Serialize to JSON and update our D3 method in stats.html
    """

    # Get the 1000 most recent.
    # TODO: if we make it more than a 1000 days, implement some better interface.
    stats = Stat.objects.only('vesting_org_count')[:1000]

    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename="data.csv"'

    headers = ['date', 'close']

    writer = csv.writer(response)
    writer.writerow(headers)

    for stat in stats:
        writer.writerow([stat.creation_timestamp, stat.vesting_org_count])


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
    #response['Content-Disposition'] = 'attachment; filename="data.csv"'

    headers = ['date', 'close']

    writer = csv.writer(response)
    writer.writerow(headers)

    for stat in stats:
        writer.writerow([stat.creation_timestamp, stat.registrar_count])


    return response