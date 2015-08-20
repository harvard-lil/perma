from wsgiref.util import FileWrapper
import logging
from urlparse import urlparse
import requests
from ratelimit.decorators import ratelimit

from django.core.files.storage import default_storage
from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import render_to_response, render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render_to_response, render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect, Http404, HttpResponse, HttpResponseNotFound, HttpResponseServerError, StreamingHttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_control
from django.core.mail import EmailMessage
from django.views.static import serve as media_view

import logging
from urlparse import urlparse
import requests
from ratelimit.decorators import ratelimit

from ..models import Link, Asset
from perma.forms import ContactForm
from perma.middleware import ssl_optional
from perma.utils import if_anonymous, send_contact_email

logger = logging.getLogger(__name__)
valid_serve_types = ['image', 'pdf', 'source', 'warc_download']


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


def landing(request):
    """
    The landing page
    """
    if request.user.is_authenticated() and settings.HOST not in request.META.get('HTTP_REFERER',''):
        return HttpResponseRedirect(reverse('create_link'))
        
    else:
        return render(request, 'landing.html', {'this_page': 'landing'})
    

def stats(request):
    """
    The global stats
    """
    
    # TODO: generate these nightly. we shouldn't be doing this for every request
    top_links_all_time = list(Link.objects.all().order_by('-view_count')[:10])

    context = RequestContext(request, {'top_links_all_time': top_links_all_time})

    return render_to_response('stats.html', context)


@ssl_optional
@if_anonymous(cache_control(max_age=settings.CACHE_MAX_AGES['single_linky']))
@ratelimit(method='GET', rate=settings.MINUTE_LIMIT, block=True, ip=False,
           keys=lambda req: req.META.get('HTTP_X_FORWARDED_FOR', req.META['REMOTE_ADDR']))
@ratelimit(method='GET', rate=settings.HOUR_LIMIT, block=True, ip=False,
           keys=lambda req: req.META.get('HTTP_X_FORWARDED_FOR', req.META['REMOTE_ADDR']))
@ratelimit(method='GET', rate=settings.DAY_LIMIT, block=True, ip=False,
           keys=lambda req: req.META.get('HTTP_X_FORWARDED_FOR', req.META['REMOTE_ADDR']))
def single_linky(request, guid):
    """
    Given a Perma ID, serve it up. Vesting also takes place here.
    """

    # Create a canonical version of guid (non-alphanumerics removed, hyphens every 4 characters, uppercase),
    # and forward to that if it's different from current guid.
    canonical_guid = Link.get_canonical_guid(guid)
    link = get_object_or_404(Link, guid=canonical_guid)

    if canonical_guid != guid:
        return HttpResponsePermanentRedirect(reverse('single_linky', args=[canonical_guid]))

    # User requested archive type
    serve_type = request.GET.get('type', 'live')
    if not serve_type in valid_serve_types:
        serve_type = 'live'

    # SSL check
    # This helper func will return a redirect if we are trying to view a live http link from an https frame
    # (which will fail because of the mixed content policy),
    # or if we are using an http frame and could be using https.
    def ssl_redirect(link):
        if not settings.SECURE_SSL_REDIRECT:
            return
        if serve_type == 'live' and not link.startswith('https'):
            if request.is_secure():
                return HttpResponseRedirect("http://%s%s" % (request.get_host(), request.get_full_path()))
        elif not request.is_secure():
            return HttpResponseRedirect("https://%s%s" % (request.get_host(), request.get_full_path()))

    # make sure frame and content ssl match (see helper func above)
    redirect = ssl_redirect(link.submitted_url)
    if redirect:
        return redirect

    # Increment the view count if we're not the referrer
    parsed_url = urlparse(request.META.get('HTTP_REFERER', ''))

    if not request.get_host() in parsed_url.netloc and not settings.READ_ONLY_MODE:
        link.view_count += 1
        link.save()
    # serve raw WARC
    if serve_type == 'warc_download':
        # TEMP: remove this line after all legacy warcs have been exported
        if not default_storage.exists(link.warc_storage_file()):
            link.export_warc()

        response = StreamingHttpResponse(FileWrapper(default_storage.open(link.warc_storage_file()), 1024 * 8),
                                         content_type="application/gzip")
        response['Content-Disposition'] = "attachment; filename=%s.warc.gz" % link.guid
        return response
        
    capture = None
    if serve_type == 'live':
        # We used to support a live tab. That's depreicated now. Let's
        # serve up somethign as a backup
        capture = link.primary_capture
        
    elif serve_type == 'source' or serve_type == 'pdf':
        capture = link.primary_capture

    elif serve_type == 'image':
        capture = link.screenshot_capture

    context = {
        'link': link,
        'can_view': link.can_view(request.user),
        'capture': capture,
        'next': request.get_full_path(),
        'serve_type': serve_type
    }

    return render(request, 'archive/single-link.html', context)


def rate_limit(request, exception):
    """
    When a user hits a rate limit, send them here.
    """
    
    return render_to_response("rate_limit.html")

## We need custom views for server errors because otherwise Django
## doesn't send a RequestContext (meaning we don't get STATIC_ROOT).
def server_error_404(request):
    return HttpResponseNotFound(render_to_string('404.html', context_instance=RequestContext(request)))

def server_error_500(request):
    return HttpResponseServerError(render_to_string('500.html', context_instance=RequestContext(request)))

@csrf_exempt
@ratelimit(method='GET', rate=settings.MINUTE_LIMIT, block=True, ip=False,
           keys=lambda req: req.META.get('HTTP_X_FORWARDED_FOR', req.META['REMOTE_ADDR']))
def contact(request):
    """
    Our contact form page
    """

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # If our form is valid, let's generate and email to our contact folks

            user_agent = 'Unknown'
            if 'HTTP_USER_AGENT' in request.META:
                user_agent = request.META.get('HTTP_USER_AGENT')

            from_address = form.cleaned_data['email']

            content = '''
            This is a message from the Perma.cc contact form, http://perma.cc/contact



            Message from user
            --------
            %s


            User email: %s
            User agent: %s

            ''' % (form.cleaned_data['message'], from_address, user_agent)

            send_contact_email(
                "New message from Perma contact form",
                content,
                from_address
            )

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('contact_thanks'))
        else:
            context = RequestContext(request, {'form': form})
            return render_to_response('contact.html', context)

    else:

        # Our contact form serves a couple of purposes
        # If we get a message parameter, we're getting a message from the create form
        # about a failed archive
        #
        # If we get a flagged parameter, we're getting the guid of an archive from the
        # Flag as inappropriate button on an archive page
        #
        # We likely want to clean up this contact for logic if we tack much else on
        
        message = request.GET.get('message', '')
        flagged_archive_guid = request.GET.get('flag', '')

        if flagged_archive_guid:
            message = 'http://perma.cc/%s contains material that is inappropriate.' % flagged_archive_guid


        form = ContactForm(initial={'message': message})

        context = RequestContext(request, {'form': form})
        return render_to_response('contact.html', context)


def debug_media_view(request, *args, **kwargs):
    """
        Override Django's built-in dev-server view for serving media files,
        in order to NOT set content-encoding for gzip files.
        This stops the dev server from messing up delivery of archive.warc.gz files.
    """
    response = media_view(request, *args, **kwargs)
    if response.get("Content-Encoding") == "gzip":
        del response["Content-Encoding"]
    return response
