from ratelimit.decorators import ratelimit
from datetime import timedelta
from dateutil.tz import tzutc
from io import StringIO
from link_header import Link as Rel, LinkHeader
from urllib.parse import urlencode
from timegate.utils import closest
from warcio.timeutils import datetime_to_http_date
from werkzeug.http import parse_date

from django.forms import widgets
from django.shortcuts import render, get_object_or_404, redirect
from django.http import (HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect,
    JsonResponse, HttpResponseNotFound, HttpResponseBadRequest)
from django.urls import reverse, NoReverseMatch
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_control

from perma.wsgi_utils import retry_on_exception

from ..models import Link, Registrar, Organization, LinkUser
from ..forms import ContactForm, ReportForm, check_honeypot
from ..utils import (if_anonymous, ratelimit_ip_key, redirect_to_download,
    protocol, stream_warc_if_permissible,
    timemap_url, timegate_url, memento_url, memento_data_for_url, url_with_qs_and_hash,
    remove_control_characters)
from ..email import send_admin_email, send_user_email_copy_admins

import logging

logger = logging.getLogger(__name__)
valid_serve_types = ['image', 'warc_download', 'standard']


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
    if request.user.is_authenticated and request.get_host() not in request.META.get('HTTP_REFERER',''):
        return HttpResponseRedirect(reverse('create_link'))

    else:
        # orgs_count = Organization.objects.count()
        # users_count = LinkUser.objects.count()
        # links_count = Link.objects.filter(is_private=False).count()

        return render(request, 'landing.html', {
            'this_page': 'landing',
            # 'orgs_count': orgs_count, 'users_count': users_count, 'links_count': links_count,
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
@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.HOUR_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.DAY_LIMIT, block=True, key=ratelimit_ip_key)
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
        if link.default_to_screenshot_view:
            serve_type = 'image'
        else:
            serve_type = 'standard'
    elif serve_type not in valid_serve_types:
        return HttpResponsePermanentRedirect(reverse('single_permalink', args=[canonical_guid]))

    # serve raw WARC
    if serve_type == 'warc_download':
        return stream_warc_if_permissible(link, request.user)

    # handle requested capture type
    if serve_type == 'image':
        capture = link.screenshot_capture

        # not all Perma Links have screenshots; if no screenshot is present,
        # forward to primary capture for playback or for appropriate error message
        if (not capture or capture.status != 'success') and link.primary_capture:
            return HttpResponseRedirect(reverse('single_permalink', args=[guid])+"?type=standard")
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

    # If this record was just created by the current user, we want to do some special-handling:
    # for instance, show them a message in the template, and give the playback extra time to initialize
    new_record = request.user.is_authenticated and link.created_by_id == request.user.id and not link.user_deleted \
                 and link.creation_timestamp > timezone.now() - timedelta(seconds=300)

    # Provide the max upload size, in case the upload form is used
    max_size = settings.MAX_ARCHIVE_FILE_SIZE / 1024 / 1024

    if not link.submitted_description:
        link.submitted_description = f"This is an archive of {link.submitted_url} from {link.creation_timestamp.strftime('%A %d, %B %Y')}"

    logger.debug(f"Preparing context for {link.guid}")
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

    if context['can_view'] and link.can_play_back():
        if new_record:
            logger.debug(f"Ensuring warc for {link.guid} has finished uploading.")
            def assert_exists(filename):
                assert default_storage.exists(filename)
            try:
                retry_on_exception(assert_exists, args=[link.warc_storage_file()], exception=AssertionError, attempts=settings.WARC_AVAILABLE_RETRIES)
            except AssertionError:
                logger.error(f"Made {settings.WARC_AVAILABLE_RETRIES} attempts to get {link.guid}'s warc; still not available.")
                # Let's consider this a HTTP 200, I think...
                return render(request, 'archive/playback-delayed.html', context,  status=200)

        logger.info(f'Preparing client-side playback for {link.guid}')
        context['client_side_playback_host'] = f"{settings.PLAYBACK_SUBDOMAIN}.{settings.HOST}"
        context['embed'] = False if request.GET.get('embed') == 'False' else True

    response = render(request, 'archive/single-link.html', context)

    # Adjust status code
    if link.user_deleted:
        response.status_code = 410
    elif not context['can_view'] and link.is_private:
        response.status_code = 403

    # Add memento headers, when appropriate
    logger.debug(f"Deciding whether to include memento headers for {link.guid}")
    if link.is_visible_to_memento():
        logger.debug(f"Including memento headers for {link.guid}")
        response['Memento-Datetime'] = datetime_to_http_date(link.creation_timestamp)
        # impose an arbitrary length-limit on the submitted URL, so that this header doesn't become illegally large
        url = link.submitted_url[:500]
        # strip control characters from url, if somehow they slipped in prior to https://github.com/harvard-lil/perma/commit/272b3a79d94a795142940281c9444b45c24a05db
        url = remove_control_characters(url)
        response['Link'] = str(
            LinkHeader([
                Rel(url, rel='original'),
                Rel(timegate_url(request, url), rel='timegate'),
                Rel(timemap_url(request, url, 'link'), rel='timemap', type='application/link-format'),
                Rel(timemap_url(request, url, 'json'), rel='timemap', type='application/json'),
                Rel(timemap_url(request, url, 'html'), rel='timemap', type='text/html'),
                Rel(memento_url(request, link), rel='memento', datetime=datetime_to_http_date(link.creation_timestamp)),
            ])
        )

    # Prevent browser caching
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    logger.debug(f"Returning response for {link.guid}")
    return response


def serve_warc(request, guid):
    """
    This is a redundant route for downloading a warc, for use in client-side playback,
    which has specific requirements:
    - the warc must be served from a URL ending in `.warc`
    - the response cannot be streamed
    """

    canonical_guid = Link.get_canonical_guid(guid)
    link = get_object_or_404(Link.objects.all_with_deleted(), guid=canonical_guid)
    return stream_warc_if_permissible(link, request.user, stream=False)


@if_anonymous(cache_control(max_age=settings.CACHE_MAX_AGES['timemap']))
@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.HOUR_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.DAY_LIMIT, block=True, key=ratelimit_ip_key)
def timemap(request, response_format, url):
    url = url_with_qs_and_hash(url, request.META['QUERY_STRING'])
    data = memento_data_for_url(request, url)
    if data:
        if response_format == 'json':
            response = JsonResponse(data)
        elif response_format == 'html':
            response = render(request, 'memento/timemap.html', data)
        else:
            content_type = 'application/link-format'
            file = StringIO()
            file.writelines(f"{line},\n" for line in [
                Rel(data['original_uri'], rel='original'),
                Rel(data['timegate_uri'], rel='timegate'),
                Rel(data['self'], rel='self', type='application/link-format'),
                Rel(data['timemap_uri']['link_format'], rel='timemap', type='application/link-format'),
                Rel(data['timemap_uri']['json_format'], rel='timemap', type='application/json'),
                Rel(data['timemap_uri']['html_format'], rel='timemap', type='text/html')
            ] + [
                Rel(memento['uri'], rel='memento', datetime=datetime_to_http_date(memento['datetime'])) for memento in data['mementos']['list']
            ])
            file.seek(0)
            response = HttpResponse(file, content_type=f'{content_type}')
    else:
        if response_format == 'html':
            response = render(request, 'memento/timemap.html', {"original_uri": url}, status=404)
        else:
            response = HttpResponseNotFound('404 page not found\n')

    response['X-Memento-Count'] = str(len(data['mementos']['list'])) if data else 0
    return response


