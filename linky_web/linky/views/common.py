from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse

from datetime import datetime
from urlparse import urlparse
import urllib2
import logging

from linky.models import Link, Asset
from linky.utils import base
from ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)

try:
    from linky.local_settings import *
except ImportError, e:
    logger.error('Unable to load local_settings.py: %s', e)

@ratelimit(method='GET', rate=INTERNAL['MINUTE_LIMIT'], block='True')
@ratelimit(method='GET', rate=INTERNAL['HOUR_LIMIT'], block='True')
@ratelimit(method='GET', rate=INTERNAL['DAY_LIMIT'], block='True')
def landing(request):
    """
    The landing page
    """

    if request.user.id >= 0:
      linky_links = list(Link.objects.filter(created_by=request.user).order_by('-creation_timestamp'))


      # TODO: we should always store the protocol with the link, https://github.com/harvard-lil/linky/issues/105
      # this'll save us from having to do this protocol sniffing
      # TODO: Move the ... management to the view
      for linky_link in linky_links:
        if linky_link.submitted_url.startswith('http://'):
          linky_link.submitted_url = linky_link.submitted_url[7:]
        elif linky_link.submitted_url.startswith('https://'):
          linky_link.submitted_url = linky_link.submitted_url[8:]
        if len(linky_link.submitted_title) > 50:
          linky_link.submitted_title = linky_link.submitted_title[:50] + '...'
        if len(linky_link.submitted_url) > 79:
          linky_link.submitted_url = linky_link.submitted_url[:70] + '...'
    else:
      linky_links = None;

    context = {'this_page': 'landing', 'host': request.get_host(), 'user': request.user, 'linky_links': linky_links, 'next': request.get_full_path()}
    context.update(csrf(request))

    return render_to_response('landing.html', context)


def about(request):
    """
    The about page
    """

    context = {'host': request.get_host()}

    return render_to_response('about.html', context)


def faq(request):
    """
    The FAQ page
    """
    
    return render_to_response('faq.html', {})


def contact(request):
    """
    The contact page
    """
    
    return render_to_response('contact.html', {})


def terms_of_service(request):
    """
    The terms of service page
    """
    
    return render_to_response('terms_of_service.html', {})


def privacy_policy(request):
    """
    The privacy policy page
    """
    
    return render_to_response('privacy_policy.html', {})


def tools(request):
    """
    The tools page
    """
    
    return render_to_response('tools.html', {})


@ratelimit(method='GET', rate=INTERNAL['MINUTE_LIMIT'], block='True')
@ratelimit(method='GET', rate=INTERNAL['HOUR_LIMIT'], block='True')
@ratelimit(method='GET', rate=INTERNAL['DAY_LIMIT'], block='True')
def single_linky(request, linky_guid):
    """
    Given a Linky ID, serve it up. Vetting also takes place here.
    """

    if request.method == 'POST':
        Link.objects.filter(guid=linky_guid).update(vested = True, vested_by_editor = request.user, vested_timestamp = datetime.now())

        return HttpResponseRedirect('/%s/' % linky_guid)
    else:

        link = get_object_or_404(Link, guid=linky_guid)

        link.view_count += 1
        link.save()

        try:
            response = urllib2.urlopen(link.submitted_url)
            if 'X-Frame-Options' in response.headers:
                # TODO actually check if X-Frame-Options specifically allows requests from us
                display_iframe = False
            else:
                display_iframe = True
        except urllib2.URLError:
            # Something is broken with the site, so we might as well display it in an iFrame so the user knows
            display_iframe = True

        asset= Asset.objects.get(link__guid=link.guid)

        created_datestamp = link.creation_timestamp
        pretty_date = created_datestamp.strftime("%B %d, %Y %I:%M GMT")

        context = {'linky': link, 'asset': asset, 'pretty_date': pretty_date, 'user': request.user, 'next': request.get_full_path(), 'display_iframe': display_iframe}

        context.update(csrf(request))

    return render_to_response('single-linky.html', context)


def rate_limit(request, exception):
    """
    When a user hits a rate limit, send them here.
    """
    
    return render_to_response("rate_limit.html")
