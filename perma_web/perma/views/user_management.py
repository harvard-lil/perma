import csv
from datetime import timedelta
import itertools
import logging
from typing import Literal

import celery
import redis

from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from ratelimit.decorators import ratelimit

from django.views.generic import UpdateView
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, PasswordChangeForm
from django.contrib.auth import views as auth_views
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.db.models import Count, F, Max, Sum
from django.db.models.expressions import RawSQL
from django.db.models.functions import Coalesce, Greatest
from django.db.models.manager import BaseManager
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    Http404,
    HttpResponseForbidden,
    JsonResponse,
)

from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.template.context_processors import csrf
from django.contrib import messages

from perma.forms import (
    check_honeypot,
    RegistrarForm,
    LibraryRegistrarForm,
    OrganizationWithRegistrarForm,
    OrganizationForm,
    FirmOrganizationForm,
    FirmUsageForm,
    UserForm,
    UserFormWithRegistrar,
    UserFormWithSponsoringRegistrar,
    UserFormWithOrganization,
    CreateUserFormWithCourt,
    CreateUserFormWithFirm,
    CreateUserFormWithUniversity,
    UserAddRegistrarForm,
    UserAddSponsoringRegistrarForm,
    UserAddOrganizationForm,
    UserFormWithAdmin,
    UserAddAdminForm,
    UserUpdateProfileForm,
)
from perma.models import Registrar, LinkUser, Organization, Link, Capture, CaptureJob, ApiKey, Sponsorship, Folder, InternetArchiveItem
from perma.utils import (apply_search_query, apply_pagination, apply_sort_order, get_form_data,
    ratelimit_ip_key, user_passes_test_or_403, prep_for_perma_payments,
    get_complete_ia_rate_limiting_info)
from perma.email import send_admin_email, send_user_email
from perma.exceptions import PermaPaymentsCommunicationException

logger = logging.getLogger(__name__)
valid_member_sorts = ['last_name', '-last_name', 'date_joined', '-date_joined', 'last_login', '-last_login', 'link_count', '-link_count']
valid_registrar_sorts = ['name', '-name', 'link_count', '-link_count', '-date_created', 'date_created', 'last_active', '-last_active']
valid_org_sorts = ['name', '-name', 'link_count', '-link_count', '-date_created', 'date_created', 'last_active', '-last_active', 'organization_users', 'organization_users']


### HELPERS ###

class RequireOrgOrRegOrAdminUser:
    """ Mixin for class-based views that requires user to be an org user, registrar user, or admin. """
    @method_decorator(user_passes_test_or_403(lambda user: user.is_registrar_user() or user.is_organization_user or user.is_staff))
    def dispatch(self, request, *args, **kwargs):
        return super(RequireOrgOrRegOrAdminUser, self).dispatch(request, *args, **kwargs)

class RequireRegOrAdminUser:
    """ Mixin for class-based views that requires user to be a registrar user or admin. """
    @method_decorator(user_passes_test_or_403(lambda user: user.is_registrar_user() or user.is_staff))
    def dispatch(self, request, *args, **kwargs):
        return super(RequireRegOrAdminUser, self).dispatch(request, *args, **kwargs)

class RequireAdminUser:
    """ Mixin for class-based views that requires user to be an admin. """
    @method_decorator(user_passes_test_or_403(lambda user: user.is_staff))
    def dispatch(self, request, *args, **kwargs):
        return super(RequireAdminUser, self).dispatch(request, *args, **kwargs)


