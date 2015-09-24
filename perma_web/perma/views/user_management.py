import random, string, logging, time
from ratelimit.decorators import ratelimit
from tastypie.models import ApiKey

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import views as auth_views
from django.contrib.sites.models import get_current_site
from django.core.mail import send_mail
from django.db.models import Count, Max, Sum
from django.utils.http import is_safe_url, cookie_date
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.shortcuts import render_to_response, get_object_or_404, resolve_url, render
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from django.contrib import messages

from perma.forms import (
    RegistrarForm, 
    OrganizationWithRegistrarForm, 
    OrganizationForm,
    CreateUserForm,
    CreateUserFormWithRegistrar,
    CreateUserFormWithOrganization,
    CreateUserFormWithCourt,
    CreateUserFormWithUniversity,
    UserAddRegistrarForm,
    UserAddOrganizationForm,
    UserRegForm,
    UserFormSelfEdit, 
    SetPasswordForm, 
)
from perma.models import Registrar, LinkUser, Organization
from perma.utils import apply_search_query, apply_pagination, apply_sort_order, send_contact_email

logger = logging.getLogger(__name__)
valid_member_sorts = ['last_name', '-last_name', 'date_joined', '-date_joined', 'last_login', '-last_login', 'vested_links_count', '-vested_links_count']
valid_registrar_sorts = ['name', '-name', 'vested_links', '-vested_links', '-date_created', 'date_created', 'last_active', '-last_active']
valid_org_sorts = ['name', '-name', 'vested_links', '-vested_links', '-date_created', 'date_created', 'last_active', '-last_active', 'organization_users', 'organization_users']


@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_registrar(request):
    """
    Linky admins can manage registrars (libraries)
    """

    registrars = Registrar.objects.all()

    # handle sorting
    registrars, sort = apply_sort_order(request, registrars, valid_registrar_sorts)

    # handle search
    registrars, search_query = apply_search_query(request, registrars, ['name', 'email', 'website'])

    # handle status filter
    status = request.GET.get('status', '')
    if status:
        #sort_url = '{sort_url}&status={status}'.format(sort_url=sort_url, status=status)
        if status == 'approved':
            registrars = registrars.filter(is_approved=True)
        elif status == 'pending':
            registrars = registrars.filter(is_approved=False)

    # handle annotations
    registrars = registrars.annotate(
        vested_links=Count('organizations__link',distinct=True),
        registrar_users=Count('users', distinct=True),
        last_active=Max('users__last_login'),
        orgs_count=Count('organizations',distinct=True),
    )

    orgs_count = registrars.aggregate(count=Sum('orgs_count'))
    #users_count = registrars.aggregate(count=Sum('registrar_users'))

    # handle pagination
    registrars = apply_pagination(request, registrars)

    # handle creation of new registrars
    if request.method == 'POST':
        form = RegistrarForm(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.is_approved = True
            new_user.save()

            return HttpResponseRedirect(reverse('user_management_manage_registrar'))
    else:
        form = RegistrarForm(prefix = "a")

    return render(request, 'user_management/manage_registrars.html', {
        'registrars': registrars,
        'orgs_count': orgs_count,
        # 'users_count': users_count,
        'this_page': 'users_registrars',
        'search_query': search_query,
        'sort': sort,
        'form': form,
    })


@login_required
@user_passes_test(lambda user: user.is_staff or user.is_registrar_member())
def manage_single_registrar(request, registrar_id):
    """ Linky admins can manage registrars (libraries)
        in this view, we allow for edit/delete """

    target_registrar = get_object_or_404(Registrar, id=registrar_id)
    if request.user.is_registrar_member():	
    	if not target_registrar == request.user.registrar:
            raise Http404

    context = {'target_registrar': target_registrar,
        'this_page': 'users_registrars'}

    if request.method == 'POST':

        form = RegistrarForm(request.POST, prefix = "a", instance=target_registrar)

        if form.is_valid():
            new_user = form.save()
            
            if request.user.is_staff:
            	return HttpResponseRedirect(reverse('user_management_manage_registrar'))
            else:
            	return HttpResponseRedirect(reverse('user_management_settings_organizations'))

        else:
            context.update({'form': form,})
    else:
        form = RegistrarForm(prefix = "a", instance=target_registrar)
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/manage_single_registrar.html', context)
    
    
@login_required
@user_passes_test(lambda user: user.is_staff)
def approve_pending_registrar(request, registrar_id):
    """ Perma admins can approve account requests from libraries """

    target_registrar = get_object_or_404(Registrar, id=registrar_id)
    try:
        target_registrar_member = LinkUser.objects.get(pending_registrar=registrar_id)
    except LinkUser.DoesNotExist:
        target_registrar_member = None

    context = {'target_registrar': target_registrar, 'target_registrar_member': target_registrar_member,
        'this_page': 'users_registrars'}

    if request.method == 'POST':
        target_registrar.is_approved = True
        target_registrar.save()
        
        target_registrar_member.registrar = target_registrar
        target_registrar_member.pending_registrar = None
        target_registrar_member.save()
        email_approved_registrar_user(request, target_registrar_member)

        messages.add_message(request, messages.SUCCESS, '<h4>Registrar approved!</h4> <strong>%s</strong> will receive a notification email with further instructions.' % target_registrar_member.email, extra_tags='safe')
        return HttpResponseRedirect(reverse('user_management_manage_registrar'))

    context = RequestContext(request, context)

    return render_to_response('user_management/approve_pending_registrar.html', context)
    
    
@login_required
@user_passes_test(lambda user: user.is_staff or user.is_registrar_member() or user.is_organization_member)
def manage_organization(request):
    """
    Registry and registrar members can manage organizations (journals)
    """

    is_registry = request.user.is_staff
    orgs = Organization.objects.select_related('registrar')

    # handle sorting
    orgs, sort = apply_sort_order(request, orgs, valid_org_sorts)

    # handle search
    orgs, search_query = apply_search_query(request, orgs, ['name', 'registrar__name'])

    # If not registry member, return just those orgs that belong to the registrar member's registrar
    if not is_registry:
    	if request.user.is_registrar_member():
        	orgs = orgs.filter(registrar__id=request.user.registrar_id)
        else:
        	orgs = orgs.filter(pk__in=request.user.organizations.all())

    # handle registrar filter
    registrar_filter = request.GET.get('registrar', '')
    if registrar_filter:
        orgs = orgs.filter(registrar__id=registrar_filter)
        registrar_filter = Registrar.objects.get(pk=registrar_filter)

    # add annotations
    orgs = orgs.annotate(
        organization_users=Count('users', distinct=True),
        last_active=Max('users__last_login'),
        vested_links=Count('link', distinct=True)
    )

    # get total user count
    users_count = orgs.aggregate(count=Sum('organization_users'))['count']

    # handle pagination
    orgs = apply_pagination(request, orgs)

    if request.method == 'POST':
        if is_registry:
            form = OrganizationWithRegistrarForm(request.POST, prefix = "a")
        else:
            form = OrganizationForm(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save()
            if not is_registry:
                new_user.registrar_id = request.user.registrar_id
                new_user.save()

            return HttpResponseRedirect(reverse('user_management_manage_organization'))
    else:
        if is_registry:
            form = OrganizationWithRegistrarForm(prefix = "a")
        else:
            form = OrganizationForm(prefix = "a")

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


@login_required
@user_passes_test(lambda user: user.is_staff or user.is_registrar_member() or user.is_organization_member)
def manage_single_organization(request, org_id):
    """ Registry and registrar members can manage organizations (journals)
        in this view, we allow for edit/delete """

    target_org = get_object_or_404(Organization, id=org_id)
    
    if request.user.is_organization_member:
        if target_org not in request.user.organizations.all():
            raise Http404

    context = {'target_org': target_org,
        'this_page': 'users_orgs'}

    if request.method == 'POST':

        if request.user.is_staff:
            form = OrganizationWithRegistrarForm(request.POST, prefix = "a", instance=target_org)
        else:
            form = OrganizationForm(request.POST, prefix = "a", instance=target_org)

        if form.is_valid():
            new_user = form.save()
            
            return HttpResponseRedirect(reverse('user_management_manage_organization'))

        else:
            context.update({'form': form,})
    else:
        if request.user.is_staff:
            form = OrganizationWithRegistrarForm(prefix = "a", instance=target_org)
        else:
            form = OrganizationForm(prefix = "a", instance=target_org)
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/manage_single_organization.html', context)



@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_registry_user(request):
    return list_users_in_group(request, 'registry_user')
    
@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_single_registry_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'registry_user')

@login_required
@user_passes_test(lambda user: user.is_staff or user.is_registrar_member())
def manage_registrar_user(request):
    return list_users_in_group(request, 'registrar_user')

@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_single_registrar_user(request, user_id):
    return edit_user_in_group(request, user_id, 'registrar_user')

@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_single_registrar_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'registrar_user')
    
