import logging
import itertools

from datetime import datetime, timedelta

from celery.task.control import inspect as celery_inspect
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables

#from ratelimit.decorators import ratelimit

from django.views.generic import UpdateView
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, PasswordResetForm, PasswordChangeForm
from django.contrib.auth import views as auth_views
from django.db.models import Count, Max, Sum
from django.db.models.expressions import RawSQL
from django.db.models.functions import Coalesce, Greatest
from django.utils import timezone
from django.utils.http import is_safe_url
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import get_object_or_404, resolve_url, render
from django.core.urlresolvers import reverse, reverse_lazy
from django.template.context_processors import csrf
from django.contrib import messages

from perma.forms import (
    RegistrarForm,
    LibraryRegistrarForm,
    OrganizationWithRegistrarForm,
    OrganizationForm,
    UserForm,
    UserFormWithRegistrar,
    UserFormWithOrganization,
    CreateUserFormWithCourt,
    CreateUserFormWithFirm,
    CreateUserFormWithUniversity,
    UserAddRegistrarForm,
    UserAddOrganizationForm,
    UserFormWithAdmin,
    UserAddAdminForm)
from perma.models import Registrar, LinkUser, Organization, Link, Capture, CaptureJob, ApiKey
from perma.utils import apply_search_query, apply_pagination, apply_sort_order, get_form_data, get_lat_long, user_passes_test_or_403, to_timestamp, prep_for_perma_payments
from perma.email import send_admin_email, send_user_email
from perma.exceptions import PermaPaymentsCommunicationException

logger = logging.getLogger(__name__)
valid_member_sorts = ['last_name', '-last_name', 'date_joined', '-date_joined', 'last_login', '-last_login', 'link_count', '-link_count']
valid_registrar_sorts = ['name', '-name', 'link_count', '-link_count', '-date_created', 'date_created', 'last_active', '-last_active']
valid_org_sorts = ['name', '-name', 'link_count', '-link_count', '-date_created', 'date_created', 'last_active', '-last_active', 'organization_users', 'organization_users']


### HELPERS ###

class RequireOrgOrRegOrAdminUser(object):
    """ Mixin for class-based views that requires user to be an org user, registrar user, or admin. """
    @method_decorator(user_passes_test_or_403(lambda user: user.is_registrar_user() or user.is_organization_user or user.is_staff))
    def dispatch(self, request, *args, **kwargs):
        return super(RequireOrgOrRegOrAdminUser, self).dispatch(request, *args, **kwargs)

class RequireRegOrAdminUser(object):
    """ Mixin for class-based views that requires user to be a registrar user or admin. """
    @method_decorator(user_passes_test_or_403(lambda user: user.is_registrar_user() or user.is_staff))
    def dispatch(self, request, *args, **kwargs):
        return super(RequireRegOrAdminUser, self).dispatch(request, *args, **kwargs)