@user_passes_test_or_403(lambda user: user.is_staff)
def stats(request, stat_type=None):

    out = None

    if stat_type == "days":
        # get link counts for last 30 days
        out = {'days':[]}
        for days_ago in range(30):
            end_date = timezone.now() - timedelta(days=days_ago)
            start_date = end_date - timedelta(days=1)
            day = {
                'days_ago': days_ago,
                'start_date': start_date,
                'end_date': end_date,
                'top_users': list(LinkUser.objects
                                          .filter(created_links__creation_timestamp__gt=start_date,created_links__creation_timestamp__lt=end_date)
                                          .annotate(links_count=Count('created_links'))
                                          .order_by('-links_count')[:3]
                                          .values('email','links_count')),
                'statuses': Capture.objects
                                   .filter(role='primary', link__creation_timestamp__gt=start_date, link__creation_timestamp__lt=end_date)
                                   .values('status')
                                   .annotate(count=Count('status')),
                'capture_time_dist': '-',
                'wait_time_dist': '-',
            }

            # calculate 5%/50%/95% capture and wait timings
            capture_time_fields = CaptureJob.objects.filter(
                link__creation_timestamp__gt=start_date, link__creation_timestamp__lt=end_date
            ).values(
                'capture_start_time', 'link__creation_timestamp', 'capture_end_time'
            ).exclude(capture_start_time=None).exclude(capture_end_time=None)
            if capture_time_fields:
                ctf_len = len(capture_time_fields)
                capture_times = sorted(c['capture_end_time']-c['capture_start_time'] for c in capture_time_fields)
                wait_times = sorted(c['capture_start_time']-c['link__creation_timestamp'] for c in capture_time_fields)
                day['capture_time_dist'] = " / ".join(str(i) for i in [capture_times[int(ctf_len*.05)], capture_times[int(ctf_len*.5)], capture_times[int(ctf_len*.95)]])
                day['wait_time_dist'] = " / ".join(str(i) for i in [wait_times[int(ctf_len*.05)], wait_times[int(ctf_len*.5)], wait_times[int(ctf_len*.95)]])

            day['statuses'] = dict((x['status'], x['count']) for x in day['statuses'])
            day['link_count'] = sum(day['statuses'].values())
            out['days'].append(day)

    elif stat_type == "emails":
        # get users by email top-level domain
        out = {
            'users_by_domain': list(LinkUser.objects
                .filter(is_confirmed=True)
                # Postgres doesn't presently let you extract the last element of a split cleanly:
                # technique from https://www.postgresql-archive.org/split-part-for-the-last-element-td6159483.html
                .annotate(domain=RawSQL("reverse(split_part(reverse(lower(email)), '.', 1))", []))
                .values('domain')
                .annotate(count=Count('domain'))
                .order_by('-count')
                .values('domain', 'count'))
        }

    elif stat_type == "random":
        # random
        out = {
            'total_link_count': Link.objects.count(),
            'private_link_count': Link.objects.filter(is_private=True).count(),
            'private_user_direction': Link.objects.filter(is_private=True, private_reason='user').count(),
            'private_domain': Link.objects.filter(is_private=True, private_reason='domain').count(),
            'private_meta': Link.objects.filter(is_private=True, private_reason='meta').count(),
            'private_meta_perma': Link.objects.filter(is_private=True, private_reason='meta_perma').count(),
            'private_takedown': Link.objects.filter(is_private=True, private_reason='takedown').count(),
            'private_flagged': Link.objects.filter(is_private=True, private_reason='flagged').count(),
            'private_meta_failure': Link.objects.filter(is_private=True, private_reason='failure').count(),
            'links_w_meta_failure_tag': Link.objects.filter(tags__name__in=['meta-tag-retrieval-failure']).count(),
            'links_w_timeout_failure_tag': Link.objects.filter(tags__name__in=['timeout-failure']).count(),
            'links_w_browser_crashed_tag': Link.objects.filter(tags__name__in=['browser-crashed']).count(),
            'total_user_count': LinkUser.objects.count(),
            'unconfirmed_user_count': LinkUser.objects.filter(is_confirmed=False).count(),
            'users_with_ten_links':LinkUser.objects.filter(link_count=10).count(),
            'confirmed_users_with_no_links':LinkUser.objects.filter(is_confirmed=True, link_count=0).count()
        }
        out['private_link_percentage'] = round(100.0*out['private_link_count']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_user_percentage_of_total'] = round(100.0*out['private_user_direction']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_user_percentage_of_private'] = round(100.0*out['private_user_direction']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_domain_percentage_of_total'] = round(100.0*out['private_domain']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_domain_percentage_of_private'] = round(100.0*out['private_domain']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_meta_perma_percentage_of_total'] = round(100.0*out['private_meta_perma']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_meta_perma_percentage_of_private'] = round(100.0*out['private_meta_perma']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_meta_percentage_of_total'] = round(100.0*out['private_meta']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_meta_percentage_of_private'] = round(100.0*out['private_meta']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_flagged_percentage_of_total'] = round(100.0*out['private_flagged']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_flagged_percentage_of_private'] = round(100.0*out['private_flagged']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_takedown_percentage_of_total'] = round(100.0*out['private_takedown']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_takedown_percentage_of_private'] = round(100.0*out['private_takedown']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_meta_failure_percentage_of_total'] = round(100.0*out['private_meta_failure']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_meta_failure_percentage_of_private'] = round(100.0*out['private_meta_failure']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['tagged_meta_failure_percentage_of_total'] = round(100.0*out['links_w_meta_failure_tag']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['tagged_timeout_failure_percentage_of_total'] = round(100.0*out['links_w_timeout_failure_tag']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['tagged_browser_crashed_percentage_of_total'] = round(100.0*out['links_w_browser_crashed_tag']/out['total_link_count'], 1) if out['total_link_count'] else 0

        out['unconfirmed_user_percentage'] = round(100.0*out['unconfirmed_user_count']/out['total_user_count'], 1) if out['total_user_count'] else 0
        out['users_with_ten_links_percentage'] = round(100.0*out['users_with_ten_links']/out['total_user_count'], 1) if out['total_user_count'] else 0
        out['confirmed_users_with_no_links_percentage'] = round(100.0*out['confirmed_users_with_no_links']/out['total_user_count'], 1) if out['total_user_count'] else 0


    elif stat_type == "celery":
        inspector = celery.current_app.control.inspect()
        active = inspector.active()
        reserved = inspector.reserved()
        stats = inspector.stats()
        queues = []
        if active is not None:
            for queue in sorted(active.keys()):
                try:
                    queues.append({
                        'name': queue,
                        'active': active[queue],
                        'reserved': reserved[queue],
                        'stats': stats[queue],
                    })
                except (KeyError, TypeError):
                    pass
        out = {'queues':queues}

    elif stat_type == "celery_queues":
        r = redis.from_url(settings.CELERY_BROKER_URL)
        out = {
            'total_main_queue': r.llen('celery'),
            'total_background_queue': r.llen('background'),
            'total_ia_queue': r.llen('ia'),
            'total_ia_readonly_queue': r.llen('ia-readonly'),
            'total_wacz_conversion_queue': r.llen('wacz-conversion')
        }

    elif stat_type == "job_queue":
        job_queues = CaptureJob.objects.filter(status='pending').order_by('order', 'pk').select_related('link', 'link__created_by')
        job_queues = dict(itertools.groupby(job_queues, lambda x: 'human' if x.human else 'robot'))
        for queue_key, queue in job_queues.items():
            job_queues[queue_key] = [{'email':email, 'count':len(list(jobs))} for email, jobs in itertools.groupby(queue, lambda x: x.link.created_by.email)]
        out = {
            'job_queues': job_queues,
            'active_jobs': [{
                'link_id': j.link_id,
                'email': j.link.created_by.email,
                'attempt': j.attempt,
                'step_count': round(j.step_count, 2),
                'step_description': j.step_description,
                'capture_start_time': j.capture_start_time
            } for j in CaptureJob.objects.filter(status='in_progress').select_related('link', 'link__created_by')]
        }

    elif stat_type == 'rate_limits':
        out = get_complete_ia_rate_limiting_info()
        out["inflight"] = InternetArchiveItem.inflight_task_count()

        r = redis.from_url(settings.CELERY_BROKER_URL)
        out['total_ia_queue'] = r.llen('ia')
        out['total_ia_readonly_queue'] =  r.llen('ia-readonly')

    elif stat_type == 'capture_errors':

        # Set up time ranges
        now = timezone.now()
        last_24_hrs = (
            now - timedelta(days=1),
            now
        )
        previous_24_hrs = (
            now - timedelta(days=2),
            now - timedelta(days=1)
        )
        last_hour = (
            now - timedelta(hours=1),
            now
        )
        last_hour_on_previous_day = (
            now - timedelta(days=1) - timedelta(hours=1),
            now - timedelta(days=1)
        )
        last_3_hrs = (
            now - timedelta(hours=3),
            now
        )
        last_3_hrs_on_previous_day = (
            now - timedelta(days=1) - timedelta(hours=3),
            now - timedelta(days=1)
        )
        ranges = {
            "last_24_hrs": last_24_hrs,
            "previous_24_hrs": previous_24_hrs,
            "last_hour": last_hour,
            "last_hour_on_previous_day": last_hour_on_previous_day,
            "last_3_hrs": last_3_hrs,
            "last_3_hrs_on_previous_day": last_3_hrs_on_previous_day
        }

        out = {}

        for range_name, range_tuple in ranges.items():

            #
            # Get Totals
            #

            completed = CaptureJob.objects.filter(
                engine='scoop-api',
                status='completed',
                capture_start_time__range=range_tuple
            ).count()

            failed = CaptureJob.objects.filter(
                engine='scoop-api',
                status='failed',
                capture_start_time__range=range_tuple
            ).count()

            denominator = completed + failed

            #
            # Get By Error Type
            #
            if denominator:

                celery_timeout = Link.objects.all_with_deleted().filter(
                    tags__name__in=['timeout-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                proxy_error = Link.objects.all_with_deleted().filter(
                    tags__name__in=['scoop-proxy-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                blocklist_error = Link.objects.all_with_deleted().filter(
                    tags__name__in=['scoop-blocklist-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                playwright_error = Link.objects.all_with_deleted().filter(
                    tags__name__in=['scoop-playwright-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                timeout = Link.objects.all_with_deleted().filter(
                    tags__name__in=['scoop-silent-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                didnt_load = Link.objects.all_with_deleted().filter(
                    tags__name__in=['scoop-load-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                out[range_name] = {
                    "completed": completed,
                    "completed_percent": round(completed/denominator * 100, 1),
                    "failed": failed,
                    "failed_percent": round(failed/denominator * 100, 1),
                    "celery_timeout": celery_timeout,
                    "celery_timeout_percent": round(celery_timeout/denominator * 100, 1),
                    "proxy_error": proxy_error,
                    "proxy_error_percent": round(proxy_error/denominator * 100, 1),
                    "blocklist_error": blocklist_error,
                    "blocklist_error_percent": round(blocklist_error/denominator * 100, 1),
                    "playwright_error": playwright_error,
                    "playwright_error_percent": round(playwright_error/denominator * 100, 1),
                    "timeout": timeout,
                    "timeout_percent": round(timeout/denominator * 100, 1),
                    "didnt_load": didnt_load,
                    "didnt_load_percent": round(didnt_load/denominator * 100, 1),
                }

            else:

                out[range_name] = {
                    "completed": 0,
                    "completed_percent": 0,
                    "failed": 0,
                    "failed_percent": 0,
                    "celery_timeout": 0,
                    "celery_timeout_percent": 0,
                    "proxy_error": 0,
                    "proxy_error_percent": 0,
                    "blocklist_error": 0,
                    "blocklist_error_percent": 0,
                    "playwright_error": 0,
                    "playwright_error_percent": 0,
                    "timeout": 0,
                    "timeout_percent": 0,
                    "didnt_load": 0,
                    "didnt_load_percent": 0,
                }

    if out:
        return JsonResponse(out)

    else:
        return render(request, 'user_management/stats.html')


@user_passes_test_or_403(lambda user: user.is_staff)
def manage_registrar(request):
    """
    Perma admins can manage registrars (libraries)
    """

    # handle creation of new registrars
    form = RegistrarForm(get_form_data(request), prefix = "a")
    if request.method == 'POST':
        if form.is_valid():
            new_registrar = form.save(commit=False)
            new_registrar.status = "approved"
            new_registrar.save()

            return HttpResponseRedirect(reverse('user_management_manage_registrar'))

    registrars = Registrar.objects.all()

    # handle annotations
    registrars = registrars.annotate(
        registrar_users=Count('users', distinct=True),
        last_active_registrar=Max('users__last_login'),
        last_active_org_user=Max('organizations__users__last_login')
    ).annotate(
        # Greatest on MySQL returns NULL if any fields are NULL:
        # use of Coalesce here is a workaround
        # https://docs.djangoproject.com/en/2.0/ref/models/database-functions/
        last_active=Greatest(Coalesce('last_active_registrar', 'last_active_org_user'), 'last_active_org_user')
    )

    # handle sorting
    registrars, sort = apply_sort_order(request, registrars, valid_registrar_sorts)

    # handle search
    registrars, search_query = apply_search_query(request, registrars, ['name', 'email', 'website'])

    # handle status filter
    status = request.GET.get('status', '')
    if status:
        registrars = registrars.filter(status=status)

    orgs_count = Organization.objects.filter(registrar__in=registrars).count()
    #users_count = registrars.aggregate(count=Sum('registrar_users'))

    # handle pagination
    registrars = apply_pagination(request, registrars)

    return render(request, 'user_management/manage_registrars.html', {
        'registrars': registrars,
        'orgs_count': orgs_count,
        # 'users_count': users_count,
        'this_page': 'users_registrars',
        'search_query': search_query,
        'status': status,
        'sort': sort,
        'form': form,
    })



@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user())
def manage_single_registrar(request, registrar_id):
    """ Edit details for a registrar. """

    target_registrar = get_object_or_404(Registrar, id=registrar_id)
    if not request.user.can_edit_registrar(target_registrar):
        raise Http404

    form = RegistrarForm(get_form_data(request), prefix = "a", instance=target_registrar)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if request.user.is_staff:
                return HttpResponseRedirect(reverse('user_management_manage_registrar'))
            else:
                return HttpResponseRedirect(reverse('user_management_settings_affiliations'))

    return render(request, 'user_management/manage_single_registrar.html', {
        'target_registrar': target_registrar,
        'this_page': 'users_registrars',
        'form': form
    })

@user_passes_test_or_403(lambda user: user.is_staff)
def approve_pending_registrar(request, registrar_id):
    """ Perma admins can approve account requests from libraries """

    target_registrar = get_object_or_404(Registrar, id=registrar_id)
    target_registrar_user = target_registrar.pending_users.first()

    if request.method == 'POST':

        with transaction.atomic():

            new_status = request.POST.get("status")
            if new_status in ["approved", "denied"]:
                target_registrar.status = new_status
                target_registrar.save()

                if new_status == "approved":
                    target_registrar_user.registrar = target_registrar
                    target_registrar_user.pending_registrar = None
                    target_registrar_user.save()
                    email_approved_registrar_user(request, target_registrar_user)

                    messages.add_message(request, messages.SUCCESS, f'<h4>Registrar approved!</h4> <strong>{target_registrar_user.email}</strong> will receive a notification email with further instructions.', extra_tags='safe')
                else:
                    messages.add_message(request, messages.SUCCESS, f'Registrar request for <strong>{target_registrar}</strong> denied. Please inform {target_registrar_user.email} if appropriate.', extra_tags='safe')

        return HttpResponseRedirect(reverse('user_management_manage_registrar'))

    return render(request, 'user_management/approve_pending_registrar.html', {
        'target_registrar': target_registrar,
        'target_registrar_user': target_registrar_user,
        'this_page': 'users_registrars'})


@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user() or user.is_organization_user)
def manage_organization(request):
    """
    Admin and registrar users can manage organizations (journals)
    """

    is_admin = request.user.is_staff
    if is_admin:
        form = OrganizationWithRegistrarForm(get_form_data(request), prefix = "a")
    else:
        form = OrganizationForm(get_form_data(request), prefix = "a")

    if request.method == 'POST':
        if form.is_valid():
            new_org = form.save(commit=False)
            if not is_admin:
                new_org.registrar_id = request.user.registrar_id
            new_org.save()
            return HttpResponseRedirect(reverse('user_management_manage_organization'))

    orgs = Organization.objects.accessible_to(request.user).select_related('registrar')

    # add annotations
    orgs = orgs.annotate(
        organization_users=Count('users', distinct=True),
        last_active=Max('users__last_login'),
    )

    # handle sorting
    orgs, sort = apply_sort_order(request, orgs, valid_org_sorts)

    # handle search
    orgs, search_query = apply_search_query(request, orgs, ['name', 'registrar__name'])

    # handle registrar filter
    registrar_filter = request.GET.get('registrar', '')
    if registrar_filter:
        orgs = orgs.filter(registrar__id=registrar_filter)
        registrar_filter = Registrar.objects.get(pk=registrar_filter)

    # get total user count
    users_count = orgs.aggregate(count=Sum('organization_users'))['count']

    # handle pagination
    orgs = apply_pagination(request, orgs)

    return render(request, 'user_management/manage_orgs.html', {
        'orgs': orgs,
        'this_page': 'users_orgs',
        'search_query': search_query,

        'users_count': users_count,

        'registrars': Registrar.objects.all().order_by('name'),
        'registrar_filter': registrar_filter,
        'sort': sort,

        'form': form,
    })


@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user() or user.is_organization_user)
def manage_single_organization(request, org_id):
    """ Edit organization details. """
    try:
        target_org = Organization.objects.accessible_to(request.user).get(pk=org_id)
    except Organization.DoesNotExist:
        raise Http404

    if request.user.is_staff:
        form = OrganizationWithRegistrarForm(get_form_data(request), prefix = "a", instance=target_org)
    else:
        form = OrganizationForm(get_form_data(request), prefix = "a", instance=target_org)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('user_management_manage_organization'))

    return render(request, 'user_management/manage_single_organization.html', {
        'target_org': target_org,
        'this_page': 'users_orgs',
        'form': form,
    })


@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user() or user.is_organization_user)
def manage_single_organization_delete(request, org_id):
    """
        Delete an empty org
    """
    try:
        target_org = Organization.objects.accessible_to(request.user).get(pk=org_id)
    except Organization.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        if target_org.links.count() > 0:
            raise Http404

        target_org.safe_delete()
        target_org.save()

        return HttpResponseRedirect(reverse('user_management_manage_organization'))

    return render(request, 'user_management/organization_delete_confirm.html', {
        'target_org': target_org,
        'this_page': 'users_orgs',
    })


@user_passes_test_or_403(lambda user: user.is_staff)
def manage_admin_user(request):
    return list_users_in_group(request, 'admin_user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_admin_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'admin_user')

@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user())
def manage_registrar_user(request):
    return list_users_in_group(request, 'registrar_user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_registrar_user(request, user_id):
    return edit_user_in_group(request, user_id, 'registrar_user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_registrar_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'registrar_user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_registrar_user_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'registrar_user')

@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user())
def manage_sponsored_user(request):
    return list_sponsored_users(request)


@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user())
def manage_sponsored_user_export_user_list(request: HttpRequest) -> HttpResponse | JsonResponse:
    # Get query results via list_sponsored_users
    field_names = [
        'email',
        'first_name',
        'last_name',
        'date_joined',
        'last_login',
        'sponsorship_status',
        'sponsorship_created_at',
    ]
    records = list_sponsored_users(request, export=True)
    users = records.annotate(
        sponsorship_status=F('sponsorships__status'),
        sponsorship_created_at=F('sponsorships__created_at'),
    ).values(*field_names)

    # Export records in appropriate format based on `format` URL parameter
    export_format: Literal['csv', 'json'] = request.GET.get('format', 'csv').casefold()
    match export_format:
        case 'json':
            response = JsonResponse(list(users), safe=False)
        case 'csv' | _:
            response = HttpResponse(
                content_type='text/csv',
                headers={'Content-Disposition': 'attachment; filename="perma-sponsored-users.csv"'},
            )
            writer = csv.DictWriter(response, fieldnames=field_names)
            writer.writeheader()
            for user in users:
                writer.writerow(user)
    return response


@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user())
def manage_single_sponsored_user(request, user_id):
    return edit_user_in_group(request, user_id, 'sponsored_user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_sponsored_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'sponsored_user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_sponsored_user_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'sponsored_user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_user(request):
    return list_users_in_group(request, 'user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_user(request, user_id):
    return edit_user_in_group(request, user_id, 'user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_user_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'user')

@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user() or user.is_organization_user)
def manage_organization_user(request):
    return list_users_in_group(request, 'organization_user')

@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user() or user.is_organization_user)
def manage_single_organization_user(request, user_id):
    return edit_user_in_group(request, user_id, 'organization_user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_organization_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'organization_user')

@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_organization_user_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'organization_user')


@user_passes_test_or_403(
    lambda user: user.is_staff or user.is_registrar_user() or user.is_organization_user
)
def manage_single_organization_export_user_list(
    request: HttpRequest, org_id: int
) -> HttpResponse | JsonResponse:
    """Return a file listing all users belonging to an organization."""
    org_users = (
        LinkUser.objects.filter(organizations__id=org_id)
        .annotate(organization_name=F('organizations__name'))
        .values('email', 'first_name', 'last_name', 'organization_name')
    )
    filename_stem = f'perma-organization-{org_id}-users'

    # Generate output records from query results and add organization name
    field_names = ['email', 'first_name', 'last_name', 'organization_name']

    # Export records in appropriate format based on `format` URL parameter
    export_format: Literal['csv', 'json'] = request.GET.get('format', 'csv').casefold()
    match export_format:
        case 'json':
            response = JsonResponse(list(org_users), safe=False)
        case 'csv' | _:
            response = HttpResponse(
                content_type='text/csv',
                headers={'Content-Disposition': f'attachment; filename="{filename_stem}.csv"'},
            )
            writer = csv.DictWriter(response, fieldnames=field_names)
            writer.writeheader()
            for org_user in org_users:
                writer.writerow(org_user)
    return response


@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user() or user.is_organization_user)
def list_users_in_group(request, group_name):
    """
        Show list of users with given group name.
    """

    users = LinkUser.objects.distinct().prefetch_related('organizations')  # .exclude(id=request.user.id)

    # handle sorting
    users, sort = apply_sort_order(request, users, valid_member_sorts)

    # handle search
    users, search_query = apply_search_query(request, users, ['email', 'first_name', 'last_name', 'organizations__name'])

    registrar_filter = request.GET.get('registrar', '')

    registrars = None
    orgs = None

    # apply permissions limits
    if request.user.is_staff:
        if registrar_filter:
            orgs = Organization.objects.filter(registrar__id=registrar_filter).order_by('name')
        else:
            orgs = Organization.objects.all().order_by('name')
        registrars = Registrar.objects.filter(status__in=['pending', 'approved']).order_by('name')
    elif request.user.is_registrar_user():
        if group_name == 'organization_user':
            users = users.filter(organizations__registrar=request.user.registrar)
            orgs = Organization.objects.filter(registrar_id=request.user.registrar_id).order_by('name')
        elif group_name == 'sponsored_user':
            users = users.filter(sponsoring_registrars=request.user.registrar)
        else:
            users = users.filter(registrar=request.user.registrar)
    elif request.user.is_organization_user:
        users = users.filter(organizations__in=request.user.organizations.all())

    # apply group filter
    if group_name == 'admin_user':
        users = users.exclude(is_staff=False)
    elif group_name == 'registrar_user':
        users = users.exclude(registrar_id=None).prefetch_related('registrar')
    elif group_name == 'sponsored_user':
        users = users.exclude(sponsoring_registrars=None).prefetch_related('sponsoring_registrars', 'sponsorships')
    elif group_name == 'organization_user':
        # careful handling to exclude users associated only with deleted orgs
        users = users.filter(organizations__user_deleted=0)
    else:
        # careful handling to include users associated only with deleted orgs
        users = users.filter(registrar_id=None, is_staff=False).exclude(organizations__user_deleted=0).filter(sponsorships=None)

    # handle status filter
    status = request.GET.get('status', '')
    if status:
        if status == 'active':
            users = users.filter(is_confirmed=True, is_active=True)
        elif status == 'deactivated':
            users = users.filter(is_confirmed=True, is_active=False)
        elif status == 'unactivated':
            users = users.filter(is_confirmed=False, is_active=False)

    # handle upgrade filter
    upgrade = request.GET.get('upgrade', '')
    if upgrade:
        users = users.filter(requested_account_type=upgrade)

    # handle org filter
    org_filter = request.GET.get('org', '')
    if org_filter:
        users = users.filter(organizations__id=org_filter)
        org_filter = Organization.objects.get(pk=org_filter)

    # handle registrar filter
    if registrar_filter:
        if group_name == 'organization_user':
            users = users.filter(organizations__registrar_id=registrar_filter)
        elif group_name == 'sponsored_user':
            users = users.filter(sponsoring_registrars__id=registrar_filter)
        elif group_name == 'registrar_user':
            users = users.filter(registrar_id=registrar_filter)
        registrar_filter = Registrar.objects.get(pk=registrar_filter)

    # handle sponsorship status filter:
    sponsorship_status = request.GET.get('sponsorship_status', '')
    if sponsorship_status:
        users = users.filter(sponsorships__status=sponsorship_status)

    # get total counts
    active_users = users.filter(is_active=True, is_confirmed=True).count()
    deactivated_users = users.filter(is_confirmed=True, is_active=False).count()
    # work-around for https://github.com/harvard-lil/perma/issues/3276: use math to get the number
    # of unactivated users instead of running the expensive SQL query generated by the ORM
    unactivated_users = users.count() - active_users - deactivated_users

    total_created_links_count = users.aggregate(count=Sum('link_count'))['count']

    # handle pagination
    users = apply_pagination(request, users)

    context = {
        'this_page': f'users_{group_name}s',
        'users': users,
        'active_users': active_users,
        'deactivated_users': deactivated_users if request.user.is_staff else None,  # only expose to staff, for unknown historical reasons
        'unactivated_users': unactivated_users,
        'orgs': orgs,
        'total_created_links_count': total_created_links_count,
        'registrars': registrars,
        'group_name':group_name,
        'pretty_group_name':group_name.replace('_', ' ').capitalize(),
        'user_list_url':f'user_management_manage_{group_name}',
        'reactivate_user_url':f'user_management_manage_single_{group_name}_reactivate',
        'single_user_url':f'user_management_manage_single_{group_name}',
        'delete_user_url':f'user_management_manage_single_{group_name}_delete',
        'add_user_url':f'user_management_{group_name}_add_user',

        'sort': sort,
        'search_query': search_query,
        'registrar_filter': registrar_filter,
        'org_filter': org_filter,
        'status': status,
        'upgrade': upgrade,
        'sponsorship_status': sponsorship_status
    }
    context['pretty_group_name_plural'] = context['pretty_group_name'] + "s"

    return render(request, 'user_management/manage_users.html', context)


@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user())
def list_sponsored_users(
    request: HttpRequest, group_name: str = 'sponsored_user', export: bool = False
) -> HttpResponse | BaseManager[LinkUser]:
    """
    Show list of sponsored users. Adapted from `list_users_in_group` for improved performance.

    If `export` is enabled, returns a query manager for exporting user records.
    """
    from perma.models import Sponsorship

    registrars = None
    registrar_filter = request.GET.get('registrar', '')
    if request.user.is_registrar_user():
        sponsorships = Sponsorship.objects.filter(registrar=request.user.registrar)
    else:
        sponsorships = Sponsorship.objects.all()
        registrars = Registrar.objects.exclude(sponsorships=None).order_by('name')

        # handle registrar filter
        if registrar_filter:
            sponsorships = sponsorships.filter(registrar_id=registrar_filter)
            registrar_filter = Registrar.objects.get(pk=registrar_filter)

    # handle sponsorship status filter:
    sponsorship_status = request.GET.get('sponsorship_status', '')
    if sponsorship_status:
        sponsorships = sponsorships.filter(status=sponsorship_status)

    sponsorship_ids = sponsorships.values_list('id', flat=True)
    users = LinkUser.objects.distinct().filter(sponsorships__in=sponsorship_ids).prefetch_related('sponsorships', 'sponsorships__registrar')

    # handle user status filter
    status = request.GET.get('status', '')
    if status:
        if status == 'active':
            users = users.filter(is_confirmed=True, is_active=True)
        elif status == 'deactivated':
            users = users.filter(is_confirmed=True, is_active=False)
        elif status == 'unactivated':
            users = users.filter(is_confirmed=False, is_active=False)

    # handle sorting
    users, sort = apply_sort_order(request, users, valid_member_sorts)

    # handle search
    users, search_query = apply_search_query(request, users, ['email', 'first_name', 'last_name'])

    # if exporting records (e.g. for CSV or JSON output), return query manager directly
    if export is True:
        return users

    # get total counts
    active_users = users.filter(is_active=True, is_confirmed=True).count()
    deactivated_users = users.filter(is_confirmed=True, is_active=False).count()
    unactivated_users = users.count() - active_users - deactivated_users

    total_created_links_count = users.aggregate(count=Sum('link_count'))['count']

    # handle pagination
    users = apply_pagination(request, users)

    context = {
        'this_page': f'users_{group_name}s',
        'users': users,
        'active_users': active_users,
        'deactivated_users': deactivated_users if request.user.is_staff else None,  # only expose to staff, for unknown historical reasons
        'unactivated_users': unactivated_users,
        'total_created_links_count': total_created_links_count,
        'registrars': registrars,
        'group_name':group_name,
        'pretty_group_name':group_name.replace('_', ' ').capitalize(),
        'user_list_url':f'user_management_manage_{group_name}',
        'reactivate_user_url':f'user_management_manage_single_{group_name}_reactivate',
        'single_user_url':f'user_management_manage_single_{group_name}',
        'delete_user_url':f'user_management_manage_single_{group_name}_delete',
        'add_user_url':f'user_management_{group_name}_add_user',

        'sort': sort,
        'search_query': search_query,
        'registrar_filter': registrar_filter,
        'status': status,
        'sponsorship_status': sponsorship_status
    }
    context['pretty_group_name_plural'] = context['pretty_group_name'] + "s"

    return render(request, 'user_management/manage_users.html', context)


def edit_user_in_group(request, user_id, group_name):
    """
        Edit particular user with given group name.
    """

    target_user = get_object_or_404(LinkUser, id=user_id)

    if request.user.is_registrar_user():
        # registrar users can edit their sponsored users,
        # and users who belong to any of their registrar's organizations
        sponsorships = target_user.sponsorships.filter(registrar=request.user.registrar)
        orgs = target_user.organizations.all() & Organization.objects.filter(registrar=request.user.registrar)

        if not sponsorships and len(orgs) == 0:
            raise Http404

    elif request.user.is_organization_user:
        # org users can only edit their members in the same orgs
        sponsorships = None
        orgs = target_user.organizations.all() & request.user.organizations.all()

        if len(orgs) == 0:
            raise Http404

    else:
        # Must be admin user
        sponsorships = target_user.sponsorships.all().order_by('status', 'registrar__name')
        orgs = target_user.organizations.all()

    context = {
        'target_user': target_user, 'group_name':group_name,
        'this_page': f'users_{group_name}s',
        'pretty_group_name':group_name.replace('_', ' ').capitalize(),
        'user_list_url':f'user_management_manage_{group_name}',
        'delete_user_url':f'user_management_manage_single_{group_name}_delete',
        'sponsorships':sponsorships,
        'orgs': orgs,
    }

    return render(request, 'user_management/manage_single_user.html', context)


### ADD USER TO GROUP ###

class BaseAddUserToGroup(UpdateView):
    """
        Base class for views that take an email address and either add a new user, or add the user to
        a given group if they already exist.
    """

    def __init__(self, **kwargs):
        super(BaseAddUserToGroup, self).__init__(**kwargs)
        self.extra_context = {}

    def dispatch(self, request, *args, **kwargs):
        """ Before handling a post or get request, make sure that the target user is allowed to be added to the given group. """
        self.object = self.get_object()
        self.is_new = self.object is None
        valid, error_message = self.target_user_valid()
        if not valid:
            self.extra_context['error_message'] = error_message
            return self.form_invalid(None)
        return super(BaseAddUserToGroup, self).dispatch(request, *args, **kwargs)

    def get_form_class(self):
        """ Choose form based on whether target user already exists. """
        return self.new_user_form if self.is_new else self.existing_user_form

    def get_form_kwargs(self):
        """ Add form prefix. (TODO: stop adding form prefixes.) """
        return dict(
            super(BaseAddUserToGroup, self).get_form_kwargs(),
            prefix="a")

    def get_object(self, queryset=None):
        """ Fetch the target user based on the email address in the ?email= get param. """
        if getattr(self, 'object', None):
            return self.object
        user_email = self.request.GET.get('email')
        if user_email:
            return LinkUser.objects.filter(email=user_email.lower()).first()

    def get_initial(self):
        """ Populate form with supplied email address. """
        return dict(
            super(BaseAddUserToGroup, self).get_initial(),
            email=self.request.GET.get('email'))

    def get_context_data(self, **kwargs):
        """ Populate template context with supplied email address. """
        return dict(
            super(BaseAddUserToGroup, self).get_context_data(**kwargs),
            user_email=self.request.GET.get('email'),
            **self.extra_context)

    def form_valid(self, form):
        """ If form is submitted successfully, show success message and send email to target user. """
        response = super(BaseAddUserToGroup, self).form_valid(form)
        if self.is_new:
            email_new_user(
                self.request,
                self.object,
                self.user_added_email_template,
                { 'form': form }
            )
            messages.add_message(self.request, messages.SUCCESS,
                                 f'<h4>Account created!</h4> <strong>{self.object.email}</strong> will receive an email with instructions on how to activate the account and create a password.',
                                 extra_tags='safe')
        else:
            send_user_email(
                self.object.raw_email,
                self.confirmation_email_template,
                { 'account_settings_page': f"https://{self.request.get_host()}{reverse('user_management_settings_profile')}",
                  'form': form }
            )
            messages.add_message(self.request, messages.SUCCESS,
                                 f'<h4>Success!</h4> <strong>{self.object.email}</strong> added.',
                                 extra_tags='safe')

        return response


class AddUserToOrganization(RequireOrgOrRegOrAdminUser, BaseAddUserToGroup):
    template_name = 'user_management/user_add_to_organization_confirm.html'
    success_url = reverse_lazy('user_management_manage_organization_user')
    confirmation_email_template = 'email/user_added_to_organization.txt'
    user_added_email_template = 'email/new_user_added_to_org_by_other.txt'
    new_user_form = UserFormWithOrganization
    existing_user_form = UserAddOrganizationForm

    def get_form_kwargs(self):
        """ Filter organizations to those current user can access. """
        return dict(
            super(AddUserToOrganization, self).get_form_kwargs(),
            current_user=self.request.user)

    def target_user_valid(self):
        """ User can only be added to org if they aren't admin or registrar. """
        if self.is_new:
            return True, ""
        if self.object.is_staff:
            return False, f"{self.object} is an admin user and cannot be added to individual organizations."
        if self.object.is_registrar_user():
            return False, f"{self.object} is already a registrar user and cannot be added to individual organizations."
        return True, ""


class AddUserToRegistrar(RequireRegOrAdminUser, BaseAddUserToGroup):
    template_name = 'user_management/user_add_to_registrar_confirm.html'
    success_url = reverse_lazy('user_management_manage_registrar_user')
    confirmation_email_template = 'email/user_added_to_registrar.txt'
    user_added_email_template = 'email/new_user_added_to_registrar_by_other.txt'
    new_user_form = UserFormWithRegistrar
    existing_user_form = UserAddRegistrarForm

    def get_form_kwargs(self):
        """ Filter registrars to those current user can access. """
        return dict(
            super(AddUserToRegistrar, self).get_form_kwargs(),
            current_user=self.request.user)

    def target_user_valid(self):
        """ User can only be added to registrar if they aren't admin or registrar or org user. """
        if self.is_new:
            return True, ""
        if self.object.is_staff:
            return False, f"{self.object} is an admin user and cannot be added to individual registrars."

        # limits that apply just if the current user is a registrar rather than staff
        if self.request.user.is_registrar_user():
            if self.object.is_registrar_user():
                if self.object.registrar == self.request.user.registrar:
                    return False, f"{self.object} is already a registrar user for your registrar."
                else:
                    return False, f"{self.object} is already a member of another registrar and cannot be added to your registrar."
            if self.object.organizations.exclude(registrar=self.request.user.registrar).exists():
                return False, f"{self.object} belongs to organizations that are not controlled by your registrar. You cannot make them a registrar unless they leave those organizations."
        return True, ""


class AddSponsoredUserToRegistrar(RequireRegOrAdminUser, BaseAddUserToGroup):
    template_name = 'user_management/user_add_to_sponsoring_registrar_confirm.html'
    success_url = reverse_lazy('user_management_manage_sponsored_user')
    confirmation_email_template = 'email/user_added_to_sponsoring_registrar.txt'
    user_added_email_template = 'email/new_user_added_to_sponsoring_registrar_by_other.txt'
    new_user_form = UserFormWithSponsoringRegistrar
    existing_user_form = UserAddSponsoringRegistrarForm

    def get_form_kwargs(self):
        """ Filter registrars to those current user can access. """
        return dict(
            super(AddSponsoredUserToRegistrar, self).get_form_kwargs(),
            current_user=self.request.user)

    def target_user_valid(self):
        """ User can only be added to registrar if they aren't already sponsored by the registrar. """
        if self.is_new:
            return True, ""

        if self.request.user.is_registrar_user():
            if self.request.user.registrar in self.object.sponsoring_registrars.all():
                return False, f"{self.object} is already sponsored by your registrar."
        return True, ""


class AddUserToAdmin(RequireAdminUser, BaseAddUserToGroup):
    template_name = 'user_management/user_add_to_admin_confirm.html'
    success_url = reverse_lazy('user_management_manage_admin_user')
    confirmation_email_template = 'email/user_added_to_admin.txt'
    user_added_email_template = 'email/new_user_added_by_other.txt'
    new_user_form = UserFormWithAdmin
    existing_user_form = UserAddAdminForm

    def target_user_valid(self):
        """ Any user can be made into an admin. """
        return True, ""


class AddRegularUser(RequireAdminUser, BaseAddUserToGroup):
    template_name = 'user_management/user_add_confirm.html'
    success_url = reverse_lazy('user_management_manage_user')
    user_added_email_template = 'email/new_user_added_by_other.txt'
    new_user_form = UserForm
    existing_user_form = UserForm

    def target_user_valid(self):
        """ Existing users cannot be added as regular users. """
        return self.is_new, "User already exists."


@user_passes_test_or_403(lambda user: user.is_organization_user)
def organization_user_leave_organization(request, org_id):
    try:
        org = Organization.objects.accessible_to(request.user).get(pk=org_id)
    except Organization.DoesNotExist:
        raise Http404

    context = {'this_page': 'settings', 'user': request.user, 'org': org}

    if request.method == 'POST':
        request.user.organizations.remove(org)
        request.user.save()

        messages.add_message(request, messages.SUCCESS, f'<h4>Success.</h4> You are no longer a member of <strong>{org.name}</strong>.', extra_tags='safe')

        if request.user.organizations.exists():
            return HttpResponseRedirect(reverse('user_management_settings_affiliations'))
        else:
            return HttpResponseRedirect(reverse('create_link'))

    return render(request, 'user_management/user_leave_confirm.html', context)


@user_passes_test_or_403(lambda user: user.is_staff)
def delete_user_in_group(request, user_id, group_name):
    """
        Delete particular user with given group name.
    """

    target_user = get_object_or_404(LinkUser, id=user_id)

    context = {'target_user': target_user,
               'action': 'deactivate' if target_user.is_confirmed else 'delete',
               'this_page': f'users_{group_name}s'}

    if request.method == 'POST':
        if target_user.is_confirmed:
            target_user.is_active = False
            target_user.organizations.clear()
            target_user.registrar = None
            target_user.save()
        else:
            target_user.delete()

        return HttpResponseRedirect(reverse(f'user_management_manage_{group_name}'))

    return render(request, 'user_management/user_delete_confirm.html', context)


@user_passes_test_or_403(lambda user: user.is_registrar_user() or user.is_organization_user or user.is_staff)
def manage_single_organization_user_remove(request, user_id):
    """
        Remove an organization user from an org.
    """

    if request.method == 'POST':
        try:
            org = Organization.objects.accessible_to(request.user).get(pk=request.POST.get('org'))
        except Organization.DoesNotExist:
            raise Http404

        target_user = get_object_or_404(LinkUser, id=user_id)
        target_user.organizations.remove(org)

        # special case -- user demoted themselves, can't see page anymore
        if request.user == target_user and not target_user.organizations.exists():
            return HttpResponseRedirect(reverse('create_link'))

    return HttpResponseRedirect(reverse('user_management_manage_organization_user'))


@user_passes_test_or_403(lambda user: user.is_registrar_user())
def manage_single_registrar_user_remove(request, user_id):
    """
        Remove a registrar user from a registrar.
    """

    target_user = get_object_or_404(LinkUser, id=user_id)

    # Registrar users can only edit their own registrar users
    if request.user.registrar_id != target_user.registrar_id:
        raise Http404

    context = {'target_user': target_user,
               'this_page': 'organization_user'}

    if request.method == 'POST':
        target_user.registrar = None
        target_user.save()

        # special case -- user demoted themselves, can't see page anymore
        if request.user == target_user:
            return HttpResponseRedirect(reverse('create_link'))

        return HttpResponseRedirect(reverse('user_management_manage_registrar_user'))

    return render(request, 'user_management/user_remove_registrar_confirm.html', context)


def toggle_status(request, user_id, registrar_id, status):
    target_user = get_object_or_404(LinkUser, id=user_id)
    registrar =  get_object_or_404(Registrar, id=registrar_id)
    sponsorship = get_object_or_404(Sponsorship, user=target_user, registrar=registrar)

    # Registrar users can only edit their own sponsored users,
    # and can only deactivate their own sponsorships
    if request.user.is_registrar_user() and \
        (request.user.registrar not in target_user.sponsoring_registrars.all() or
         str(request.user.registrar_id) != registrar_id):
        raise Http404

    if request.method == 'POST':
        sponsorship.status = status
        sponsorship.save()
        return HttpResponseRedirect(reverse('user_management_manage_single_sponsored_user', args=[user_id]))

    return render(request, f"user_management/user_{'readd' if status == 'active' else 'remove'}_sponsored_confirm.html", {'target_user': target_user, 'registrar': registrar})


@user_passes_test_or_403(lambda user: user.is_registrar_user() or user.is_staff)
def manage_single_sponsored_user_remove(request, user_id, registrar_id):
    """
        Deactivate an active sponsorship for a user
    """
    return toggle_status(request, user_id, registrar_id, 'inactive')


@user_passes_test_or_403(lambda user: user.is_registrar_user() or user.is_staff)
def manage_single_sponsored_user_readd(request, user_id, registrar_id):
    """
        Reactivate an inactive sponsorship for a user
    """
    return toggle_status(request, user_id, registrar_id, 'active')


@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user())
def manage_single_sponsored_user_links(request, user_id, registrar_id):
    target_user = get_object_or_404(LinkUser, id=user_id)
    registrar =  get_object_or_404(Registrar, id=registrar_id)

    # Registrar users can only see links belonging to their own sponsorships
    if request.user.is_registrar_user() and \
        (request.user.registrar not in target_user.sponsoring_registrars.all() or
         str(request.user.registrar_id) != registrar_id):
        raise Http404

    folders = Folder.objects.filter(owned_by=target_user, sponsored_by=registrar)
    links = Link.objects.filter(folders__in=folders).select_related('capture_job').prefetch_related('captures').order_by('-creation_timestamp')
    links = apply_pagination(request, links)

    return render(request, 'user_management/manage_single_user_links.html', {
        'this_page': 'users_sponsored_users',
        'target_user': target_user,
        'registrar': registrar,
        'links': links
    })