@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_single_registrar_user_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'registrar_user')



@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_user(request):
    return list_users_in_group(request, 'user')

@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_single_user(request, user_id):
    return edit_user_in_group(request, user_id, 'user')

@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_single_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'user')

@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_single_user_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'user')



@login_required
@user_passes_test(lambda user: user.is_staff or user.is_registrar_member() or user.is_organization_member)
def manage_organization_user(request):
    return list_users_in_group(request, 'organization_user')

@login_required
@user_passes_test(lambda user: user.is_staff or user.is_registrar_member() or user.is_organization_member)
def manage_single_organization_user(request, user_id):
    return edit_user_in_group(request, user_id, 'organization_user')

@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_single_organization_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'organization_user')

@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_single_organization_user_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'organization_user')



def list_users_in_group(request, group_name):
    """
        Show list of users with given group name.
    """

    is_registry = False
    is_registrar = False
    added_user = request.REQUEST.get('added_user')
    users = LinkUser.objects.prefetch_related('organizations')  # .exclude(id=request.user.id)

    # handle sorting
    users, sort = apply_sort_order(request, users, valid_member_sorts)

    # handle search
    users, search_query = apply_search_query(request, users, ['email', 'first_name', 'last_name', 'organizations__name'])

    # apply annotations
    users = users.annotate(vested_links_count=Count('vested_links', distinct=True))

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
        is_registry = True
    elif request.user.is_registrar_member():
        if group_name == 'organization_user':
            users = users.filter(organizations__registrar=request.user.registrar)
            orgs = Organization.objects.filter(registrar_id=request.user.registrar_id).order_by('name')
        else:
            users = users.filter(registrar=request.user.registrar)
        is_registrar = True
    elif request.user.is_organization_member:
        users = users.filter(organizations__in=request.user.organizations.all())
    else:
        raise Http404  # this shouldn't happen

    # apply group filter
    if group_name == 'registry_user':
        users = users.exclude(is_staff=False)
    elif group_name == 'registrar_user':
        users = users.exclude(registrar_id=None).prefetch_related('registrar')
    elif group_name == 'organization_user':
        users = users.exclude(organizations=None)
    elif group_name == 'user':
        users = users.filter(registrar_id=None, is_staff=False, organizations=None)
    else:
        raise NotImplementedError("Unknown group name: %s" % group_name)
        
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
    if is_registry:
        deactivated_users = users.filter(is_confirmed=True, is_active=False).count()
    unactivated_users = users.filter(is_confirmed=False, is_active=False).count()
    total_vested_links_count = users.aggregate(count=Sum('vested_links_count'))

    # handle pagination
    users = apply_pagination(request, users)

    context = {
        'this_page': 'users_{group_name}s'.format(group_name=group_name),
        'users': users,
        'active_users': active_users,
        'deactivated_users': deactivated_users,
        'unactivated_users': unactivated_users,
        'orgs': orgs,
        'total_vested_links_count': total_vested_links_count,
        'registrars': registrars,
        'added_user': added_user,
        'group_name':group_name,
        'pretty_group_name':group_name.replace('_', ' ').capitalize(),
        'user_list_url':'user_management_manage_{group_name}'.format(group_name=group_name),
        'reactivate_user_url':'user_management_manage_single_{group_name}_reactivate'.format(group_name=group_name),
        'single_user_url':'user_management_manage_single_{group_name}'.format(group_name=group_name),
        'delete_user_url':'user_management_manage_single_{group_name}_delete'.format(group_name=group_name),
        
        'sort': sort,
        'search_query': search_query,
        'registrar_filter': registrar_filter,
        'org_filter': org_filter,
        'status': status,
        'upgrade': upgrade,
    }
    context['pretty_group_name_plural'] = context['pretty_group_name'] + "s"


    # handle creation of new users
    form = None
    form_data = request.POST or None
    if group_name == 'registrar_user':
        form = CreateUserFormWithRegistrar(form_data, prefix="a")
    elif group_name == 'organization_user':
        if is_registry:
            form = CreateUserFormWithOrganization(form_data, prefix="a")
        elif is_registrar:
            form = CreateUserFormWithOrganization(form_data, prefix="a", registrar_id=request.user.registrar_id)
    if not form:
        form = CreateUserForm(form_data, prefix = "a")
    if request.method == 'POST':
        if form.is_valid():
            new_user = form.save()
            new_user.is_active = False
            if group_name == 'organization_user':
                if not (is_registry or is_registrar):
                    new_user.organization = request.user.org
            if group_name == 'registry_user':
                new_user.is_staff = True
            new_user.save()
            email_new_user(request, new_user)
            messages.add_message(request, messages.SUCCESS, '<h4>Account created!</h4> <strong>%s</strong> will receive an email with instructions on how to activate the account and create a password.' % new_user.email, extra_tags='safe')
            return HttpResponseRedirect(reverse(context['user_list_url']))

    context['form'] = form
    return render(request, 'user_management/manage_users.html', context)