class RequireAdminUser(object):
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
                .annotate(domain=RawSQL("SUBSTRING_INDEX(email, '.', -1)",[]))
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
            'private_policy': Link.objects.filter(is_private=True, private_reason='policy').count(),
            'private_takedown': Link.objects.filter(is_private=True, private_reason='takedown').count(),
            'private_meta_failure': Link.objects.filter(is_private=True, private_reason='failure').count(),
            'links_w_meta_failure_tag': Link.objects.filter(tags__name__in=['meta-tag-retrieval-failure']).count(),
            'links_w_timeout_failure_tag': Link.objects.filter(tags__name__in=['timeout-failure']).count(),
            'links_w_browser_crashed_tag': Link.objects.filter(tags__name__in=['browser-crashed']).count(),
            'total_user_count': LinkUser.objects.count(),
            'unconfirmed_user_count': LinkUser.objects.filter(is_confirmed=False).count()
        }
        out['private_link_percentage'] = round(100.0*out['private_link_count']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_user_percentage_of_total'] = round(100.0*out['private_user_direction']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_user_percentage_of_private'] = round(100.0*out['private_user_direction']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_policy_percentage_of_total'] = round(100.0*out['private_policy']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_policy_percentage_of_private'] = round(100.0*out['private_policy']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_takedown_percentage_of_total'] = round(100.0*out['private_takedown']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_takedown_percentage_of_private'] = round(100.0*out['private_takedown']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_meta_failure_percentage_of_total'] = round(100.0*out['private_meta_failure']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_meta_failure_percentage_of_private'] = round(100.0*out['private_meta_failure']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['tagged_meta_failure_percentage_of_total'] = round(100.0*out['links_w_meta_failure_tag']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['tagged_timeout_failure_percentage_of_total'] = round(100.0*out['links_w_timeout_failure_tag']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['tagged_browser_crashed_percentage_of_total'] = round(100.0*out['links_w_browser_crashed_tag']/out['total_link_count'], 1) if out['total_link_count'] else 0

        out['unconfirmed_user_percentage'] = round(100.0*out['unconfirmed_user_count']/out['total_user_count'], 1) if out['total_user_count'] else 0

    elif stat_type == "celery":
        inspector = celery_inspect()
        active = inspector.active()
        reserved = inspector.reserved()
        stats = inspector.stats()
        queues = []
        if active is not None:
            for queue in active.keys():
                queues.append({
                    'name': queue,
                    'active': active[queue],
                    'reserved': reserved[queue],
                    'stats': stats[queue],
                })
        out = {'queues':queues}

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

    if out:
        return JsonResponse(out)

    else:
        return render(request, 'user_management/stats.html', locals())


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

    # handle sorting
    registrars, sort = apply_sort_order(request, registrars, valid_registrar_sorts)

    # handle search
    registrars, search_query = apply_search_query(request, registrars, ['name', 'email', 'website'])

    # handle status filter
    status = request.GET.get('status', '')
    if status:
        registrars = registrars.filter(status=status)

    # handle annotations
    registrars = registrars.annotate(
        registrar_users=Count('users', distinct=True),
        last_active_registrar=Max('users__last_login'),
        last_active_org_user=Max('organizations__users__last_login'),
        # Greatest on MySQL returns NULL if any fields are NULL:
        # use of Coalesce here is a workaround
        # https://docs.djangoproject.com/en/2.0/ref/models/database-functions/
        last_active=Greatest(Coalesce('last_active_registrar', 'last_active_org_user'), 'last_active_org_user')
    )

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
        new_status = request.POST.get("status")
        if new_status in ["approved", "denied"]:
            target_registrar.status = new_status
            target_registrar.save()

            if new_status == "approved":
                target_registrar_user.registrar = target_registrar
                target_registrar_user.pending_registrar = None
                target_registrar_user.save()
                email_approved_registrar_user(request, target_registrar_user)

                messages.add_message(request, messages.SUCCESS, '<h4>Registrar approved!</h4> <strong>%s</strong> will receive a notification email with further instructions.' % target_registrar_user.email, extra_tags='safe')
            else:
                messages.add_message(request, messages.SUCCESS, 'Registrar request for <strong>%s</strong> denied. Please inform %s if appropriate.' % (target_registrar, target_registrar_user.email), extra_tags='safe')

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
    orgs = Organization.objects.accessible_to(request.user).select_related('registrar')

    # handle sorting
    orgs, sort = apply_sort_order(request, orgs, valid_org_sorts)

    # handle search
    orgs, search_query = apply_search_query(request, orgs, ['name', 'registrar__name'])

    # handle registrar filter
    registrar_filter = request.GET.get('registrar', '')
    if registrar_filter:
        orgs = orgs.filter(registrar__id=registrar_filter)
        registrar_filter = Registrar.objects.get(pk=registrar_filter)

    # add annotations
    orgs = orgs.annotate(
        organization_users=Count('users', distinct=True),
        last_active=Max('users__last_login'),
    )

    # get total user count
    users_count = orgs.aggregate(count=Sum('organization_users'))['count']

    # handle pagination
    orgs = apply_pagination(request, orgs)

    if is_admin:
        form = OrganizationWithRegistrarForm(get_form_data(request), prefix = "a")
    else:
        form = OrganizationForm(get_form_data(request), prefix = "a")

    if request.method == 'POST':
        if form.is_valid():
            new_user = form.save()
            if not is_admin:
                new_user.registrar_id = request.user.registrar_id
                new_user.save()

            return HttpResponseRedirect(reverse('user_management_manage_organization'))

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
        registrars = Registrar.objects.all().order_by('name')
    elif request.user.is_registrar_user():
        if group_name == 'organization_user':
            users = users.filter(organizations__registrar=request.user.registrar)
            orgs = Organization.objects.filter(registrar_id=request.user.registrar_id).order_by('name')
        else:
            users = users.filter(registrar=request.user.registrar)
    elif request.user.is_organization_user:
        users = users.filter(organizations__in=request.user.organizations.all())

    # apply group filter
    if group_name == 'admin_user':
        users = users.exclude(is_staff=False)
    elif group_name == 'registrar_user':
        users = users.exclude(registrar_id=None).prefetch_related('registrar')
    elif group_name == 'organization_user':
        # careful handling to exclude users associated only with deleted orgs
        users = users.filter(organizations__user_deleted=0)
    else:
        # careful handling to include users associated only with deleted orgs
        users = users.filter(registrar_id=None, is_staff=False).exclude(organizations__user_deleted=0)

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
        elif group_name == 'registrar_user':
            users = users.filter(registrar_id=registrar_filter)
        registrar_filter = Registrar.objects.get(pk=registrar_filter)

    # get total counts
    active_users = users.filter(is_active=True, is_confirmed=True).count()
    deactivated_users = None
    if request.user.is_staff:
        deactivated_users = users.filter(is_confirmed=True, is_active=False).count()
    unactivated_users = users.filter(is_confirmed=False, is_active=False).count()
    total_created_links_count = users.aggregate(count=Sum('link_count'))['count']

    # handle pagination
    users = apply_pagination(request, users)

    context = {
        'this_page': 'users_{group_name}s'.format(group_name=group_name),
        'users': users,
        'active_users': active_users,
        'deactivated_users': deactivated_users,
        'unactivated_users': unactivated_users,
        'orgs': orgs,
        'total_created_links_count': total_created_links_count,
        'registrars': registrars,
        'group_name':group_name,
        'pretty_group_name':group_name.replace('_', ' ').capitalize(),
        'user_list_url':'user_management_manage_{group_name}'.format(group_name=group_name),
        'reactivate_user_url':'user_management_manage_single_{group_name}_reactivate'.format(group_name=group_name),
        'single_user_url':'user_management_manage_single_{group_name}'.format(group_name=group_name),
        'delete_user_url':'user_management_manage_single_{group_name}_delete'.format(group_name=group_name),
        'add_user_url':'user_management_{group_name}_add_user'.format(group_name=group_name),

        'sort': sort,
        'search_query': search_query,
        'registrar_filter': registrar_filter,
        'org_filter': org_filter,
        'status': status,
        'upgrade': upgrade,
    }
    context['pretty_group_name_plural'] = context['pretty_group_name'] + "s"

    return render(request, 'user_management/manage_users.html', context)

def edit_user_in_group(request, user_id, group_name):
    """
        Edit particular user with given group name.
    """

    target_user = get_object_or_404(LinkUser, id=user_id)

    # org users can only edit their members in the same orgs
    if request.user.is_registrar_user():
        # Get the intersection of the user's and the registrar user's orgs
        orgs = target_user.organizations.all() & Organization.objects.filter(registrar=request.user.registrar)

        if len(orgs) == 0:
            raise Http404

    elif request.user.is_organization_user:
        orgs = target_user.organizations.all() & request.user.organizations.all()

        if len(orgs) == 0:
            raise Http404

    else:
        # Must be admin user
        orgs = target_user.organizations.all()

    context = {
        'target_user': target_user, 'group_name':group_name,
        'this_page': 'users_{group_name}s'.format(group_name=group_name),
        'pretty_group_name':group_name.replace('_', ' ').capitalize(),
        'user_list_url':'user_management_manage_{group_name}'.format(group_name=group_name),
        'delete_user_url':'user_management_manage_single_{group_name}_delete'.format(group_name=group_name),
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
            return LinkUser.objects.filter(email=user_email).first()

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
                                 '<h4>Account created!</h4> <strong>%s</strong> will receive an email with instructions on how to activate the account and create a password.' % self.object.email,
                                 extra_tags='safe')
        else:
            send_user_email(
                self.object.email,
                self.confirmation_email_template,
                { 'account_settings_page': "https://%s%s" % (self.request.get_host(), reverse('user_management_settings_profile')),
                  'form': form }
            )
            messages.add_message(self.request, messages.SUCCESS,
                                 '<h4>Success!</h4> <strong>%s</strong> added.' % (self.object.email,),
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
            return False, "%s is an admin user and cannot be added to individual organizations." % self.object
        if self.object.is_registrar_user():
            return False, "%s is already a registrar user and cannot be added to individual organizations." % self.object
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
            return False, "%s is an admin user and cannot be added to individual registrars." % self.object

        # limits that apply just if the current user is a registrar rather than staff
        if self.request.user.is_registrar_user():
            if self.object.is_registrar_user():
                if self.object.registrar == self.request.user.registrar:
                    return False, "%s is already a registrar user for your registrar." % self.object
                else:
                    return False, "%s is already a member of another registrar and cannot be added to your registrar." % self.object
            if self.object.organizations.exclude(registrar=self.request.user.registrar).exists():
                return False, "%s belongs to organizations that are not controlled by your registrar. You cannot make them a registrar unless they leave those organizations." % self.object
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

        messages.add_message(request, messages.SUCCESS, '<h4>Success.</h4> You are no longer a member of <strong>%s</strong>.' % org.name, extra_tags='safe')

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
               'this_page': 'users_{group_name}s'.format(group_name=group_name)}

    if request.method == 'POST':
        if target_user.is_confirmed:
            target_user.is_active = False
            target_user.organizations.clear()
            target_user.registrar = None
            target_user.save()
        else:
            target_user.delete()

        return HttpResponseRedirect(reverse('user_management_manage_{group_name}'.format(group_name=group_name)))

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
               'this_page': 'users_{group_name}s'.format(group_name=group_name)}

    if request.method == 'POST':
        target_user.is_active = True
        target_user.save()

        return HttpResponseRedirect(reverse('user_management_manage_{group_name}'.format(group_name=group_name)))

    return render(request, 'user_management/user_reactivate_confirm.html', context)


@login_required
def settings_profile(request):
    """
    Settings profile, change name, change email, ...
    """

    form = UserForm(get_form_data(request), prefix = "a", instance=request.user)

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
@user_passes_test_or_403(lambda user: user.can_view_subscription())
def settings_subscription(request):
    registrar = request.user.registrar
    try:
        subscription_info = registrar.get_subscription_info(datetime.utcnow())
    except PermaPaymentsCommunicationException:
        context = {
            'this_page': 'settings_subscription',
        }
        return render(request, 'user_management/settings-subscription-unavailable.html', context)

    context = {
        'this_page': 'settings_subscription',
        'subscription_info': subscription_info,
        # for subscribing
        'subscribe_url': settings.SUBSCRIBE_URL,
        'encrypted_data_monthly': prep_for_perma_payments(subscription_info['monthly_required_fields']),
        'encrypted_data_annual': prep_for_perma_payments(subscription_info['annual_required_fields']),
        # for canceling
        'cancel_confirm_url': reverse('user_management_settings_subscription_cancel'),
        # for updating
        'encrypted_data_update': prep_for_perma_payments(subscription_info['update_required_fields']),
        'update_url': settings.UPDATE_URL
    }
    return render(request, 'user_management/settings-subscription.html', context)


@sensitive_variables()
@user_passes_test_or_403(lambda user: user.can_view_subscription())
def settings_subscription_cancel(request):
    context = {
        'this_page': 'settings_subscription',
        'cancel_url': settings.CANCEL_URL,
        'data': prep_for_perma_payments({
            'registrar': request.user.registrar.pk,
            'timestamp': to_timestamp(datetime.utcnow())
        })
    }
    return render(request, 'user_management/settings-subscription-cancel-confirm.html', context)


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
        return auth_views.logout(request, template_name='registration/logout_success.html')
    return render(request, "registration/logout.html")


#@ratelimit(rate=settings.LOGIN_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
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

    if request.method == "POST" and not request.user.is_authenticated():
        username = request.POST.get('username')
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

    # This can be removed in Django 1.10 and replaced with redirect_authenticated_user=True
    if request.user.is_authenticated():
        redirect_to = request.POST.get(redirect_field_name, request.GET.get(redirect_field_name, ''))
        if not is_safe_url(url=redirect_to, host=request.get_host()):
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
        return HttpResponseRedirect(redirect_to)

    # subclass authentication_form to add autofocus attribute to username field
    class LoginForm(authentication_form):
        def __init__(self, *args, **kwargs):
            super(LoginForm, self).__init__(*args, **kwargs)
            self.fields['username'].widget.attrs['autofocus'] = ''

    return auth_views.login(request, template_name, redirect_field_name, LoginForm, extra_context)


def reset_password(request):
    """
        Displays the reset password form.

        We wrap the default Django view to add autofocus to the email field,
        and a custom redirect if unconfirmed users try to reset their password.
    """
    class OurPasswordResetForm(PasswordResetForm):
        def __init__(self, *args, **kwargs):
            super(PasswordResetForm, self).__init__(*args, **kwargs)
            self.fields['email'].widget.attrs['autofocus'] = ''

    if request.method == "POST":
        try:
            target_user = LinkUser.objects.get(email=request.POST.get('email'))
        except LinkUser.DoesNotExist:
            target_user = None
        if target_user:
            if not target_user.is_confirmed:
                request.session['email'] = target_user.email
                return HttpResponseRedirect(reverse('user_management_not_active'))
            if not target_user.is_active:
                return HttpResponseRedirect(reverse('user_management_account_is_deactivated'))

    return auth_views.password_reset(request, password_reset_form=OurPasswordResetForm)


def set_access_token_cookie(request):
    """
        This function is designed to run on the warc playback domain. It will set an access token cookie and then
        redirect to the target warc playback.
    """
    token = request.GET.get('token', '')
    link_guid = request.GET.get('guid')
    next = request.GET.get('next')

    redirect_url = '%s/%s/%s' % (settings.WARC_ROUTE, link_guid, next)
    response = HttpResponseRedirect(redirect_url)

    if token and Link(pk=link_guid).validate_access_token(token):
        # set token cookie
        response.set_cookie(link_guid,
                            token,
                            httponly=True,
                            secure=settings.SESSION_COOKIE_SECURE,
                            path='/warc/%s/' % link_guid)

        # set nocache cookie so CloudFlare doesn't cache authenticated results
        response.set_cookie('nocache',
                            '1',
                            httponly=True,
                            secure=settings.SESSION_COOKIE_SECURE)

        # Workaround so IE accepts cookies in iframe. See http://stackoverflow.com/a/16475093
        response['P3P'] = 'CP="No P3P policy."'

    return response


def set_safari_cookie(request):
    """
        Special handling for Safari's third party cookie blocking: when showing a private link, user will be forwarded
        to this view on WARC_HOST to have an arbitrary cookie set, so Safari will let us set an authorization cookie
        in the iframe. Once we set the cookie we forward back to the referrer.
    """
    redirect_url = request.GET.get('next')
    if not is_safe_url(url=redirect_url, host=settings.HOST):
        return HttpResponseBadRequest()
    redirect_url += ('&' if '?' in redirect_url else '?') + 'safari=1'
    response = HttpResponseRedirect(redirect_url)
    response.set_cookie('safari', '1')
    return response


#@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def libraries(request):
    """
    Info for libraries, allow them to request accounts
    """
    if request.method == 'POST':
        registrar_form = LibraryRegistrarForm(request.POST, request.FILES, prefix ="b")
        if request.user.is_authenticated():
            user_form = None
        else:
            user_form = UserForm(request.POST, prefix = "a")
            user_form.fields['email'].label = "Your email"
        user_email = request.POST.get('a-email', None)
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
            address = registrar_form.cleaned_data.get('address', '')
            if settings.GEOCODING_KEY and address:
                try:
                    (lat, lng) = get_lat_long(address)
                    new_registrar.latitude = lat
                    new_registrar.longitude = lng
                    new_registrar.save(update_fields=["latitude", "longitude"])
                except TypeError:
                    # get_lat_long returned None
                    pass
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
        if not request.user.is_authenticated():
            user_form = UserForm(prefix="a")
            user_form.fields['email'].label = "Your email"
        if request_data:
            registrar_form = LibraryRegistrarForm(request_data, prefix="b")
        else:
            registrar_form = LibraryRegistrarForm(prefix="b")

    return render(request, "registration/sign-up-libraries.html",
        {'user_form':user_form, 'registrar_form':registrar_form})

#@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up(request):
    """
    Register a new user
    """
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            email_new_user(request, new_user)
            return HttpResponseRedirect(reverse('register_email_instructions'))
    else:
        form = UserForm()

    return render(request, "registration/sign-up.html", {'form': form})


#@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_courts(request):
    """
    Register a new court user
    """
    if request.method == 'POST':
        form = CreateUserFormWithCourt(request.POST)
        user_email = request.POST.get('email', None)
        try:
            target_user = LinkUser.objects.get(email=user_email)
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


#@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_faculty(request):
    """
    Register a new user
    """
    if request.method == 'POST':
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

#@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_firm(request):
    """
    Register a new law firm user
    """
    if request.method == 'POST':
        form = CreateUserFormWithFirm(request.POST)
        user_email = request.POST.get('email', None)
        try:
            target_user = LinkUser.objects.get(email=user_email)
        except LinkUser.DoesNotExist:
            target_user = None
        if target_user:
            requested_account_note = request.POST.get('requested_account_note', None)
            target_user.requested_account_type = 'firm'
            target_user.requested_account_note = requested_account_note
            target_user.save()
            email_firm_request(request, target_user)
            return HttpResponseRedirect(reverse('firm_request_response'))

        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.requested_account_type = 'firm'
            create_account = request.POST.get('create_account', None)
            if create_account:
                new_user.save()
                email_new_user(request, new_user)
                email_firm_request(request, new_user)
                messages.add_message(request, messages.INFO, "We will shortly follow up with more information about how Perma.cc could work in your firm.")
                return HttpResponseRedirect(reverse('register_email_instructions'))
            else:
                email_firm_request(request, new_user)
                return HttpResponseRedirect(reverse('firm_request_response'))

    else:
        form = CreateUserFormWithFirm()

    return render(request, "registration/sign-up-firms.html", {'form': form})


#@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_journals(request):
    """
    Register a new user
    """
    if request.method == 'POST':
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


def register_email_code_password(request, code):
    """
    Allow system created accounts to create a password.
    """
    # find user based on confirmation code
    try:
        user = LinkUser.objects.get(confirmation_code=code)
    except LinkUser.DoesNotExist:
        return render(request, 'registration/set_password.html', {'no_code': True})

    # save password
    if request.method == "POST":
        form = SetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save(commit=False)
            user.is_active = True
            user.is_confirmed = True
            user.save()
            messages.add_message(request, messages.SUCCESS, 'Your account is activated.  Log in below.')
            return HttpResponseRedirect(reverse('user_management_limited_login'))
    else:
        form = SetPasswordForm(user=user)

    return render(request, 'registration/set_password.html', {'form': form})


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
    if not user.confirmation_code:
        user.save_new_confirmation_code()
    host = request.get_host()
    context.update({
        "host": host,
        "activation_route": reverse('register_password', args=[user.confirmation_code]),
        "request": request
    })
    send_user_email(
        user.email,
        template,
        context
    )


def email_pending_registrar_user(request, user):
    """
    Send email to newly created accounts for folks requesting library accounts
    """
    if not user.confirmation_code:
        user.save_new_confirmation_code()

    host = request.get_host()

    send_user_email(
        user.email,
        'email/pending_registrar.txt',
        {
            "host": host,
            "activation_route": reverse('register_password', args=[user.confirmation_code])
        }
    )


def email_registrar_request(request, pending_registrar):
    """
    Send email to Perma.cc admins when a library requests an account
    """
    host = request.get_host()
    try:
        email = request.user.email
    except AttributeError:
        # User did not have an account
        email = request.POST.get('a-email')

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
        user.email,
        "email/library_approved.txt",
        {
            "host": host,
            "account_route": reverse('user_management_manage_organization')
        }
    )


def email_court_request(request, court):
    """
    Send email to Perma.cc admins when a court requests an account
    """
    try:
        target_user = LinkUser.objects.get(email=court.email)
    except LinkUser.DoesNotExist:
        target_user = None
    send_admin_email(
        "Perma.cc new library court account information request",
        court.email,
        request,
        "email/admin/court_request.txt",
        {
            "first_name": court.first_name,
            "last_name": court.last_name,
            "court_name": court.requested_account_note,
            "has_account": target_user
        }
    )

def email_firm_request(request, firm):
    """
    Send email to Perma.cc admins when a firm requests an account
    """
    try:
        target_user = LinkUser.objects.get(email=firm.email)
    except LinkUser.DoesNotExist:
        target_user = None
    send_admin_email(
        "Perma.cc new law firm account information request",
        firm.email,
        request,
        "email/admin/firm_request.txt",
        {
            "first_name": firm.first_name,
            "last_name": firm.last_name,
            "firm_name": firm.requested_account_note,
            "has_account": target_user
        }
    )