@user_passes_test_or_403(lambda user: user.is_staff)
def manage_single_admin_user_remove(request, user_id):
    """
        Basically demote a admin to a regular user.
    """

    target_user = get_object_or_404(LinkUser, id=user_id)

    context = {'target_user': target_user,
               'this_page': 'users_admin_user'}

    if request.method == 'POST':
        target_user.is_staff = False
        target_user.save()

        # special case -- user demoted themselves, can't see page anymore
        if request.user == target_user:
            return HttpResponseRedirect(reverse('create_link'))

        return HttpResponseRedirect(reverse('user_management_manage_admin_user'))

    return render(request, 'user_management/user_remove_admin_confirm.html', context)


@user_passes_test_or_403(lambda user: user.is_staff)
def reactive_user_in_group(request, user_id, group_name):
    """
        Reactivate particular user with given group name.
    """

    target_user = get_object_or_404(LinkUser, id=user_id)

    context = {'target_user': target_user,
               'this_page': f'users_{group_name}s'}

    if request.method == 'POST':
        target_user.is_active = True
        target_user.save()

        return HttpResponseRedirect(reverse(f'user_management_manage_{group_name}'))

    return render(request, 'user_management/user_reactivate_confirm.html', context)


@login_required
def settings_profile(request):
    """
    Settings profile, change name, change email, ...
    """
    if request.method == 'GET':
        # We want the user to see their raw email address
        request.user.email = request.user.raw_email

    form = UserUpdateProfileForm(get_form_data(request), prefix = "a", instance=request.user)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Profile saved!', extra_tags='safe')
            return HttpResponseRedirect(reverse('user_management_settings_profile'))

    return render(request, 'user_management/settings-profile.html', {
        'this_page': 'settings_profile',
        'form': form,
    })


