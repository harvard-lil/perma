from wsgiref.util import FileWrapper
import logging
from time import mktime

from django.contrib.auth.views import redirect_to_login
from ratelimit.decorators import ratelimit
from datetime import timedelta
from wsgiref.handlers import format_date_time
from ua_parser import user_agent_parser
from urllib import urlencode

from django.core.files.storage import default_storage
from django.forms import widgets
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect, StreamingHttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_control

from ..models import Link, Registrar, Organization, LinkUser
from ..forms import ContactForm
from ..utils import if_anonymous, ratelimit_ip_key
from ..email import send_admin_email, send_user_email_copy_admins

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
    return render(request, 'stats.html')

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

    # serve raw WARC
    if serve_type == 'warc_download':
        if request.user.can_view(link):
            response = StreamingHttpResponse(FileWrapper(default_storage.open(link.warc_storage_file()), 1024 * 8),
                                             content_type="application/gzip")
            response['Content-Disposition'] = "attachment; filename=%s.warc.gz" % link.guid
            return response
        else:
            return HttpResponseForbidden('Private archive.')

    # Special handling for private links on Safari:
    # Safari won't let us set the auth cookie for the WARC_HOST domain inside the iframe, unless we've already set a
    # cookie on that domain outside the iframe. So do a redirect to WARC_HOST to set a cookie and then come back.
    # safari=1 in the query string indicates that the redirect has already happened.
    # See http://labs.fundbox.com/third-party-cookies-with-ie-at-2am/
    if link.is_private and not request.GET.get('safari'):
        user_agent = user_agent_parser.ParseUserAgent(request.META.get('HTTP_USER_AGENT', ''))
        if user_agent.get('family') == 'Safari':
            return redirect_to_login(request.build_absolute_uri(),
                                     "//%s%s" % (settings.WARC_HOST, reverse('user_management_set_safari_cookie')))

    # handle requested capture type
    if serve_type == 'image':
        capture = link.screenshot_capture
    else:
        capture = link.primary_capture

        # if primary capture did not work, but screenshot did work, forward to screenshot
        if (not capture or capture.status != 'success') and link.screenshot_capture and link.screenshot_capture.status == 'success':
            return HttpResponseRedirect(reverse('single_linky', args=[guid])+"?type=image")

    # If this record was just created by the current user, show them a new record message
    new_record = request.user.is_authenticated() and link.created_by_id == request.user.id and not link.user_deleted \
                 and link.creation_timestamp > timezone.now() - timedelta(seconds=300)

    # Provide the max upload size, in case the upload form is used
    max_size = settings.MAX_ARCHIVE_FILE_SIZE / 1024 / 1024

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
        'max_size': max_size
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


@csrf_exempt
@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def contact(request):
    """
    Our contact form page
    """
    def affiliation_string():
        affiliation_string = ''
        if request.user.is_authenticated():
            if request.user.registrar:
                affiliation_string = "{} (Registrar)".format(request.user.registrar.name)
            else:
                affiliations = ["{} ({})".format(org.name, org.registrar.name) for org in request.user.organizations.all().order_by('registrar')]
                if affiliations:
                    affiliation_string = ', '.join(affiliations)
        return affiliation_string

    def formatted_organization_list(registrar):
        organization_string = ''
        if request.user.is_organization_user:
            orgs = [org.name for org in request.user.organizations.filter(registrar=registrar)]
            org_count = len(orgs)
            if org_count > 2:
                organization_string = ", ".join(orgs[:-1]) + " and " + orgs[-1]
            elif org_count == 2:
                organization_string = "{} and {}".format(orgs[0], orgs[1])
            elif org_count == 1:
                organization_string = orgs[0]
            else:
                # this should never happen, consider raising an exception
                organization_string = '(error retrieving organization list)'
        return organization_string

    def handle_registrar_fields(form):
        if request.user.is_supported_by_registrar():
            registrars = set(org.registrar for org in request.user.organizations.all())
            if len(registrars) > 1:
                form.fields['registrar'].choices = [(registrar.id, registrar.name) for registrar in registrars]
            if len(registrars) == 1:
                form.fields['registrar'].widget = widgets.HiddenInput()
                registrar = registrars.pop()
                form.fields['registrar'].initial = registrar.id
                form.fields['registrar'].choices = [(registrar.id, registrar.email)]
        else:
            del form.fields['registrar']
        return form

    if request.method == 'POST':
        form = handle_registrar_fields(ContactForm(request.POST))
        if form.is_valid():
            # Assemble info for email
            from_address = form.cleaned_data['email']
            subject = "[perma-contact] " + form.cleaned_data['subject']
            context = {
                "message": form.cleaned_data['message'],
                "from_address": from_address,
                "referer": form.cleaned_data['referer'],
                "affiliation_string": affiliation_string()
            }
            if request.user.is_supported_by_registrar():
                # Send to all active registar users for registrar and cc Perma
                reg_id = form.cleaned_data['registrar']
                context["organization_string"] = formatted_organization_list(registrar=reg_id)
                send_user_email_copy_admins(
                    subject,
                    from_address,
                    [user.email for user in Registrar.objects.get(id=reg_id).active_registrar_users()],
                    request,
                    'email/registrar_contact.txt',
                    context
                )
                # redirect to a new URL:
                return HttpResponseRedirect(
                    reverse('contact_thanks') + "?{}".format(urlencode({'registrar': reg_id}))
                )
            else:
                # Send only to the admins
                send_admin_email(
                    subject,
                    from_address,
                    request,
                    'email/admin/contact.txt',
                    context
                )
                # redirect to a new URL:
                return HttpResponseRedirect(reverse('contact_thanks'))
        else:
            return render(request, 'contact.html', {'form': form})

    else:

        # Our contact form serves a couple of purposes
        # If we get a message parameter, we're getting a message from the create form
        # about a failed archive
        #
        # If we get a flagged parameter, we're getting the guid of an archive from the
        # Flag as inappropriate button on an archive page
        #
        # We likely want to clean up this contact for logic if we tack much else on

        subject = request.GET.get('subject', '')
        message = request.GET.get('message', '')

        flagged_archive_guid = request.GET.get('flag', '')
        if flagged_archive_guid:
            subject = 'Reporting Inappropriate Content'
            message = 'http://perma.cc/%s contains material that is inappropriate.' % flagged_archive_guid

        form = handle_registrar_fields(
            ContactForm(
                initial={
                    'message': message,
                    'subject': subject,
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'email': getattr(request.user, 'email', '')
                }
            )
        )

        return render(request, 'contact.html', {'form': form})

def contact_thanks(request):
    """
    The page users are delivered at after submitting the contact form.
    """
    registrar = Registrar.objects.filter(pk=request.GET.get('registrar', '-1')).first()
    return render(request, 'contact-thanks.html', {'registrar': registrar})