def edit_user_in_group(request, user_id, group_name):
    """
        Edit particular user with given group name.
    """

    target_user = get_object_or_404(LinkUser, id=user_id)

    # Org members can only edit their members in the same orgs
    if request.user.is_registrar_member():
        # Get the intersection of the user's and the registrar member's orgs
        orgs = target_user.organizations.all() & Organization.objects.filter(registrar=request.user.registrar)

        if len(orgs) == 0:
            raise Http404

    elif request.user.is_organization_member:
        orgs = target_user.organizations.all() & request.user.organizations.all()

        if len(orgs) == 0:
            raise Http404

    else:
        # Must be registry member
        orgs = target_user.organizations.all()

    context = {
        'target_user': target_user, 'group_name':group_name,
        'this_page': 'users_{group_name}s'.format(group_name=group_name),
        'pretty_group_name':group_name.replace('_', ' ').capitalize(),
        'user_list_url':'user_management_manage_{group_name}'.format(group_name=group_name),
        'delete_user_url':'user_management_manage_single_{group_name}_delete'.format(group_name=group_name),
        'orgs': orgs, 
    }


    context = RequestContext(request, context)

    return render_to_response('user_management/manage_single_user.html', context)


@login_required
@user_passes_test(lambda user: user.is_registrar_member() or user.is_organization_member or user.is_staff)
def organization_user_add_user(request):
    """
        Add new user for organization.
    """
    
    user_email = request.GET.get('email', None)
    try:
        target_user = LinkUser.objects.get(email=user_email)
    except LinkUser.DoesNotExist:
        target_user = None
        
    form = None
    form_data = request.POST or None
    if target_user == None:
        if request.user.is_registrar_member():
            form = CreateUserFormWithOrganization(form_data, prefix = "a", initial={'email': user_email}, registrar_id=request.user.registrar_id)
        elif request.user.is_organization_member:
            form = CreateUserFormWithOrganization(form_data, prefix = "a", initial={'email': user_email}, org_member_id=request.user.pk)
        else:
            form = CreateUserFormWithOrganization(form_data, prefix = "a", initial={'email': user_email})
    else:
        if request.user.is_registrar_member():

            # First, do a little error checking. This target user might already
            # be in each org admined by the user
            orgs = Organization.objects.filter(registrar=request.user.registrar).exclude(pk__in=target_user.organizations.all())

            if len(orgs) > 0:
                form = UserAddOrganizationForm(form_data, prefix = "a", registrar_id=request.user.registrar_id, target_user_id=target_user.pk)
            else:
                messages.add_message(request, messages.ERROR, '<h4>Not added.</h4> <strong>%s</strong> is already a member of all your organizations.' % target_user.email, extra_tags='safe')
                return HttpResponseRedirect(reverse('user_management_manage_organization_user'))

        elif request.user.is_organization_member:

            # First, do a little error checking. This target user might already
            # be in each org admined by the user
            orgs = request.user.organizations.all() | target_user.organizations.all()
            orgs = orgs.exclude(pk__in=target_user.organizations.all())

            if len(orgs) > 0:
                form = UserAddOrganizationForm(form_data, prefix = "a", org_member_id=request.user.pk, target_user_id=target_user.pk)
            else:
                messages.add_message(request, messages.ERROR, '<h4>Not added.</h4> <strong>%s</strong> is already a member of all your organizations.' % target_user.email, extra_tags='safe')
                return HttpResponseRedirect(reverse('user_management_manage_organization_user'))
        else:
            # User is registry member
            # and we're not going to bother to check if the user is already a
            # member of all orgs. That's a crazy corner case.

            form = UserAddOrganizationForm(form_data, prefix = "a", target_user_id=target_user.pk)


            
    context = {'this_page': 'users_organization_users', 'user_email': user_email, 'form': form, 'target_user': target_user}

    is_new_user = False

    if request.method == 'POST':
        if ((form and form.is_valid()) or form == None):

            if target_user == None:
                target_user = form.save()
                is_new_user = True
        
            if is_new_user:
                target_user.is_active = False
                email_new_user(request, target_user)
                messages.add_message(request, messages.SUCCESS, '<h4>Account created!</h4> <strong>%s</strong> will receive an email with instructions on how to activate the account and create a password.' % target_user.email, extra_tags='safe')
            else:
                messages.add_message(request, messages.SUCCESS, '<h4>Success!</h4> <strong>%s</strong> is now a member of an organization.' % target_user.email, extra_tags='safe')

            org = form.cleaned_data['organizations'][0]
            target_user.organizations.add(org)
            target_user.requested_account_note = None
            target_user.requested_account_type = None

            target_user.save()

            if not is_new_user:
                # Drop the newly added user a friendly note
                email_new_organization_user(request, target_user, org)


            return HttpResponseRedirect(reverse('user_management_manage_organization_user'))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_add_to_organization_confirm.html', context)
    

