import csv
import logging
import re
from typing import Literal

from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters


from ratelimit.decorators import ratelimit

from django.views.generic import UpdateView
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth import views as auth_views
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.db.models import Count, F, Max, Sum
from django.db.models.functions import Coalesce, Greatest
from django.db.models.manager import BaseManager
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
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
    UserAddRegistrarForm,
    UserAddSponsoringRegistrarForm,
    UserAddOrganizationForm,
    UserFormWithAdmin,
    UserAddAdminForm,
)
from perma.models import Registrar, LinkUser, Organization, Link, Sponsorship, Folder, UserOrganizationAffiliation
from perma.utils import (apply_search_query, apply_pagination, apply_sort_order, get_form_data,
    ratelimit_ip_key, user_passes_test_or_403)
from perma.email import send_admin_email, send_user_email


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
        return HttpResponseForbidden()

    form = RegistrarForm(get_form_data(request), prefix = "a", instance=target_registrar)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if request.user.is_staff:
                return HttpResponseRedirect(reverse('user_management_manage_registrar'))
            else:
                return HttpResponseRedirect(reverse('settings_affiliations'))

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
    target_org = get_object_or_404(Organization, id=org_id)
    if not request.user.can_edit_organization(target_org):
        return HttpResponseForbidden()

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
    target_org = get_object_or_404(Organization, id=org_id)
    if not request.user.can_edit_organization(target_org):
        return HttpResponseForbidden()

    if request.method == 'POST':
        if target_org.links.count() > 0:
            return HttpResponseForbidden()

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
    target_org = get_object_or_404(Organization, id=org_id)
    if not request.user.can_edit_organization(target_org):
        return HttpResponseForbidden()

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
        user_org_affiliations = UserOrganizationAffiliation.objects.filter(user=target_user).all()
        registrar_orgs = Organization.objects.filter(registrar=request.user.registrar)
        affiliations = user_org_affiliations.filter(organization__in=registrar_orgs)

        if not sponsorships and len(affiliations) == 0:
            return HttpResponseForbidden()

    elif request.user.is_organization_user:
        # org users can only edit their members in the same orgs
        sponsorships = None
        user_org_affiliations = UserOrganizationAffiliation.objects.filter(user=target_user)
        affiliations = user_org_affiliations.filter(organization__in=request.user.organizations.all())

        if len(affiliations) == 0:
            return HttpResponseForbidden()

    else:
        # Must be admin user
        sponsorships = target_user.sponsorships.all().order_by('status', 'registrar__name')
        affiliations = UserOrganizationAffiliation.objects.filter(user=target_user)

    context = {
        'target_user': target_user,
        'group_name': group_name,
        'this_page': f'users_{group_name}s',
        'pretty_group_name': group_name.replace('_', ' ').capitalize(),
        'user_list_url': f'user_management_manage_{group_name}',
        'delete_user_url': f'user_management_manage_single_{group_name}_delete',
        'sponsorships': sponsorships,
        'affiliations': affiliations,
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
                { 'account_settings_page': f"https://{self.request.get_host()}{reverse('settings_profile')}",
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
            return HttpResponseRedirect(reverse('settings_affiliations'))
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
    target_user = get_object_or_404(LinkUser, id=user_id)
    if not request.user.shares_scope_with_user(target_user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        affiliation = get_object_or_404(UserOrganizationAffiliation, id=request.POST.get('affiliation'))
        if not request.user.can_edit_organization(affiliation.organization):
            return HttpResponseForbidden()

        affiliation.delete()

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
        return HttpResponseForbidden()

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
        return HttpResponseForbidden()

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
        return HttpResponseForbidden()

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
                return HttpResponseRedirect(reverse('settings_affiliations'))
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
            organization_form = FirmOrganizationForm()
            usage_form = FirmUsageForm()

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


def suggest_registrars(user: LinkUser, limit: int = 5) -> BaseManager[Registrar]:
    """Suggest potential registrars for a user based on email domain.

    This queries the database for registrars whose website matches the
    base domain from the user's email address. For example, if the
    user's email is `username@law.harvard.edu`, this will suggest
    registrars whose domains end with `harvard.edu`.
    """
    _, email_domain = user.email.split('@')
    base_domain = '.'.join(email_domain.rsplit('.', 2)[-2:])
    pattern = f'^https?://([a-zA-Z0-9\\-\\.]+\\.)?{re.escape(base_domain)}(/.*)?$'
    registrars = (
        Registrar.objects.exclude(status='pending')
        .filter(website__iregex=pattern)
        .order_by('-link_count', 'name')[:limit]
    )
    return registrars


def email_new_user(request, user, template='email/new_user.txt', context=None):
    """
    Send email to newly created accounts
    """
    # This uses the forgot-password flow; logic is borrowed from auth_forms.PasswordResetForm.save()
    activation_route = request.build_absolute_uri(reverse('password_reset_confirm', args=[
        urlsafe_base64_encode(force_bytes(user.pk)),
        default_token_generator.make_token(user),
    ]))

    # Include context variables
    template_is_default = template == 'email/new_user.txt'
    context = context if context is not None else {}
    context.update(
        {
            'activation_expires': settings.PASSWORD_RESET_TIMEOUT,
            'activation_route': activation_route,
            'request': request,
            # Only query DB if we're using the default template; otherwise there's no need
            'suggested_registrars': suggest_registrars(user) if template_is_default else [],
        }
    )

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

    # Validate form values; this should rarely or never arise in practice, but the `cleaned_data`
    # attribute is only populated after checking
    if organization_form.errors or usage_form.errors:
        return HttpResponseBadRequest('Form data contains validation errors')

    try:
        existing_user = LinkUser.objects.get(email=user_form.data['e-address'].casefold())
    except LinkUser.DoesNotExist:
        existing_user = None

    send_admin_email(
        'Perma.cc new law firm account information request',
        user.raw_email,
        request,
        'email/admin/firm_request.txt',
        {
            'existing_user': existing_user,
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


