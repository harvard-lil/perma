from ratelimit.decorators import ratelimit
from datetime import timedelta
from dateutil.tz import tzutc
from io import StringIO
from link_header import Link as Rel, LinkHeader
from urllib.parse import urlencode
import time
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
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_control

from django.utils.six.moves.http_client import responses


from ..models import Link, Registrar, Organization, LinkUser
from ..forms import ContactForm
from ..utils import (if_anonymous, ratelimit_ip_key, redirect_to_download,
    protocol, stream_warc_if_permissible, set_options_headers,
    timemap_url, timegate_url, memento_url, memento_data_for_url, url_with_qs_and_hash,
    get_client_ip, remove_control_characters)
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
    if request.user.is_authenticated and request.get_host() not in request.META.get('HTTP_REFERER',''):
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
        serve_type = 'source'
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
            return HttpResponseRedirect(reverse('single_permalink', args=[guid]))
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
        link.submitted_description = "This is an archive of %s from %s" % (link.submitted_url, link.creation_timestamp.strftime("%A %d, %B %Y"))

    logger.info(f"Preparing context for {link.guid}")
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
            logger.info(f"Ensuring warc for {link.guid} has finished uploading.")
            start_time = time.time()
            while not default_storage.exists(link.warc_storage_file()):
                wait_time = time.time() - start_time
                if wait_time > settings.WARC_AVAILABLE_TIMEOUT:
                    logger.error(f"Waited {wait_time} for {link.guid}'s warc; still not available.")
                    return render(request, 'archive/playback-delayed.html', context,  status=500)
                time.sleep(1)
        try:
            logger.info(f"Initializing play back of {link.guid}")
            wr_username = link.init_replay_for_user(request)
        except Exception:  # noqa
            # We are experiencing many varieties of transient flakiness in playback:
            # second attempts, triggered by refreshing the page, almost always seem to work.
            # While we debug... let's give playback a second try here, and see if this
            # noticeably improves user experience.
            logger.exception(f"First attempt to init replay of {link.guid} failed. (Retrying: observe whether this error recurs.)")
            time.sleep(settings.WR_PLAYBACK_RETRY_AFTER)
            logger.info(f"Initializing play back of {link.guid} (2nd try)")
            wr_username = link.init_replay_for_user(request)

        logger.info(f"Updating context with WR playback information for {link.guid}")
        context.update({
            'wr_host': settings.PLAYBACK_HOST,
            'wr_prefix': link.wr_iframe_prefix(wr_username),
            'wr_url': capture.url,
            'wr_timestamp': link.creation_timestamp.strftime('%Y%m%d%H%M%S'),
        })

    logger.info(f"Rendering template for {link.guid}")
    response = render(request, 'archive/single-link.html', context)

    # Adjust status code
    if link.user_deleted:
        response.status_code = 410
    elif not context['can_view'] and link.is_private:
        response.status_code = 403

    # Add memento headers, when appropriate
    logger.info(f"Deciding whether to include memento headers for {link.guid}")
    if link.is_visible_to_memento():
        logger.info(f"Including memento headers for {link.guid}")
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
    logger.info(f"Returning response for {link.guid}")
    return response


def set_iframe_session_cookie(request):
    """
    The <iframe> used for Perma Link playback serves content from Webrecorder.
    If the Perma Link is private, playback requires a WR session cookie.
    The cookie's value is set via a WR api call during Perma's
    `link.init_replay_for_user` and is stored in Perma's session data.
    If the iframe requests a resource without the cookie,
    WR will redirect here. This route in turn redirects back to WR with the
    session cookie as a GET param. WR sets the cookie in the browser, and then,
    finally, redirects to the originally requested resource.
    """
    if request.method == 'OPTIONS':
        # no redirects required; subsequent requests from the browser get the cookie
        response = HttpResponse()
    else:
        cookie = urlencode({'cookie': request.session.get('wr_private_session_cookie')})
        url = protocol() + settings.PLAYBACK_HOST + '/_set_session?{0}&{1}'.format(request.META.get('QUERY_STRING', ''), cookie)
        response = HttpResponseRedirect(url)
        response['Cache-Control'] = 'no-cache'

    # set CORS headers (for both OPTIONS and actual redirect)
    set_options_headers(request, response)
    return response


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

    target, target_datetime = closest(map(lambda m: m.values(), data['mementos']['list']), accept_datetime)

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


@csrf_exempt
@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def contact(request):
    """
    Our contact form page
    """
    def affiliation_string():
        affiliation_string = ''
        if request.user.is_authenticated:
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
        # Only send email if box2 is filled out and box1 is not.
        # box1 is display: none, so should never be filled out except by spam bots.
        if form.data.get('box1'):
            user_ip = get_client_ip(request)
            logger.info(f"Suppressing invalid contact email from {user_ip}: {form.data}")
            return HttpResponseRedirect(reverse('contact_thanks'))

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

        upgrade = request.GET.get('upgrade', '')
        if upgrade == 'organization' :
            subject = 'Upgrade to Unlimited Account'
            message = "My organization is interested in a subscription to Perma.cc."
        else:
            # all other values of `upgrade` are disallowed
            upgrade = None

        flagged_archive_guid = request.GET.get('flag', '')
        if flagged_archive_guid:
            subject = 'Reporting Inappropriate Content'
            message = 'http://perma.cc/%s contains material that is inappropriate.' % flagged_archive_guid

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


def robots_txt(request):
    """
    robots.txt
    """
    from ..urls import urlpatterns

    disallowed_prefixes = ['_', 'archive-', 'api_key', 'errors', 'log', 'manage', 'password', 'register', 'service', 'settings', 'sign-up']
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


@csrf_exempt
def archive_error(request):
    """
    Replay content not found error page
    """

    # handle cors options for error page redirect from cors
    if request.method == 'OPTIONS':
        response = HttpResponse()
        set_options_headers(request, response)
        return response

    reported_status = request.GET.get('status')
    status_code = int(reported_status or '200')
    if status_code != 404:
        # We only want to return 404 and 200 here, to avoid complications with Cloudflare.
        # Other error statuses always (?) indicate some problem with WR, not a status code we
        # need or want to pass on to the user.
        status_code = 200
    response = render(request, 'archive/archive-error.html', {
        'err_url': request.GET.get('url'),
        'timestamp': request.GET.get('timestamp'),
        'status': f'{status_code} {responses.get(status_code)}',
        'err_msg': request.GET.get('error'),
    }, status=status_code)

    # even if not setting full headers (eg. if Origin is not set)
    # still set set Access-Control-Allow-Origin to content host to avoid Chrome CORB issues
    set_options_headers(request, response, always_set_allowed_origin=True)
    return response