@login_required
@user_passes_test(lambda user: user.is_registrar_member() or user.is_staff)
def registrar_user_add_user(request):
    """
        Registrar users can add other registrar users
    """
    
    user_email = request.GET.get('email', None)
    try:
        target_user = LinkUser.objects.get(email=user_email)
    except LinkUser.DoesNotExist:
        target_user = None
        
    cannot_add = True
    is_new_user = False
    
    form = None
    form_data = request.POST or None
    if target_user == None:
        cannot_add = False
        if request.user.is_registrar_member():
            form = CreateUserForm(form_data, prefix = "a", initial={'email': user_email})
        else:
            form = CreateUserFormWithRegistrar(form_data, prefix = "a", initial={'email': user_email})
    else:
        if not target_user.can_vest():
            cannot_add = False
        if request.user.is_registrar_member():
        	form = None
        else:
        	form = UserAddRegistrarForm(form_data, prefix = "a")
            
    context = {'this_page': 'users_registrar_users', 'user_email': user_email, 'form': form, 'target_user': target_user, 'cannot_add': cannot_add}

    if request.method == 'POST': 
        if ((form and form.is_valid()) or form == None) and not cannot_add:
            if target_user == None:
                target_user = form.save()
                is_new_user = True
    
            if request.user.is_registrar_member():
                target_user.registrar = request.user.registrar
            else:
            	target_user.registrar = form.cleaned_data['registrar']
    
            if is_new_user:
                target_user.is_active = False
                email_new_user(request, target_user)
                messages.add_message(request, messages.SUCCESS, '<h4>Account created!</h4> <strong>%s</strong> will receive an email with instructions on how to activate the account and create a password.' % target_user.email, extra_tags='safe')
            else:
                email_new_registrar_user(request, target_user)
                messages.add_message(request, messages.SUCCESS, '<h4>Success!</h4> <strong>%s</strong> is now a registrar user.' % target_user.email, extra_tags='safe')
            
            target_user.requested_account_note = None
            target_user.requested_account_type = None
            target_user.save()

            return HttpResponseRedirect(reverse('user_management_manage_registrar_user'))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_add_to_registrar_confirm.html', context)
    

@login_required
@user_passes_test(lambda user: user.is_staff)
def registry_user_add_user(request):
    """
        Registry users can add other registry users
    """
    
    user_email = request.GET.get('email', None)
    try:
        target_user = LinkUser.objects.get(email=user_email)
    except LinkUser.DoesNotExist:
        target_user = None
        
    cannot_add = True
    is_new_user = False
    
    form = None
    form_data = request.POST or None
    if target_user == None:
        cannot_add = False
        form = CreateUserForm(form_data, prefix = "a", initial={'email': user_email})
    else:
        if not target_user.is_staff:
            cannot_add = False
        form = None
            
    context = {'this_page': 'users_registry_users', 'user_email': user_email, 'form': form, 'target_user': target_user, 'cannot_add': cannot_add}

    if request.method == 'POST': 
        if ((form and form.is_valid()) or form == None) and not cannot_add:
            if target_user == None:
                target_user = form.save()
                is_new_user = True
    
            target_user.is_staff = True
    
            if is_new_user:
                target_user.is_active = False
                email_new_user(request, target_user)
                messages.add_message(request, messages.SUCCESS, '<h4>Account created!</h4> <strong>%s</strong> will receive an email with instructions on how to activate the account and create a password.' % target_user.email, extra_tags='safe')
            else:
                email_new_registrar_user(request, target_user)
                messages.add_message(request, messages.SUCCESS, '<h4>Success!</h4> <strong>%s</strong> is now a registry user.' % target_user.email, extra_tags='safe')
            
            target_user.save()

            return HttpResponseRedirect(reverse('user_management_manage_registry_user'))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_add_to_registry_confirm.html', context)
    

@login_required
@user_passes_test(lambda user: user.is_organization_member)
def organization_user_leave_organization(request, org_id):

    org = get_object_or_404(Organization, id=org_id)
    context = {'this_page': 'settings', 'user': request.user, 'org': org}

    if request.method == 'POST':
        request.user.organizations.remove(org)
        request.user.save()

        return HttpResponseRedirect(reverse('user_management_settings_organizations'))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_leave_confirm.html', context)