@login_required
def delete_account(request):
    """
    Generate or regenerate an API key for the user
    """
    if request.method == "POST":
        request.user.notes = f"Requested account deletion {timezone.now()}\n" + request.user.notes
        request.user.save()
        email_deletion_request(request)
    return HttpResponseRedirect(reverse('user_management_settings_profile'))


@login_required
def settings_password(request):
    """
    Settings change password ...
    """
    form = PasswordChangeForm(get_form_data(request))
    context = {
        'this_page': 'settings_password',
        'form': form,
    }
    return render(request, 'user_management/settings-password.html', context)


@user_passes_test_or_403(lambda user: user.is_registrar_user() or user.is_organization_user or user.has_registrar_pending())
def settings_affiliations(request):
    """
    Settings view organizations, leave organizations ...
    """

    pending_registrar = request.user.pending_registrar
    if pending_registrar:
        messages.add_message(request, messages.INFO, "Thank you for requesting an account for your library. Perma.cc will review your request as soon as possible.")

    organizations = request.user.organizations.all().order_by('registrar')
    orgs_by_registrar = {registrar : [org for org in orgs] for registrar, orgs in itertools.groupby(organizations, lambda x: x.registrar)}

    return render(request, 'user_management/settings-affiliations.html', {
        'this_page': 'settings_affiliations',
        'pending_registrar': pending_registrar,
        'orgs_by_registrar': orgs_by_registrar})