@if_anonymous(cache_control(max_age=settings.CACHE_MAX_AGES['timegate']))
@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.HOUR_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.DAY_LIMIT, block=True, key=ratelimit_ip_key)
def timegate(request, url):
    # impose an arbitrary length-limit on the submitted URL, so that the headers don't become illegally large
    url = url_with_qs_and_hash(url, request.META['QUERY_STRING'])[:500]
    data = memento_data_for_url(request, url)
    if not data:
        return HttpResponseNotFound('404 page not found\n')

    accept_datetime = request.META.get('HTTP_ACCEPT_DATETIME')
    if accept_datetime:
        accept_datetime = parse_date(accept_datetime)
        if not accept_datetime:
            return HttpResponseBadRequest('Invalid value for Accept-Datetime.')
    else:
        accept_datetime = timezone.now()
    accept_datetime = accept_datetime.replace(tzinfo=tzutc())

    target, target_datetime = closest([m.values() for m in data['mementos']['list']], accept_datetime)

    response = redirect(target)
    response['Vary'] = 'accept-datetime'
    response['Link'] = str(
        LinkHeader([
            Rel(data['original_uri'], rel='original'),
            Rel(data['timegate_uri'], rel='timegate'),
            Rel(data['timemap_uri']['link_format'], rel='timemap', type='application/link-format'),
            Rel(data['timemap_uri']['json_format'], rel='timemap', type='application/json'),
            Rel(data['timemap_uri']['html_format'], rel='timemap', type='text/html'),
            Rel(data['mementos']['first']['uri'], rel='first memento', datetime=datetime_to_http_date(data['mementos']['first']['datetime'])),
            Rel(data['mementos']['last']['uri'], rel='last memento', datetime=datetime_to_http_date(data['mementos']['last']['datetime'])),
            Rel(target, rel='memento', datetime=datetime_to_http_date(target_datetime)),
        ])
    )
    return response