@login_required
@user_passes_test(lambda user: user.is_staff)
def delete_user_in_group(request, user_id, group_name):
    """
        Delete particular user with given group name.
    """

    target_member = get_object_or_404(LinkUser, id=user_id)
        
    context = {'target_member': target_member,
               'this_page': 'users_{group_name}s'.format(group_name=group_name)}

    if request.method == 'POST':
        if target_member.is_confirmed:
            target_member.is_active = False
            target_member.organizations.clear()
            target_member.registrar = None
            target_member.save()
        else:
            target_member.delete()

        return HttpResponseRedirect(reverse('user_management_manage_{group_name}'.format(group_name=group_name)))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_delete_confirm.html', context)


@login_required
@user_passes_test(lambda user: user.is_registrar_member() or user.is_organization_member or user.is_staff)
def manage_single_organization_user_remove(request, user_id):
    """
        Basically demote an organization user to a regular user.
    """

    if request.method == 'POST':

        print "post"

        org = get_object_or_404(Organization, pk=request.POST.get('org'))
        target_user = get_object_or_404(LinkUser, id=user_id)

        if request.user.is_organization_member and org not in request.user.organizations.all():
            # An organization user should only be able to remove an organization user if they're in the org
            raise Http404

        elif request.user.is_registrar_member() and org.registrar != request.user.registrar:
            # A registrar user should only be able to remove a organization user if they're the registrar for that org
            raise Http404

        target_user.organizations.remove(org)


    return HttpResponseRedirect(reverse('user_management_manage_organization_user'))

    
@login_required
@user_passes_test(lambda user: user.is_registrar_member())
def manage_single_registrar_user_remove(request, user_id):
    """
        Basically demote a organization user to a regular user.
    """

    target_member = get_object_or_404(LinkUser, id=user_id)

    # Registrar users can only edit their own registrar members
    if request.user.registrar_id != target_member.registrar_id:
        raise Http404

    context = {'target_member': target_member,
               'this_page': 'organization_user'}

    if request.method == 'POST':
        target_member.registrar = None
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_registrar_user'))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_remove_registrar_confirm.html', context)


@login_required
@user_passes_test(lambda user: user.is_staff)
def manage_single_registry_user_remove(request, user_id):
    """
        Basically demote a registry to a regular user.
    """

    target_member = get_object_or_404(LinkUser, id=user_id)

    context = {'target_member': target_member,
               'this_page': 'users_registry_user'}

    if request.method == 'POST':
        target_member.is_staff = False
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_registry_user'))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_remove_registry_confirm.html', context)
    

@login_required
@user_passes_test(lambda user: user.is_staff)
def reactive_user_in_group(request, user_id, group_name):
    """
        Reactivate particular user with given group name.
    """

    target_member = get_object_or_404(LinkUser, id=user_id)

    context = {'target_member': target_member,
               'this_page': 'users_{group_name}s'.format(group_name=group_name)}

    if request.method == 'POST':
        target_member.is_active = True
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_{group_name}'.format(group_name=group_name)))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_reactivate_confirm.html', context)


@login_required
@user_passes_test(lambda user: user.is_staff)
def user_add_registrar(request, user_id):
    """
        Add given user to a registrar.
    """
    target_user = get_object_or_404(LinkUser, id=user_id)
    group_name = 'registrar_user'
    old_group = request.session.get('old_group','')
    
    context = {'this_page': 'users_{old_group}s'.format(old_group=old_group)}
    
    if request.method == 'POST':
        form = UserAddRegistrarForm(request.POST, prefix = "a")

        if form.is_valid():
            target_user.registrar = form.cleaned_data['registrar']
            target_user.save()
            messages.add_message(request, messages.INFO, '<strong>%s</strong> is now a <strong>%s</strong>' % (target_user.email, group_name.replace('_', ' ').capitalize()), extra_tags='safe')

            return HttpResponseRedirect(reverse('user_management_manage_{old_group}'.format(old_group=old_group)))

    else:
        form = UserAddRegistrarForm(prefix = "a")
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/user_add_registrar.html', context)
    
    
@login_required
@user_passes_test(lambda user: user.is_staff)
def user_add_organization(request, user_id):
    """
        Add given user to an organization.
    """
    target_user = get_object_or_404(LinkUser, id=user_id)
    group_name = 'organization_user'
    old_group = request.session.get('old_group','')
    
    context = {'this_page': 'users_{old_group}s'.format(old_group=old_group)}
    
    if request.method == 'POST':
        form = UserAddOrganizationForm(request.POST, prefix = "a")

        if form.is_valid():
            target_user.org = form.cleaned_data['org']
            target_user.save()
            messages.add_message(request, messages.INFO, '<strong>%s</strong> is now a <strong>%s</strong>' % (target_user.email, group_name.replace('_', ' ').capitalize()), extra_tags='safe')

            return HttpResponseRedirect(reverse('user_management_manage_{old_group}'.format(old_group=old_group)))

    else:
        form = UserAddOrganizationForm(prefix = "a")
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/user_add_organization.html', context)


@login_required
def settings_profile(request):
    """
    Settings profile, change name, change email, ...
    """

    context = {'next': request.get_full_path(), 'this_page': 'settings_profile'}
    context.update(csrf(request))

    if request.method == 'POST':

        form = UserFormSelfEdit(request.POST, prefix = "a", instance=request.user)

        if form.is_valid():
            form.save()
            
            messages.add_message(request, messages.SUCCESS, 'Profile saved!', extra_tags='safe')

            return HttpResponseRedirect(reverse('user_management_settings_profile'))

        else:
            context.update({'form': form,})
    else:
        form = UserFormSelfEdit(prefix = "a", instance=request.user)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/settings-profile.html', context)
    