@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user() or user.is_organization_user)
def settings_organizations_change_privacy(request, org_id):
    try:
        org = Organization.objects.accessible_to(request.user).get(pk=org_id)
    except Organization.DoesNotExist:
        raise Http404
    context = {'this_page': 'settings', 'user': request.user, 'org': org}

    if request.method == 'POST':
        org.default_to_private = not org.default_to_private
        org.save()

        if request.user.is_registrar_user() or request.user.is_staff:
            return HttpResponseRedirect(reverse('user_management_manage_organization'))
        else:
            return HttpResponseRedirect(reverse('user_management_settings_affiliations'))

    return render(request, 'user_management/settings-organizations-change-privacy.html', context)


@login_required
def settings_tools(request):
    """
    Settings tools ...
    """
    return render(request, 'user_management/settings-tools.html', {'this_page': 'settings_tools'})


@sensitive_variables()
@user_passes_test_or_403(lambda user: user.can_view_usage_plan())
def settings_usage_plan(request):
    accounts = []
    purchase_history = {}
    try:
        if request.user.is_registrar_user() and not request.user.registrar.nonpaying:
            accounts.append(request.user.registrar.get_subscription_info(timezone.now()))
        if not request.user.nonpaying:
            accounts.append(request.user.get_subscription_info(timezone.now()))
            purchase_history = request.user.get_purchase_history()
    except PermaPaymentsCommunicationException:
        context = {
            'this_page': 'settings_usage_plan',
        }
        return render(request, 'user_management/settings-usage-plan-unavailable.html', context)

    context = {
        'this_page': 'settings_usage_plan',
        'purchase_url': settings.PURCHASE_URL,
        'subscribe_url': settings.SUBSCRIBE_URL,
        'cancel_confirm_url': reverse('user_management_settings_subscription_cancel'),
        'update_url': reverse('user_management_settings_subscription_update'),
        'accounts': accounts,
        'purchase_history': purchase_history,
        'bonus_packages': request.user.get_bonus_packages()

    }
    return render(request, 'user_management/settings-usage-plan.html', context)


