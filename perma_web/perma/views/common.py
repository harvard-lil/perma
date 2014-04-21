from django.core import serializers
from django.core.files.storage import default_storage
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect, Http404, HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from datetime import datetime
import urllib2, os, logging
from urlparse import urlparse
from django.views.decorators.csrf import csrf_exempt
from pywb.warc.archiveindexer import ArchiveIndexer
import surt
import json
from ratelimit.decorators import ratelimit

from perma.middleware import get_url_for_host
from perma.models import Link, Asset
from perma.utils import can_be_mirrored


logger = logging.getLogger(__name__)
valid_serve_types = ['live', 'image','pdf','source','text','warc','warc_download']


class DirectTemplateView(TemplateView):
    extra_context = None

    def get_context_data(self, **kwargs):
        """ Override Django's TemplateView to allow passing in extra_context. """
        context = super(self.__class__, self).get_context_data(**kwargs)
        if self.extra_context is not None:
            for key, value in self.extra_context.items():
                if callable(value):
                    context[key] = value()
                else:
                    context[key] = value
        return context

    @method_decorator(can_be_mirrored)
    def dispatch(self, request, *args, **kwargs):
        """ Add can_be_mirrored decorator. """
        return super(DirectTemplateView, self).dispatch(request, *args, **kwargs)

def stats(request):
    """
    The global stats
    """
    
    # TODO: generate these nightly. we shouldn't be doing this for every request
    top_links_all_time = list(Link.objects.all().order_by('-view_count')[:10])

    context = RequestContext(request, {'top_links_all_time': top_links_all_time})

    return render_to_response('stats.html', context)

@csrf_exempt
def cdx(request):
    """
        This function handles WARC lookups by our warc server (running in warc_server).
        It accepts a standard CDX request, except with a GUID instead of date, and returns a standard CDX 11 response.
        If there's no warc for the requested GUID, or the requested URL isn't stored in that WARC, it returns a 404.
    """
    # find requested link and url
    try:
        link = Link.objects.select_related().get(pk=request.GET.get('guid'))
    except Link.DoesNotExist:
        print "COULDN'T FIND LINK"
        raise Http404
    url = request.GET.get('url', link.submitted_url)

    # get warc file
    for asset in link.assets.all():
        if '.warc' in asset.warc_capture:
            warc_path = os.path.join(asset.base_storage_path, asset.warc_capture)
            break
    else:
        if settings.USE_WARC_ARCHIVE:
            print "COULDN'T FIND WARC"
            raise Http404 # no .warc file -- do something to handle this
        else:
            warc_path = os.path.join(asset.base_storage_path, "archive.warc.gz")

    # get cdx file
    cdx_path = warc_path.replace('.gz', '').replace('.warc', '.cdx')
    if not default_storage.exists(cdx_path):
        # if we can't find the CDX file associated with this WARC, create it
        with default_storage.open(warc_path, 'rb') as warc_file, default_storage.open(cdx_path, 'wb') as cdx_file:
            ArchiveIndexer(warc_file, warc_path, cdx_file, sort=True).make_index()
    cdx_lines = default_storage.open(cdx_path, 'rb')

    # find cdx lines for url
    sorted_url = surt.surt(url)
    out = ""
    for line in cdx_lines:
        if line.startswith(sorted_url+" "):
            out += line
        elif out:
            # file may contain multiple matching lines in a row; we want to return all of them
            # if we've already found one or more matching lines, and now they're no longer matching, we're done
            break

    if out:
        return HttpResponse(out, content_type="text/plain")

    print "COULDN'T FIND URL"
    raise Http404 # didn't find requested url in .cdx file

def single_link_main_server(request, guid):
    return single_linky(request, guid)

@can_be_mirrored
@ratelimit(method='GET', rate=settings.MINUTE_LIMIT, block='True')
@ratelimit(method='GET', rate=settings.HOUR_LIMIT, block='True')
@ratelimit(method='GET', rate=settings.DAY_LIMIT, block='True')
def single_linky(request, guid):
    """
    Given a Perma ID, serve it up. Vesting also takes place here.
    """

    if request.method == 'POST' and request.user.is_authenticated():
        Link.objects.filter(guid=guid).update(vested = True, vested_by_editor = request.user, vested_timestamp = datetime.now())

        return HttpResponseRedirect(reverse('single_linky', args=[guid]))

    canonical_guid = Link.get_canonical_guid(guid)
    if canonical_guid != guid:
        return HttpResponsePermanentRedirect(reverse('single_linky', args=[canonical_guid]))

    context = None

    # User requested archive type
    serve_type = request.GET.get('type','live')
    if not serve_type in valid_serve_types:
        serve_type = 'live'

    try:
        link = Link.objects.get(guid=guid)
    except Link.DoesNotExist:
        if settings.MIRROR_SERVER:
            # if we can't find the Link, and we're a mirror server, try fetching it from main server
            try:
                req = urllib2.Request(get_url_for_host(request,
                                                       request.main_server_host,
                                                       reverse('single_link_main_server', args=[guid])+"?type="+serve_type),
                                      headers={'Content-Type': 'application/json'})
                link_json = urllib2.urlopen(req)
            except urllib2.HTTPError:
                raise Http404
            context = json.loads(link_json.read())
            context['linky'] = serializers.deserialize("json", context['linky']).next().object
            context['asset'] = serializers.deserialize("json", context['asset']).next().object
            context['asset'].link = context['linky']
        else:
            raise Http404

    if not context:
        # Increment the view count if we're not the referrer
        parsed_url = urlparse(request.META.get('HTTP_REFERER', ''))
        current_site = Site.objects.get_current()
        
        if not current_site.domain in parsed_url.netloc:
            link.view_count += 1
            link.save()

        asset = Asset.objects.get(link=link)

        text_capture = None
        if serve_type == 'text':
            if asset.text_capture and asset.text_capture != 'pending':
                with default_storage.open(os.path.join(asset.base_storage_path, asset.text_capture), 'r') as f:
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

        asset = Asset.objects.get(link__guid=link.guid)

        created_datestamp = link.creation_timestamp
        pretty_date = created_datestamp.strftime("%B %d, %Y %I:%M GMT")

        context = {'linky': link, 'asset': asset, 'pretty_date': pretty_date, 'next': request.get_full_path(),
                   'display_iframe': display_iframe, 'serve_type': serve_type, 'text_capture': text_capture,
                   'warc_url':'/warc/'}

    if request.META.get('CONTENT_TYPE') == 'application/json':
        # if we were called as JSON (by a mirror), serialize and send back as JSON
        context['MEDIA_URL'] = request.build_absolute_uri(settings.MEDIA_URL)
        context['warc_url'] = request.build_absolute_uri(context['warc_url'])
        context['asset'] = serializers.serialize("json", [context['asset']], fields=['text_capture','image_capture','pdf_capture','warc_capture','base_storage_path'])
        context['linky'] = serializers.serialize("json", [context['linky']], fields=['dark_archived','guid','vested','view_count','creation_timestamp','submitted_url','submitted_title'])
        return HttpResponse(json.dumps(context), content_type="application/json")

    if serve_type == 'warc_download':
        if context['asset'].warc_download_url():
            return HttpResponseRedirect(context.get('MEDIA_URL', settings.MEDIA_URL)+context['asset'].warc_download_url())

    context['USE_WARC_ARCHIVE'] = settings.USE_WARC_ARCHIVE
    return render_to_response('single-link.html', context, RequestContext(request))


def rate_limit(request, exception):
    """
    When a user hits a rate limit, send them here.
    """
    
    return render_to_response("rate_limit.html")