@login_required
def settings_password(request):
    """
    Settings change password ...
    """

    context = {'next': request.get_full_path(), 'this_page': 'settings_password'}

    context = RequestContext(request, context)
    
    return render_to_response('user_management/settings-password.html', context)
    

@login_required
@user_passes_test(lambda user: user.is_registrar_member() or user.is_organization_member or user.has_registrar_pending())
def settings_organizations(request):
    """
    Settings view organizations, leave organizations ...
    """

    if request.user.has_registrar_pending():
        pending_registrar = get_object_or_404(Registrar, id=request.user.pending_registrar)
        messages.add_message(request, messages.INFO, "Thank you for requesting an account for your library. Perma.cc will review your request as soon as possible.")
    else:
        pending_registrar = None
        
    if request.method == 'POST':
        org = get_object_or_404(Organization, pk=request.POST.get('org'))
        org.default_to_private = request.POST.get('default_to_private')
        org.save()

        return HttpResponseRedirect(reverse('user_management_settings_organizations'))
    
    context = {'next': request.get_full_path(), 'this_page': 'settings_organizations', 'pending_registrar': pending_registrar}

    context = RequestContext(request, context)
    
    return render_to_response('user_management/settings-organizations.html', context)
    
    
@login_required
@user_passes_test(lambda user: user.is_registrar_member() or user.is_organization_member)
def settings_organizations_change_privacy(request, org_id):

    org = get_object_or_404(Organization, id=org_id)
    context = {'this_page': 'settings', 'user': request.user, 'org': org}

    if request.method == 'POST':
        org.default_to_private = not org.default_to_private
        org.save()

        return HttpResponseRedirect(reverse('user_management_settings_organizations'))

    context = RequestContext(request, context)

    return render_to_response('user_management/settings-organizations-change-privacy.html', context)
    
    
@login_required
def settings_tools(request):
    """
    Settings tools ...
    """

    context = {'next': request.get_full_path(), 'this_page': 'settings_tools'}

    context = RequestContext(request, context)
    
    return render_to_response('user_management/settings-tools.html', context)


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

# @login_required
# def batch_convert(request):
#     """
#     Detect and archive URLs from user input.
#     """
#     context = {'this_page': 'batch_convert'}
#     context.update(csrf(request))
#     return render_to_response('user_management/batch_convert.html', context, RequestContext(request))


# @login_required
# def export(request):
#     """
#     Export a CSV of a user's library/
#     """
#
#     context = {'this_page': 'export'}
#     context.update(csrf(request))
#     return render_to_response('user_management/export.html', context, RequestContext(request))


# @login_required
# def custom_domain(request):
#     """
#     Instructions for a user to configure a custom domain.
#     """
#     context = {'this_page': 'custom_domain'}
#     context.update(csrf(request))
#     return render_to_response('user_management/custom_domain.html', context, RequestContext(request))

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
        return render_to_response('registration/not_active.html', context, RequestContext(request))
        
        
def account_is_deactivated(request):
    """
    Informing a user that their account has been deactivated.
    """
    return render_to_response('user_management/deactivated.html', RequestContext(request))


def get_sitewide_cookie_domain(request):
    return '.' + settings.HOST.split(':')[0]  # remove port


def logout(request):
    response = auth_views.logout(request, template_name='registration/logout.html')
    # on logout, delete the cache bypass cookie
    cookie_kwargs = {'domain': get_sitewide_cookie_domain(request),
                     'path': settings.SESSION_COOKIE_PATH}
    response.delete_cookie(settings.CACHE_BYPASS_COOKIE_NAME, **cookie_kwargs)
    return response


@ratelimit(field='email', method='POST', rate=settings.LOGIN_MINUTE_LIMIT, block=True, ip=False,
           keys=lambda req: req.META.get('HTTP_X_FORWARDED_FOR', req.META['REMOTE_ADDR']))
def limited_login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    request.session.set_test_cookie()

    if request.method == "POST":
        form = authentication_form(request, data=request.POST)
        username = request.POST.get('username')
        try:
            target_user = LinkUser.objects.get(email=username)
        except LinkUser.DoesNotExist:
            target_user = None
        if target_user and not target_user.is_confirmed:
            request.session['email'] = target_user.email
            return HttpResponseRedirect(reverse('user_management_not_active'))
        elif target_user and not target_user.is_active:
            return HttpResponseRedirect(reverse('user_management_account_is_deactivated'))
            
          
        if form.is_valid():

            host = request.get_host() if settings.DEBUG else settings.HOST

            # Ensure the user-originating redirection url is safe.
            if not is_safe_url(url=redirect_to, host=host):
                redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())

            response = HttpResponseRedirect(redirect_to)

            # set cache bypass cookie
            # The cookie should last as long as the login cookie, so cookie logic is copied from SessionMiddleware.
            if request.session.get_expire_at_browser_close():
                max_age = None
                expires = None
            else:
                max_age = request.session.get_expiry_age()
                expires_time = time.time() + max_age
                expires = cookie_date(expires_time)

            cookie_kwargs = {'max_age': max_age,
                             'expires': expires,
                             'domain' : get_sitewide_cookie_domain(request),
                             'path'   : settings.SESSION_COOKIE_PATH}

            # Allows cache to be bypass in Cloudflare page rules
            response.set_cookie(settings.CACHE_BYPASS_COOKIE_NAME,
                                1,
                                httponly=False,
                                **cookie_kwargs)

            return response
    else:
        form = authentication_form(request)

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)


@ratelimit(method='POST', rate=settings.REGISTER_MINUTE_LIMIT, block=True, ip=False,
           keys=lambda req: req.META.get('HTTP_X_FORWARDED_FOR', req.META['REMOTE_ADDR']))