@sensitive_variables()
@require_http_methods(["POST"])
@user_passes_test_or_403(lambda user: user.can_view_usage_plan())
def settings_subscription_cancel(request):
    account_type = request.POST.get('account_type', '')
    if account_type == 'Registrar':
        customer = request.user.registrar
    elif account_type == 'Individual':
        customer = request.user
    account = customer.get_subscription_info(timezone.now())
    if not account['subscription']:
        return HttpResponseForbidden()
    context = {
        'this_page': 'settings_subscription',
        'cancel_url': settings.CANCEL_URL,
        'customer': customer,
        'customer_type': account_type,
        'account': account,
        'data': prep_for_perma_payments({
            'customer_pk': customer.id,
            'customer_type': account_type,
            'timestamp': timezone.now().timestamp()
        }).decode('utf-8')
    }
    return render(request, 'user_management/settings-subscription-cancel-confirm.html', context)


@sensitive_variables()
@require_http_methods(["POST"])
@user_passes_test_or_403(lambda user: user.can_view_usage_plan())
def settings_subscription_update(request):
    account_type = request.POST.get('account_type', '')
    if account_type == 'Registrar':
        customer = request.user.registrar
    elif account_type == 'Individual':
        customer = request.user
    account = customer.get_subscription_info(timezone.now())
    if not account['subscription']:
        return HttpResponseForbidden()
    context = {
        'this_page': 'settings_subscription',
        'update_url': settings.UPDATE_URL,
        'change_url': settings.CHANGE_URL,
        'customer': customer,
        'customer_type': account_type,
        'account': account,
        'update_encrypted_data': prep_for_perma_payments({
            'customer_pk': customer.id,
            'customer_type': account_type,
            'timestamp': timezone.now().timestamp()
        }).decode('utf-8')
    }
    return render(request, 'user_management/settings-subscription-update.html', context)