def rate_limit(request, exception):
    """
    When a user hits a rate limit, send them here.
    """
    return render(request, "rate_limit.html")


@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def contact(request):
    """
    Our contact form page
    """
    def affiliation_string():
        affiliation_string = ''
        if request.user.is_authenticated:
            if request.user.registrar:
                affiliation_string = f"{request.user.registrar.name} (Registrar)"
            else:
                affiliations = [f"{org.name} ({org.registrar.name})" for org in request.user.organizations.all().order_by('registrar')]
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
                organization_string = f"{orgs[0]} and {orgs[1]}"
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

        if something_took_the_bait := check_honeypot(request, 'contact_thanks'):
            return something_took_the_bait

        form = handle_registrar_fields(ContactForm(request.POST))

        if form.is_valid():
            # Assemble info for email
            from_address = form.cleaned_data['email']
            subject = "[perma-contact] " + form.cleaned_data['subject']
            context = {
                "message": form.cleaned_data['box2'],
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
                    [user.raw_email for user in Registrar.objects.get(id=reg_id).active_registrar_users()],
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

        upgrade = request.GET.get('upgrade', '')
        if upgrade == 'organization' :
            subject = 'Upgrade to Unlimited Account'
            message = "My organization is interested in a subscription to Perma.cc."
        else:
            # all other values of `upgrade` are disallowed
            upgrade = None

        form = handle_registrar_fields(
            ContactForm(
                initial={
                    'box2': message,
                    'subject': subject,
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'email': getattr(request.user, 'email', '')
                }
            )
        )

        return render(request, 'contact.html', {'form': form, 'upgrade': upgrade})


def contact_thanks(request):
    """
    The page users are delivered at after submitting the contact form.
    """
    registrar = Registrar.objects.filter(pk=request.GET.get('registrar', '-1')).first()
    return render(request, 'contact-thanks.html', {'registrar': registrar})


@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def report(request):
    """
    Report inappropriate content.
    """
    def affiliation_string():
        affiliation_string = ''
        if request.user.is_authenticated:
            if request.user.registrar:
                affiliation_string = f"{request.user.registrar.name} (Registrar)"
            else:
                affiliations = [f"{org.name} ({org.registrar.name})" for org in request.user.organizations.all().order_by('registrar')]
                if affiliations:
                    affiliation_string = ', '.join(affiliations)
        return affiliation_string

    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'contact_thanks'):
            return something_took_the_bait

        form = ReportForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['guid']:
                from_address = form.cleaned_data['email']
                subject = "[perma-contact] Reporting Inappropriate Content"
                context = {
                    "reason": form.cleaned_data['reason'],
                    "source": form.cleaned_data['source'],
                    "message": form.cleaned_data['box2'],
                    "from_address": from_address,
                    "guid": form.cleaned_data['guid'],
                    "referer": form.cleaned_data['referer'],
                    "affiliation_string": affiliation_string()
                }
                send_admin_email(
                    subject,
                    from_address,
                    request,
                    'email/admin/report.txt',
                    context
                )
            return HttpResponseRedirect(reverse('contact_thanks'))
        else:
            return render(request, 'report.html', {
                'form': form,
                'guid': request.POST.get('guid', '')
            })

    else:
        guid = request.GET.get('guid', '')
        form = ReportForm(
                initial={
                    'guid': guid,
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'email': getattr(request.user, 'email', '')
                }
        )
        return render(request, 'report.html', {
            'form': form,
            'guid': guid
        })


def robots_txt(request):
    """
    robots.txt
    """
    from ..urls import urlpatterns

    disallowed_prefixes = ['_', 'archive-', 'api_key', 'errors', 'log', 'manage', 'password', 'register', 'service', 'settings', 'sign-up']
    allow = ['/$']
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