def libraries(request):
    """
    Info for libraries, allow them to request accounts
    """
    
    context = {}
    registrar_count = Registrar.objects.all().count()
    
    if request.method == 'POST':
        registrar_form = RegistrarForm(request.POST, prefix = "b")
        registrar_form.fields['name'].label = "Library name"
        registrar_form.fields['email'].label = "Library email"
        registrar_form.fields['website'].label = "Library website"
        if request.user.is_authenticated():
            user_form = None
        else:
            user_form = UserRegForm(request.POST, prefix = "a")
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
        
        if registrar_form.is_valid():
            new_registrar = registrar_form.save(commit=False)
            new_registrar.is_approved = False
            new_registrar.save()
            email_registrar_request(request, new_registrar)


            if not request.user.is_authenticated():
                if user_form.is_valid():
                    new_user = user_form.save(commit=False)
                    new_user.backend='django.contrib.auth.backends.ModelBackend'
                    new_user.is_active = False
                    new_user.pending_registrar = new_registrar.id
                    new_user.save()
                    
                    email_pending_registrar_user(request, new_user)
                    return HttpResponseRedirect(reverse('register_library_instructions'))
                else:
                    context.update({'user_form':user_form, 'registrar_form':registrar_form})
            else:
                request.user.pending_registrar= new_registrar.id
                request.user.save()

                return HttpResponseRedirect(reverse('user_management_settings_organizations'))
            
        else:
            context.update({'user_form':user_form, 'registrar_form':registrar_form})
    else:
        request_data = request.session.get('request_data','')
        user_form = None
        if not request.user.is_authenticated():
            user_form = UserRegForm(prefix = "a")
            user_form.fields['email'].label = "Your email"
        if request_data:
            registrar_form = RegistrarForm(request_data, prefix = "b")
        else:
            registrar_form = RegistrarForm(prefix = "b")
        registrar_form.fields['name'].label = "Library name"
        registrar_form.fields['email'].label = "Library email"
        registrar_form.fields['website'].label = "Library website"

    return render_to_response("libraries.html",
        {'user_form':user_form, 'registrar_form':registrar_form, 'registrar_count': registrar_count},
        RequestContext(request))


@ratelimit(method='POST', rate=settings.REGISTER_MINUTE_LIMIT, block=True, ip=False,
           keys=lambda req: req.META.get('HTTP_X_FORWARDED_FOR', req.META['REMOTE_ADDR']))
def register(request):
    """
    Register a new user
    """
    if request.method == 'POST':
        form = UserRegForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.backend='django.contrib.auth.backends.ModelBackend'
            new_user.is_active = False
            new_user.save()
            
            email_new_user(request, new_user)

            return HttpResponseRedirect(reverse('register_email_instructions'))
    else:
        form = UserRegForm()

    return render_to_response("registration/register.html",
        {'form':form},
        RequestContext(request))
        
        
@ratelimit(method='POST', rate=settings.REGISTER_MINUTE_LIMIT, block=True, ip=False,
           keys=lambda req: req.META.get('HTTP_X_FORWARDED_FOR', req.META['REMOTE_ADDR']))
def sign_up(request):
    """
    Register a new user
    """
    if request.method == 'POST':
        form = UserRegForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.backend='django.contrib.auth.backends.ModelBackend'
            new_user.is_active = False
            new_user.save()
            
            email_new_user(request, new_user)

            return HttpResponseRedirect(reverse('register_email_instructions'))
    else:
        form = UserRegForm()

    return render_to_response("registration/sign-up.html",
        {'form':form},
        RequestContext(request))
        
        
@ratelimit(method='POST', rate=settings.REGISTER_MINUTE_LIMIT, block=True, ip=False,
           keys=lambda req: req.META.get('HTTP_X_FORWARDED_FOR', req.META['REMOTE_ADDR']))
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
            new_user.backend='django.contrib.auth.backends.ModelBackend'
            new_user.is_active = False
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

    return render_to_response("registration/sign-up-courts.html",
        {'form':form},
        RequestContext(request))
        
        
@ratelimit(method='POST', rate=settings.REGISTER_MINUTE_LIMIT, block=True, ip=False,
           keys=lambda req: req.META.get('HTTP_X_FORWARDED_FOR', req.META['REMOTE_ADDR']))