@login_required
def api_key_create(request):
    """
    Generate or regenerate an API key for the user
    """

    if request.method == "POST":
        try:
            # Clear key so a new one is generated on save()
            request.user.api_key.key = None
            request.user.api_key.save()
        except ApiKey.DoesNotExist:
            ApiKey.objects.create(user=request.user)
        return HttpResponseRedirect(reverse('user_management_settings_tools'))


def not_active(request):
    """
    Informing a user that their account is not active.
    """
    email = request.session.get('email','')
    if request.method == 'POST':
        target_user = get_object_or_404(LinkUser, email=email)
        email_new_user(request, target_user)

        messages.add_message(request, messages.INFO, 'Check your email for activation instructions.')
        return HttpResponseRedirect(reverse('user_management_limited_login'))
    else:
        context = {}
        context.update(csrf(request))
        return render(request, 'registration/not_active.html', context)


@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user() or user.is_organization_user)
def resend_activation(request, user_id):
    """
    Sends a user another account activation email.
    """
    target_user = get_object_or_404(LinkUser, id=user_id)
    if not request.user.shares_scope_with_user(target_user):
        raise PermissionDenied
    email_new_user(request, target_user)
    return render(request, 'user_management/activation-email.html', {"email": target_user.email})


def account_is_deactivated(request):
    """
    Informing a user that their account has been deactivated.
    """
    return render(request, 'user_management/deactivated.html')


def get_sitewide_cookie_domain(request):
    return '.' + request.get_host().split(':')[0]  # remove port


def logout(request):
    if request.method == 'POST':
        return auth_views.LogoutView.as_view(template_name='registration/logout_success.html')(request)
    return render(request, "registration/logout.html")


@ratelimit(rate=settings.LOGIN_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
@sensitive_post_parameters()
@never_cache
def limited_login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          extra_context=None):
    """
    Displays the login form and handles the login action.

    We wrap the default Django view to add some custom redirects for different user statuses.
    """

    if request.method == "POST" and not request.user.is_authenticated:
        username = request.POST.get('username', '').lower()
        try:
            target_user = LinkUser.objects.get(email=username)
        except LinkUser.DoesNotExist:
            target_user = None
        if target_user:
            if not target_user.is_confirmed:
                request.session['email'] = target_user.email
                return HttpResponseRedirect(reverse('user_management_not_active'))
            if not target_user.is_active:
                return HttpResponseRedirect(reverse('user_management_account_is_deactivated'))

    class LoginForm(authentication_form):
        def __init__(self, *args, **kwargs):
            super(LoginForm, self).__init__(*args, **kwargs)
            self.fields['username'].widget.attrs['autofocus'] = ''

        def clean_username(self):
            return self.cleaned_data.get('username', '').lower()


    return auth_views.LoginView.as_view(template_name=template_name, redirect_field_name=redirect_field_name, authentication_form=LoginForm, extra_context=extra_context, redirect_authenticated_user=True)(request)


def reset_password(request):
    """
        Displays the reset password form.

        We wrap the default Django view to add autofocus to the email field,
        to handle the logic for unconfirmed users activating their account,
        and a custom redirect if deactivated users try to reset their password.
    """
    class OurPasswordResetForm(PasswordResetForm):
        def __init__(self, *args, **kwargs):
            super(PasswordResetForm, self).__init__(*args, **kwargs)
            self.fields['email'].widget.attrs['autofocus'] = ''

        def clean_username(self):
            return self.cleaned_data.get('username', '').lower()

    if request.method == "POST":
        try:
            target_user = LinkUser.objects.get(email=request.POST.get('email', '').lower())
        except LinkUser.DoesNotExist:
            target_user = None
        if target_user:
            if not target_user.is_confirmed:
                # This is a weird area... We're doing this, for now, to help
                # smooth things for the users who sign up while we are transitioning
                # to new activation links. We think it will be less confusing for them
                # to receive a "password reset" email, since we ARE asking them to fill
                # our that form, rather than a welcome email. We can readdress later...
                # this whole architecture needs some tidying.
                email_new_user(request, target_user, template="email/unactivated_user_reset_email.txt")
            if target_user.is_confirmed and not target_user.is_active:
                return HttpResponseRedirect(reverse('user_management_account_is_deactivated'))

    return auth_views.PasswordResetView.as_view(form_class=OurPasswordResetForm)(request)

def redirect_to_reset(request, token):
    """
        Perma used to use custom account-activation logic; now we reuse the reset password flow.
        Redirect users following the old-style activation links to a page where they can
        request a new-style activation link.
    """
    return HttpResponseRedirect(reverse('password_reset_confirm', args=['0', token]))


@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def libraries(request):
    """
    Info for libraries, allow them to request accounts
    """
    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'register_library_instructions', 'a-telephone', check_js=True):
            return something_took_the_bait

        registrar_form = LibraryRegistrarForm(request.POST, request.FILES, prefix ="b")
        if request.user.is_authenticated:
            user_form = None
        else:
            user_form = UserForm(request.POST, prefix = "a")
            user_form.fields['email'].label = "Your email"
        user_email = request.POST.get('a-e-address', '').lower()
        try:
            target_user = LinkUser.objects.get(email=user_email)
        except LinkUser.DoesNotExist:
            target_user = None
        if target_user:
            messages.add_message(request, messages.INFO, "You already have a Perma account, please sign in to request an account for your library.")
            request.session['request_data'] = registrar_form.data
            return HttpResponseRedirect('/login?next=/libraries/')

        # test if both form objects that comprise the signup form are valid
        if user_form:
            form_is_valid = user_form.is_valid() and registrar_form.is_valid()
        else:
            form_is_valid = registrar_form.is_valid()
        if form_is_valid:
            new_registrar = registrar_form.save()
            email_registrar_request(request, new_registrar)
            if user_form:
                new_user = user_form.save(commit=False)
                new_user.pending_registrar = new_registrar
                new_user.save()
                email_pending_registrar_user(request, new_user)
                return HttpResponseRedirect(reverse('register_library_instructions'))
            else:
                request.user.pending_registrar = new_registrar
                request.user.save()
                return HttpResponseRedirect(reverse('user_management_settings_affiliations'))
    else:
        request_data = request.session.get('request_data','')
        user_form = None
        if not request.user.is_authenticated:
            user_form = UserForm(prefix="a")
            user_form.fields['email'].label = "Your email"
        if request_data:
            registrar_form = LibraryRegistrarForm(request_data, prefix="b")
        else:
            registrar_form = LibraryRegistrarForm(prefix="b")

    return render(request, "registration/sign-up-libraries.html",
        {'user_form':user_form, 'registrar_form':registrar_form})

