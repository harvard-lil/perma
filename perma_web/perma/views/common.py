from wsgiref.util import FileWrapper
import logging
from urlparse import urlparse
from time import mktime
from ratelimit.decorators import ratelimit
from datetime import timedelta
from wsgiref.handlers import format_date_time

from django.core.files.storage import default_storage
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response, render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponseNotFound, HttpResponseServerError, StreamingHttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_control

from ..models import Link, Registrar, Organization, LinkUser
from ..forms import ContactForm
from ..utils import if_anonymous, send_admin_email, ratelimit_ip_key

logger = logging.getLogger(__name__)
valid_serve_types = ['image', 'warc_download']


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
    if request.user.is_authenticated() and request.get_host() not in request.META.get('HTTP_REFERER',''):
        return HttpResponseRedirect(reverse('create_link'))

    else:
        orgs_count = Organization.objects.count()
        users_count = LinkUser.objects.count()
        links_count = Link.objects.filter(is_private=False).count()

        return render(request, 'landing.html', {
            'this_page': 'landing',
            'orgs_count': orgs_count, 'users_count': users_count, 'links_count': links_count,
        })

def about(request):
    """
    The about page
    """

    partners = sorted(Registrar.objects.filter(show_partner_status=True), key=lambda r: r.partner_display_name or r.name)
    halfway_point = len(partners)/2

    # sending two sets of arrays so that we can separate them
    # into two columns alphabetically, the right way

    partners_first_col = partners[:halfway_point] if len(partners) > 0 else []
    partners_last_col = partners[halfway_point:] if len(partners) > 0 else []

    return render(request, 'about.html', {
        'partners': partners,
        'partners_first_col': partners_first_col,
        'partners_last_col': partners_last_col
    })

def faq(request):
    """
    The faq page
    """
    registrars_count = Registrar.objects.approved().count()
    orgs_count = Organization.objects.all().count()
    users_count = LinkUser.objects.all().count()
    links_count = Link.objects.filter(is_private=False).count()
    return render(request, 'docs/faq.html', {'registrars_count': registrars_count,
        'orgs_count': orgs_count, 'users_count': users_count, 'links_count': links_count,})

def stats(request):
    """
    The global stats
    """

    # TODO: generate these nightly. we shouldn't be doing this for every request
    top_links_all_time = list(Link.objects.all().order_by('-view_count')[:10])

    context = RequestContext(request, {'top_links_all_time': top_links_all_time})

    return render_to_response('stats.html', context)


@if_anonymous(cache_control(max_age=settings.CACHE_MAX_AGES['single_linky']))
@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.HOUR_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.DAY_LIMIT, block=True, key=ratelimit_ip_key)
def single_linky(request, guid):
    """
    Given a Perma ID, serve it up.
    """

    # Create a canonical version of guid (non-alphanumerics removed, hyphens every 4 characters, uppercase),
    # and forward to that if it's different from current guid.
    canonical_guid = Link.get_canonical_guid(guid)

    # We only do the redirect if the correctly-formatted GUID actually exists --
    # this prevents actual 404s from redirecting with weird formatting.
    link = get_object_or_404(Link.objects.all_with_deleted(), guid=canonical_guid)

    if canonical_guid != guid:
        return HttpResponsePermanentRedirect(reverse('single_linky', args=[canonical_guid]))

    # Forward to replacement link if replacement_link is set.
    if link.replacement_link_id:
        return HttpResponseRedirect(reverse('single_linky', args=[link.replacement_link_id]))

    # If we get an unrecognized archive type (which could be an old type like 'live' or 'pdf'), forward to default version
    serve_type = request.GET.get('type')
    if serve_type is None:
        serve_type = 'source'
    elif serve_type not in valid_serve_types:
        return HttpResponsePermanentRedirect(reverse('single_linky', args=[canonical_guid]))

    # Increment the view count if we're not the referrer
    parsed_url = urlparse(request.META.get('HTTP_REFERER', ''))
    if not request.get_host() in parsed_url.netloc and not settings.READ_ONLY_MODE:
        link.view_count += 1
        link.save()

    # serve raw WARC
    if serve_type == 'warc_download':
        if request.user.can_view(link):
            response = StreamingHttpResponse(FileWrapper(default_storage.open(link.warc_storage_file()), 1024 * 8),
                                             content_type="application/gzip")
            response['Content-Disposition'] = "attachment; filename=%s.warc.gz" % link.guid
            return response
        else:
            return HttpResponseForbidden('Private archive.')

    if serve_type == 'image':
        capture = link.screenshot_capture
    else:
        capture = link.primary_capture

        # if primary capture did not work, but screenshot did work, forward to screenshot
        if (not capture or capture.status != 'success') and link.screenshot_capture and link.screenshot_capture.status == 'success':
            return HttpResponseRedirect(reverse('single_linky', args=[guid])+"?type=image")

    new_record = False
    if request.user.is_authenticated() and link.created_by_id == request.user.id and not link.user_deleted:
        # If this record was just created by the current user, show them a new record message
        new_record = link.creation_timestamp > timezone.now() - timedelta(seconds=300)

    context = {
        'link': link,
        'can_view': request.user.can_view(link),
        'can_edit': request.user.can_edit(link),
        'can_delete': request.user.can_delete(link),
        'can_toggle_private': request.user.can_toggle_private(link),
        'capture': capture,
        'next': request.get_full_path(),
        'serve_type': serve_type,
        'new_record': new_record,
        'this_page': 'single_link',
        'WARC_HOST': settings.WARC_HOST,
    }

    response = render(request, 'archive/single-link.html', context)
    date_header = format_date_time(mktime(link.creation_timestamp.timetuple()))
    protocol = "https://" if settings.SECURE_SSL_REDIRECT else "http://"
    link_memento  = protocol + settings.HOST + '/' + link.guid
    link_timegate = protocol + settings.WARC_HOST + settings.TIMEGATE_WARC_ROUTE + '/' + link.safe_url
    link_timemap  = protocol + settings.WARC_HOST + settings.WARC_ROUTE + '/timemap/*/' + link.safe_url
    response['Memento-Datetime'] = date_header

    link_memento_headers = '<{0}>; rel="original"; datetime="{1}",<{2}>; rel="memento"; datetime="{1}",<{3}>; rel="timegate",<{4}>; rel="timemap"; type="application/link-format"'
    response['Link'] = link_memento_headers.format(link.safe_url, date_header, link_memento, link_timegate, link_timemap)

    return response

def rate_limit(request, exception):
    """
    When a user hits a rate limit, send them here.
    """
    return render(request, "rate_limit.html")

## We need custom views for server errors because otherwise Django
## doesn't send a RequestContext (meaning we don't get STATIC_ROOT).
def server_error_404(request):
    return HttpResponseNotFound(render_to_string('404.html', context_instance=RequestContext(request)))

def server_error_500(request):
    return HttpResponseServerError(render_to_string('500.html', context_instance=RequestContext(request)))

@csrf_exempt
@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def contact(request):
    """
    Our contact form page
    """

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # If our form is valid, let's generate and email to our contact folks

            from_address = form.cleaned_data['email']

            content = '''
This is a message from the Perma.cc contact form, http://perma.cc/contact



Message from user
--------
%s
''' % (form.cleaned_data['message'])

            send_admin_email(
                "New message from Perma contact form",
                content,
                from_address,
                request
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
