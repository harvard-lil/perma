from ratelimit.decorators import ratelimit
from datetime import timedelta
from urllib.parse import urlencode

from django.contrib.auth.views import redirect_to_login
from django.forms import widgets
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse, NoReverseMatch
from django.conf import settings
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_control

from ..models import Link, Registrar, Organization, LinkUser
from ..forms import ContactForm
from ..utils import (if_anonymous, ratelimit_ip_key, redirect_to_download,
    parse_user_agent, protocol, stream_warc_if_permissible)
from ..email import send_admin_email, send_user_email_copy_admins

import logging

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
    halfway_point = int(len(partners)/2)

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

@if_anonymous(cache_control(max_age=settings.CACHE_MAX_AGES['single_permalink']))
#@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
#@ratelimit(rate=settings.HOUR_LIMIT, block=True, key=ratelimit_ip_key)
#@ratelimit(rate=settings.DAY_LIMIT, block=True, key=ratelimit_ip_key)
def single_permalink(request, guid):
    """
    Given a Perma ID, serve it up.
    """
    raw_user_agent = request.META.get('HTTP_USER_AGENT', '')

    # Create a canonical version of guid (non-alphanumerics removed, hyphens every 4 characters, uppercase),
    # and forward to that if it's different from current guid.
    canonical_guid = Link.get_canonical_guid(guid)

    # We only do the redirect if the correctly-formatted GUID actually exists --
    # this prevents actual 404s from redirecting with weird formatting.
    link = get_object_or_404(Link.objects.all_with_deleted(), guid=canonical_guid)

    if canonical_guid != guid:
        return HttpResponsePermanentRedirect(reverse('single_permalink', args=[canonical_guid]))

    # Forward to replacement link if replacement_link is set.
    if link.replacement_link_id:
        return HttpResponseRedirect(reverse('single_permalink', args=[link.replacement_link_id]))

    # If we get an unrecognized archive type (which could be an old type like 'live' or 'pdf'), forward to default version
    serve_type = request.GET.get('type')
    if serve_type is None:
        serve_type = 'source'
    elif serve_type not in valid_serve_types:
        return HttpResponsePermanentRedirect(reverse('single_permalink', args=[canonical_guid]))

    # serve raw WARC
    if serve_type == 'warc_download':
        return stream_warc_if_permissible(link, request.user)

    # Special handling for private links on Safari:
    # Safari won't let us set the auth cookie for the WARC_HOST domain inside the iframe, unless we've already set a
    # cookie on that domain outside the iframe. So do a redirect to WARC_HOST to set a cookie and then come back.
    # safari=1 in the query string indicates that the redirect has already happened.
    # See http://labs.fundbox.com/third-party-cookies-with-ie-at-2am/
    if link.is_private and not request.GET.get('safari'):
        user_agent = parse_user_agent(raw_user_agent)
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
            return HttpResponseRedirect(reverse('single_permalink', args=[guid])+"?type=image")

    try:
        capture_mime_type = capture.mime_type()
    except AttributeError:
        # If capture is deleted, then mime type does not exist. Catch error.
        capture_mime_type = None

    # Special handling for mobile pdf viewing because it can be buggy
    # Redirecting to a download page if on mobile
    redirect_to_download_view = redirect_to_download(capture_mime_type, raw_user_agent)

    # If this record was just created by the current user, show them a new record message
    new_record = request.user.is_authenticated() and link.created_by_id == request.user.id and not link.user_deleted \
                 and link.creation_timestamp > timezone.now() - timedelta(seconds=300)

    # Provide the max upload size, in case the upload form is used
    max_size = settings.MAX_ARCHIVE_FILE_SIZE / 1024 / 1024

    if not link.submitted_description:
        link.submitted_description = "This is an archive of %s from %s" % (link.submitted_url, link.creation_timestamp.strftime("%A %d, %B %Y"))

    context = {
        'link': link,
        'redirect_to_download_view': redirect_to_download_view,
        'mime_type': capture_mime_type,
        'can_view': request.user.can_view(link),
        'can_edit': request.user.can_edit(link),
        'can_delete': request.user.can_delete(link),
        'can_toggle_private': request.user.can_toggle_private(link),
        'capture': capture,
        'serve_type': serve_type,
        'new_record': new_record,
        'this_page': 'single_link',
        'max_size': max_size,
        'link_url': settings.HOST + '/' + link.guid,
        'protocol': protocol(),
    }

    response = render(request, 'archive/single-link.html', context)

    # Adjust status code
    if link.user_deleted:
        response.status_code = 410
    elif not context['can_view'] and link.is_private:
        response.status_code = 403

    # Add memento headers
    response['Memento-Datetime'] = link.memento_formatted_date
    link_memento_headers = '<{0}>; rel="original"; datetime="{1}",<{2}>; rel="memento"; datetime="{1}",<{3}>; rel="timegate",<{4}>; rel="timemap"; type="application/link-format"'
    response['Link'] = link_memento_headers.format(link.ascii_safe_url, link.memento_formatted_date, link.memento, link.timegate, link.timemap)

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
                affiliation_string = u"{} (Registrar)".format(request.user.registrar.name)
            else:
                affiliations = [u"{} ({})".format(org.name, org.registrar.name) for org in request.user.organizations.all().order_by('registrar')]
                if affiliations:
                    affiliation_string = u', '.join(affiliations)
        return affiliation_string

    def formatted_organization_list(registrar):
        organization_string = u''
        if request.user.is_organization_user:
            orgs = [org.name for org in request.user.organizations.filter(registrar=registrar)]
            org_count = len(orgs)
            if org_count > 2:
                organization_string = u", ".join(orgs[:-1]) + u" and " + orgs[-1]
            elif org_count == 2:
                organization_string = u"{} and {}".format(orgs[0], orgs[1])
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


def robots_txt(request):
    """
    robots.txt
    """
    from ..urls import urlpatterns

    disallowed_prefixes = ['errors', 'log', 'manage', 'password', 'register', 'service', 'settings', 'sign-up']
    allow = []
    # some urlpatterns do not have names
    names = [urlpattern.name for urlpattern in urlpatterns if urlpattern.name is not None]
    for name in names:
        # urlpatterns that take parameters can't be reversed
        try:
            url = reverse(name)
            disallowed = any(url[1:].startswith(prefix) for prefix in disallowed_prefixes)
            if not disallowed and url != '/':
                allow.append(url)
        except NoReverseMatch:
            pass
    disallow = list(Link.GUID_CHARACTER_SET) + disallowed_prefixes
    return render(request, 'robots.txt', {'allow': allow, 'disallow': disallow}, content_type='text/plain; charset=utf-8')