@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up(request):
    """
    Register a new user
    """
    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'register_email_instructions', check_js=True):
            return something_took_the_bait

        form = UserForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            email_new_user(request, new_user)
            return HttpResponseRedirect(reverse('register_email_instructions'))
    else:
        form = UserForm()

    return render(request, "registration/sign-up.html", {'form': form})


@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_courts(request):
    """
    Register a new court user
    """
    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'register_email_instructions', check_js=True):
            return something_took_the_bait

        form = CreateUserFormWithCourt(request.POST)
        submitted_email = request.POST.get('e-address', '').lower()

        try:
            target_user = LinkUser.objects.get(email=submitted_email)
        except LinkUser.DoesNotExist:
            target_user = None

        if target_user:
            requested_account_note = request.POST.get('requested_account_note', None)
            target_user.requested_account_type = 'court'
            target_user.requested_account_note = requested_account_note
            target_user.save()
            email_court_request(request, target_user)
            return HttpResponseRedirect(reverse('court_request_response'))

        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.requested_account_type = 'court'
            create_account = request.POST.get('create_account', None)
            if create_account:
                new_user.save()
                email_new_user(request, new_user)
                email_court_request(request, new_user)
                messages.add_message(request, messages.INFO, "We will shortly follow up with more information about how Perma.cc could work in your court.")
                return HttpResponseRedirect(reverse('register_email_instructions'))
            else:
                email_court_request(request, new_user)
                return HttpResponseRedirect(reverse('court_request_response'))

    else:
        form = CreateUserFormWithCourt()

    return render(request, "registration/sign-up-courts.html", {'form': form})


@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_faculty(request):
    """
    Register a new user
    """
    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'register_email_instructions', check_js=True):
            return something_took_the_bait

        form = CreateUserFormWithUniversity(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.requested_account_type = 'faculty'
            new_user.save()

            email_new_user(request, new_user)

            messages.add_message(request, messages.INFO, "Remember to ask your library about access to special Perma.cc privileges.")
            return HttpResponseRedirect(reverse('register_email_instructions'))
    else:
        form = CreateUserFormWithUniversity()

    return render(request, "registration/sign-up-faculty.html", {'form': form})

@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_firm(request):
    """
    Register a new law firm user
    """
    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'register_email_instructions', check_js=True):
            return something_took_the_bait

        user_form = CreateUserFormWithFirm(request.POST)
        user_email = request.POST.get('e-address', '').lower()

        try:
            existing_user = LinkUser.objects.get(email=user_email)
        except LinkUser.DoesNotExist:
            existing_user = None

        # If user email in form matches an existing user in database, update user record to include
        # organization name under `LinkUser.requested_account_note` field
        if existing_user is not None:
            organization_name = request.POST.get('name', None)
            existing_user.requested_account_type = 'firm'
            existing_user.requested_account_note = organization_name
            existing_user.save()
            email_firm_request(request, existing_user)
            return HttpResponseRedirect(reverse('firm_request_response'))

        # Otherwise, validate the user form, create a new user account (if requested), and email a
        # firm request to Perma administrators
        elif user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.requested_account_type = 'firm'
            create_account = request.POST.get('create_account', None)
            if create_account:
                new_user.save()
                email_new_user(request, new_user)
                email_firm_request(request, new_user)
                messages.add_message(
                    request,
                    messages.INFO,
                    'We will shortly follow up with more information about how Perma.cc could work in your organization.',
                )
                return HttpResponseRedirect(reverse('register_email_instructions'))
            else:
                email_firm_request(request, new_user)
                return HttpResponseRedirect(reverse('firm_request_response'))

    else:
        user_form = CreateUserFormWithFirm()
        organization_form = FirmOrganizationForm()
        usage_form = FirmUsageForm()

    return render(
        request,
        'registration/sign-up-firms.html',
        {
            'user_form': user_form,
            'organization_form': organization_form,
            'usage_form': usage_form,
        },
    )


@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_journals(request):
    """
    Register a new user
    """
    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'register_email_instructions', check_js=True):
            return something_took_the_bait

        form = CreateUserFormWithUniversity(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.requested_account_type = 'journal'
            new_user.save()

            email_new_user(request, new_user)

            messages.add_message(request, messages.INFO, "Remember to ask your library about access to special Perma.cc privileges.")
            return HttpResponseRedirect(reverse('register_email_instructions'))
    else:
        form = CreateUserFormWithUniversity()

    return render(request, "registration/sign-up-journals.html", {'form': form})

def register_email_instructions(request):
    """
    After the user has registered, give the instructions for confirming
    """
    return render(request, 'registration/check_email.html')


def register_library_instructions(request):
    """
    After the user requested a library account, give instructions
    """
    return render(request, 'registration/check_email_library.html')


def court_request_response(request):
    """
    After the user has requested info about a court account
    """
    return render(request, 'registration/court_request.html')

def firm_request_response(request):
    """
    After the user has requested info about a firm account
    """
    return render(request, 'registration/firm_request.html')


def email_new_user(request, user, template="email/new_user.txt", context={}):
    """
    Send email to newly created accounts
    """
    # This uses the forgot-password flow; logic is borrowed from auth_forms.PasswordResetForm.save()
    activation_route = request.build_absolute_uri(reverse('password_reset_confirm', args=[
        urlsafe_base64_encode(force_bytes(user.pk)),
        default_token_generator.make_token(user),
    ]))
    context.update({
        'activation_route': activation_route,
        'activation_expires': settings.PASSWORD_RESET_TIMEOUT,
        'request': request
    })
    send_user_email(
        user.raw_email,
        template,
        context
    )


def email_pending_registrar_user(request, user):
    """
    Send email to newly created accounts for folks requesting library accounts
    """
    email_new_user(request, user, template='email/pending_registrar.txt')


def email_registrar_request(request, pending_registrar):
    """
    Send email to Perma.cc admins when a library requests an account
    """
    host = request.get_host()
    try:
        email = request.user.raw_email
    except AttributeError:
        # User did not have an account
        email = request.POST.get('a-e-address')

    send_admin_email(
        "Perma.cc new library registrar account request",
        email,
        request,
        'email/admin/registrar_request.txt',
        {
            "name": pending_registrar.name,
            "email": pending_registrar.email,
            "requested_by_email": email,
            "host": host,
            "confirmation_route": reverse('user_management_approve_pending_registrar', args=[pending_registrar.id])
        }
    )


def email_approved_registrar_user(request, user):
    """
    Send email to newly approved registrar accounts for folks requesting library accounts
    """
    host = request.get_host()
    send_user_email(
        user.raw_email,
        "email/library_approved.txt",
        {
            "host": host,
            "account_route": reverse('user_management_manage_organization')
        }
    )


def email_court_request(request, user):
    """
    Send email to Perma.cc admins when a court requests an account
    """
    try:
        target_user = LinkUser.objects.get(email=user.email)
    except LinkUser.DoesNotExist:
        target_user = None
    send_admin_email(
        "Perma.cc new library court account information request",
        user.raw_email,
        request,
        "email/admin/court_request.txt",
        {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "court_name": user.requested_account_note,
            "has_account": target_user,
            "email": user.raw_email
        }
    )

def email_firm_request(request: HttpRequest, user: LinkUser):
    """
    Send email to Perma.cc admins when a firm requests an account
    """
    organization_form = FirmOrganizationForm(request.POST)
    usage_form = FirmUsageForm(request.POST)
    user_form = CreateUserFormWithFirm(request.POST)

    # Validate form values; this exception should rarely or never arise in practice, but the
    # `cleaned_data` attribute is only populated after checking
    if organization_form.errors or usage_form.errors or user_form.errors:
        raise ValueError('Organization or usage form data contains validation errors')

    try:
        target_user = LinkUser.objects.get(email=user_form.cleaned_data['email'])
    except LinkUser.DoesNotExist:
        target_user = None

    send_admin_email(
        'Perma.cc new law firm account information request',
        user.raw_email,
        request,
        'email/admin/firm_request.txt',
        {
            'target_user': target_user,
            'organization_form': organization_form,
            'usage_form': usage_form,
            'user_form': user_form,
        },
    )

def email_premium_request(request, user):
    """
    Send email to Perma.cc admins when a user requests a premium account
    """
    send_admin_email(
        "Perma.cc premium account request",
        user.raw_email,
        request,
        "email/admin/premium_request.txt",
        {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.raw_email
        }
    )

def email_deletion_request(request):
    """
    Send email to Perma.cc admins when a user requests their account be deleted
    """
    send_admin_email(
        "Perma.cc account deletion request",
        request.user.raw_email,
        request,
        "email/admin/deletion_request.txt",
        {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.raw_email,
            "admin_url": request.build_absolute_uri(reverse('admin:perma_linkuser_change', args=(request.user.id,)))
        }
    )
