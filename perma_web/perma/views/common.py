from django.template import Template, context, RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect, Http404, HttpResponse
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.sites.models import Site
from django.views.generic import TemplateView

from datetime import datetime, date, timedelta
from urlparse import urlparse
import urllib2, os, logging
from urlparse import urlparse
from django.views.decorators.csrf import csrf_exempt
import surt, cdx_writer

from perma.models import Link, Asset
from perma.utils import base, require_group
from ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)


class DirectTemplateView(TemplateView):
    extra_context = None
    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        if self.extra_context is not None:
            for key, value in self.extra_context.items():
                if callable(value):
                    context[key] = value()
                else:
                    context[key] = value
        return context


def stats(request):
    """
    The global stats
    """
    
    # TODO: generate these nightly. we shouldn't be doing this for every request
    top_links_all_time = list(Link.objects.all().order_by('-view_count')[:10])

    context = RequestContext(request, {'top_links_all_time': top_links_all_time})

    return render_to_response('stats.html', context)


def tools(request):
    """
    The tools page
    """
    
    return render_to_response('tools.html', {})


@ratelimit(method='GET', rate=settings.MINUTE_LIMIT, block='True')
@ratelimit(method='GET', rate=settings.HOUR_LIMIT, block='True')
@ratelimit(method='GET', rate=settings.DAY_LIMIT, block='True')
def single_linky(request, linky_guid):
    """
    Given a Perma ID, serve it up. Vesting also takes place here.
    """

    if request.method == 'POST' and request.user.is_authenticated():
        Link.objects.filter(guid=linky_guid).update(vested = True, vested_by_editor = request.user, vested_timestamp = datetime.now())

        return HttpResponseRedirect(reverse('single_linky', args=[linky_guid]))
    else:
        canonical_guid = Link.get_canonical_guid(linky_guid)

        if canonical_guid != linky_guid:
            return HttpResponsePermanentRedirect(reverse('single_linky', args=[canonical_guid]))

        link = get_object_or_404(Link, guid=linky_guid)

        # Increment the view count if we're not the referrer
        parsed_url = urlparse(request.META.get('HTTP_REFERER', ''))
        current_site = Site.objects.get_current()
        
        if not current_site.domain in parsed_url.netloc:
            link.view_count += 1
            link.save()

        asset = Asset.objects.get(link=link)


        text_capture = None

        # User requested archive type
        serve_type = 'live'

        if 'type' in request.REQUEST:
            requested_type = request.REQUEST['type']
        
            if requested_type == 'image':
                serve_type = 'image'
            elif requested_type == 'pdf':
                serve_type = 'pdf'
            elif requested_type == 'source':
                serve_type = 'source'
            elif requested_type == 'text':
                serve_type = 'text'
                            
                if asset.text_capture and asset.text_capture != 'pending':
                    path_elements = [settings.GENERATED_ASSETS_STORAGE, asset.base_storage_path, asset.text_capture]
                    file_path = os.path.sep.join(path_elements)
                
                    with open(file_path, 'r') as f:
                        text_capture = f.read()
            
        # If we are going to serve up the live version of the site, let's make sure it's iframe-able
        display_iframe = False
        if serve_type == 'live':
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

        context = RequestContext(request, {'linky': link, 'asset': asset, 'pretty_date': pretty_date, 'next': request.get_full_path(),
                   'display_iframe': display_iframe, 'serve_type': serve_type, 'text_capture': text_capture})

        #context.update(csrf(request))

    return render_to_response('single-link.html', context)
    

@require_group('registry_member')
def dark_archive_link(request, linky_guid):
    """
    Given a Perma ID, serve it up. Vesting also takes place here.
    """

    if request.method == 'POST':
        Link.objects.filter(guid=linky_guid).update(dark_archived = True)

        return HttpResponseRedirect('/%s/' % linky_guid)
    else:

        link = get_object_or_404(Link, guid=linky_guid)

        asset= Asset.objects.get(link__guid=link.guid)

        created_datestamp = link.creation_timestamp
        pretty_date = created_datestamp.strftime("%B %d, %Y %I:%M GMT")

        context = RequestContext(request, {'linky': link, 'asset': asset, 'pretty_date': pretty_date, 'next': request.get_full_path()})

    return render_to_response('dark-archive-link.html', context)


def rate_limit(request, exception):
    """
    When a user hits a rate limit, send them here.
    """
    
    return render_to_response("rate_limit.html")