def sign_up_faculty(request):
    """
    Register a new user
    """
    if request.method == 'POST':
        form = CreateUserFormWithUniversity(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.backend='django.contrib.auth.backends.ModelBackend'
            new_user.is_active = False
            new_user.requested_account_type = 'faculty'
            new_user.save()
            
            email_new_user(request, new_user)
            
            messages.add_message(request, messages.INFO, "Remember to ask your library about access to special Perma.cc privileges.")
            return HttpResponseRedirect(reverse('register_email_instructions'))
    else:
        form = CreateUserFormWithUniversity()

    return render_to_response("registration/sign-up-faculty.html",
        {'form':form},
        RequestContext(request))
        
        
@ratelimit(method='POST', rate=settings.REGISTER_MINUTE_LIMIT, block=True, ip=False,
           keys=lambda req: req.META.get('HTTP_X_FORWARDED_FOR', req.META['REMOTE_ADDR']))
def sign_up_journals(request):
    """
    Register a new user
    """
    if request.method == 'POST':
        form = CreateUserFormWithUniversity(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.backend='django.contrib.auth.backends.ModelBackend'
            new_user.is_active = False
            new_user.requested_account_type = 'journal'
            new_user.save()
            
            email_new_user(request, new_user)

            messages.add_message(request, messages.INFO, "Remember to ask your library about access to special Perma.cc priveleges.")
            return HttpResponseRedirect(reverse('register_email_instructions'))
    else:
        form = CreateUserFormWithUniversity()

    return render_to_response("registration/sign-up-journals.html",
        {'form':form},
        RequestContext(request))


# def register_email_code_confirmation(request, code):
#     """
#     Confirm a user's account when the user follows the email confirmation link.
#     """
#     user = get_object_or_404(LinkUser, confirmation_code=code)
#     user.is_active = True
#     user.is_confirmed = True
#     user.save()
#     messages.add_message(request, messages.INFO, 'Your account is activated.  Log in below.')
#     #redirect_url = reverse('user_management_limited_login')
#     #extra_params = '?confirmed=true'
#     #full_redirect_url = '%s%s' % (redirect_url, extra_params)
#     return HttpResponseRedirect(reverse('user_management_limited_login'))
    

def register_email_code_password(request, code):
    """
    Allow system created accounts to create a password.
    """
    # find user based on confirmation code
    try:
        user = LinkUser.objects.get(confirmation_code=code)
    except LinkUser.DoesNotExist:
        return render_to_response('registration/set_password.html', {'no_code': True}, RequestContext(request))

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

    return render_to_response('registration/set_password.html', {'form': form}, RequestContext(request))
    
    
def register_email_instructions(request):
    """
    After the user has registered, give the instructions for confirming
    """
    return render_to_response('registration/check_email.html', RequestContext(request))
    

def register_library_instructions(request):
    """
    After the user requested a library account, give instructions
    """
    return render_to_response('registration/check_email_library.html', RequestContext(request))
    

def court_request_response(request):
    """
    After the user has requested info about a court account
    """
    return render_to_response('registration/court_request.html', RequestContext(request))
    
    
def email_new_user(request, user):
    """
    Send email to newly created accounts
    """
    if not user.confirmation_code:
        user.confirmation_code = ''.join(
            random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(30))
        user.save()
      
    host = request.get_host() if settings.DEBUG else settings.HOST

    content = '''To activate your account, please click the link below or copy it to your web browser.  You will need to create a new password.

http://%s%s

''' % (host, reverse('register_password', args=[user.confirmation_code]))

    logger.debug(content)

    send_mail(
        "A Perma.cc account has been created for you",
        content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email], fail_silently=False
    )
    

def email_new_organization_user(request, user, org):
    """
    Send email to newly created organization accounts
    """

    host = request.get_host() if settings.DEBUG else settings.HOST

    content = '''Your Perma.cc account has been associated with %s.  You now manage archives and peers within the organization.  If this is a mistake, visit your account settings page to leave %s.

http://%s%s

''' % (org.name, org.name, host, reverse('user_management_settings_organizations'))

    send_mail(
        "Your Perma.cc account is now associated with {org}".format(org=org.name),
        content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email], fail_silently=False
    )


def email_new_registrar_user(request, user):
    """
    Send email to newly created registrar accounts
    """

    host = request.get_host() if settings.DEBUG else settings.HOST

    content = '''Your Perma.cc account has been associated with %s.  If this is a mistake, visit your account settings page to leave %s.

http://%s%s

''' % (user.registrar.name, user.registrar.name, host, reverse('user_management_settings_organizations'))

    send_mail(
        "Your Perma.cc account is now associated with {registrar}".format(registrar=user.registrar.name),
        content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email], fail_silently=False
    )
    
    
def email_pending_registrar_user(request, user):
    """
    Send email to newly created accounts for folks requesting library accounts
    """
    if not user.confirmation_code:
        user.confirmation_code = ''.join(
            random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(30))
        user.save()
      
    host = request.get_host() if settings.DEBUG else settings.HOST

    content = '''We will review your library account request as soon as possible. A personal account has been created for you and will be linked to your library once that account is approved. 
    
To activate this personal account, please click the link below or copy it to your web browser.  You will need to create a new password.

http://%s%s

''' % (host, reverse('register_password', args=[user.confirmation_code]))

    logger.debug(content)

    send_mail(
        "A Perma.cc account has been created for you",
        content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email], fail_silently=False
    )
    
    
def email_registrar_request(request, pending_registrar):
    """
    Send email to Perma.cc admins when a library requests an account
    """
      
    host = request.get_host() if settings.DEBUG else settings.HOST

    content = '''A new library account request from %s is awaiting review and approval. 

http://%s%s

''' % (pending_registrar.name, host, reverse('user_management_approve_pending_registrar', args=[pending_registrar.id]))

    logger.debug(content)

    send_contact_email(
        "Perma.cc new library registrar account request",
        content,
        pending_registrar.email,
        request
    )
    

def email_approved_registrar_user(request, user):
    """
    Send email to newly approved registrar accounts for folks requesting library accounts
    """
      
    host = request.get_host() if settings.DEBUG else settings.HOST

    content = '''Your request for a Perma.cc library account has been approved and your personal account has been linked. 
    
To start creating organizations and users, please click the link below or copy it to your web browser.

http://%s%s

''' % (host, reverse('user_management_manage_organization'))

    logger.debug(content)

    send_mail(
        "Your Perma.cc library account is approved",
        content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email], fail_silently=False
    )


def email_court_request(request, court):
    """
    Send email to Perma.cc admins when a library requests an account
    """
      
    host = request.get_host() if settings.DEBUG else settings.HOST
    try:
        target_user = LinkUser.objects.get(email=court.email)
    except LinkUser.DoesNotExist:
        target_user = None
    account_status = "does not have a personal account."
    if target_user:
        account_status = "has a personal account."

    content = '''%s %s has requested more information about creating a court account for %s. 
    
This user %s

''' % (court.first_name, court.last_name, court.requested_account_note, account_status)

    logger.debug(content)

    send_mail(
        "Perma.cc new library court account information request",
        content,
        court.email,
        [settings.DEFAULT_FROM_EMAIL], fail_silently=False
    )
