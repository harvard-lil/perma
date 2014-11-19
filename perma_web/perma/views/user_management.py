import random, string, logging, json, time
from django.core import serializers
from ratelimit.decorators import ratelimit

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import views as auth_views
from django.contrib.sites.models import get_current_site
from django.core.mail import send_mail
from django.db.models import Count, Max, Min, Sum
from django.utils.http import is_safe_url, cookie_date
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.shortcuts import render_to_response, get_object_or_404, resolve_url
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from django.core.paginator import Paginator
from django.contrib.auth.models import Group
from django.contrib import messages
from mirroring.utils import sign_message

from perma.forms import (
    RegistrarForm, 
    VestingOrgWithRegistrarForm, 
    VestingOrgForm,
    CreateUserForm,
    CreateUserFormWithRegistrar,
    CreateUserFormWithVestingOrg,
    UserFormEdit,
    RegistrarMemberFormEdit,
    VestingMemberWithVestingOrgFormEdit,
    VestingMemberWithGroupFormEdit, 
    UserAddRegistrarForm,
    UserAddVestingOrgForm,
    UserRegForm,
    UserFormSelfEdit, 
    SetPasswordForm, 
)
from perma.models import Registrar, Link, LinkUser, VestingOrg, Folder
from perma.utils import require_group, get_search_query

logger = logging.getLogger(__name__)
valid_member_sorts = ['-email', 'email', 'last_name', '-last_name', 'admin', '-admin', 'registrar__name', '-registrar__name', 'vesting_org__name', '-vesting_org__name', 'date_joined', '-date_joined', 'last_login', '-last_login', 'vested_links_count', '-vested_links_count']
valid_registrar_sorts = ['name', '-name', 'vested_links', '-vested_links', '-date_created', 'date_created', 'last_active', '-last_active']


@require_group('registry_user')
def manage_registrar(request):
    """
    Linky admins can manage registrars (libraries)
    """

    DEFAULT_SORT = 'name'

    sort = request.GET.get('sort', DEFAULT_SORT)
    if sort not in valid_registrar_sorts:
      sort = DEFAULT_SORT
      
    page = request.GET.get('page', 1)
    if page < 1:
        page = 1

    registrars = Registrar.objects.all()

    # handle search
    search_query = request.GET.get('q', '')
    if search_query:
        registrars = get_search_query(registrars, search_query, ['name', 'email', 'website'])
        
    registrars = registrars.annotate(vested_links=Count('vesting_orgs__link',distinct=True), registrar_users=Count('linkuser', distinct=True),last_active=Max('linkuser__last_login', distinct=True),vesting_orgs_count=Count('vesting_orgs',distinct=True)).order_by(sort)

    registrar_count = registrars.count()
    vesting_org_count = registrars.aggregate(count=Sum('vesting_orgs_count'))
    #users_count = registrars.aggregate(count=Sum('registrar_users'))
    registrar_results = registrars.count()
    
    paginator = Paginator(registrars, settings.MAX_USER_LIST_SIZE)
    registrars = paginator.page(page)

    context = {'registrars': registrars, 'registrar_count': registrar_count, 'vesting_org_count':vesting_org_count, #'users_count': users_count, 
        'this_page': 'users_registrars', 'registrar_results': registrar_results,
        'search_query':search_query}

    if request.method == 'POST':

        form = RegistrarForm(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save()

            return HttpResponseRedirect(reverse('user_management_manage_registrar'))

        else:
            context.update({'form': form})
    else:
        form = RegistrarForm(prefix = "a")
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/manage_registrars.html', context)


@require_group('registry_user')
def manage_single_registrar(request, registrar_id):
    """ Linky admins can manage registrars (libraries)
        in this view, we allow for edit/delete """

    target_registrar = get_object_or_404(Registrar, id=registrar_id)

    context = {'target_registrar': target_registrar,
        'this_page': 'users_registrars'}

    if request.method == 'POST':

        form = RegistrarForm(request.POST, prefix = "a", instance=target_registrar)

        if form.is_valid():
            new_user = form.save()
            
            return HttpResponseRedirect(reverse('user_management_manage_registrar'))

        else:
            context.update({'form': form,})
    else:
        form = RegistrarForm(prefix = "a", instance=target_registrar)
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/manage_single_registrar.html', context)
    
@require_group(['registry_user', 'registrar_user'])
def manage_vesting_org(request):
    """
    Registry and registrar members can manage vesting organizations (journals)
    """

    DEFAULT_SORT = 'name'
    is_registry = False
    registrars = None

    sort = request.GET.get('sort', DEFAULT_SORT)
    if sort not in valid_registrar_sorts:
      sort = DEFAULT_SORT
      
    page = request.GET.get('page', 1)
    if page < 1:
        page = 1
        
    # If registry member, return all active vesting members. If registrar member, return just those vesting members that belong to the registrar member's registrar
    if request.user.groups.all()[0].name == 'registry_user':
        vesting_orgs = VestingOrg.objects.all()
        is_registry = True
    else:
        vesting_orgs = VestingOrg.objects.filter(registrar=request.user.registrar)

    # handle search
    search_query = request.GET.get('q', '')
    if search_query:
        vesting_orgs = get_search_query(vesting_orgs, search_query, ['name', 'registrar__name'])
        
    # handle registrar filter
    registrar_filter = request.GET.get('registrar', '')
    if registrar_filter:
        vesting_orgs = vesting_orgs.filter(registrar__id=registrar_filter)
        registrar_filter = Registrar.objects.get(pk=registrar_filter)

    if is_registry:
        registrars = Registrar.objects.all().order_by('name')
        
    vesting_orgs = vesting_orgs.select_related('registrar').order_by(sort).annotate(vesting_users=Count('users', distinct=True), last_active=Max('users__last_login', distinct=True),created_date=Min('users__date_joined', distinct=True), vested_links=Count('link', distinct=True))
    
    users_count = vesting_orgs.aggregate(count=Sum('vesting_users'))
    
    #active_users = LinkUser.objects.all().filter(is_active=True, is_confirmed=True, groups__name='vesting_user', vesting_org__in=vesting_orgs).count()
    #deactivated_users = LinkUser.objects.all().filter(is_confirmed=True, is_active=False, groups__name='vesting_user', vesting_org__in=vesting_orgs).count()
    #unactivated_users = LinkUser.objects.all().filter(is_confirmed=False, is_active=False, groups__name='vesting_user', vesting_org__in=vesting_orgs).count()
        
    vesting_orgs_count = vesting_orgs.count()
    paginator = Paginator(vesting_orgs, settings.MAX_USER_LIST_SIZE)
    vesting_orgs = paginator.page(page)

    context = {'vesting_orgs': vesting_orgs,
        'this_page': 'users_vesting_orgs',
        'search_query':search_query, 'users_count': users_count, 'vesting_orgs_count': vesting_orgs_count, 'registrars': registrars, 'registrar_filter': registrar_filter, 'sort': sort}

    if request.method == 'POST':

        if is_registry:
          form = VestingOrgWithRegistrarForm(request.POST, prefix = "a")
        else:
          form = VestingOrgForm(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save()
            if not is_registry:
                new_user.registrar_id = request.user.registrar_id
                new_user.save()

            return HttpResponseRedirect(reverse('user_management_manage_vesting_org'))

        else:
            context.update({'form': form})
    else:
        if is_registry:
            form = VestingOrgWithRegistrarForm(prefix = "a")
        else:
            form = VestingOrgForm(prefix = "a")
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/manage_vesting_orgs.html', context)


@require_group(['registrar_user', 'registry_user'])
def manage_single_vesting_org(request, vesting_org_id):
    """ Registry and registrar members can manage vesting organizations (journals)
        in this view, we allow for edit/delete """

    target_vesting_org = get_object_or_404(VestingOrg, id=vesting_org_id)
    is_registry = False
    if request.user.groups.all()[0].name == 'registry_user':
        is_registry = True

    context = {'target_vesting_org': target_vesting_org,
        'this_page': 'users_vesting_orgs'}

    if request.method == 'POST':

        if is_registry:
          form = VestingOrgWithRegistrarForm(request.POST, prefix = "a", instance=target_vesting_org)
        else:
          form = VestingOrgForm(request.POST, prefix = "a", instance=target_vesting_org)

        if form.is_valid():
            new_user = form.save()
            
            return HttpResponseRedirect(reverse('user_management_manage_vesting_org'))

        else:
            context.update({'form': form,})
    else:
        if is_registry:
            form = VestingOrgWithRegistrarForm(prefix = "a", instance=target_vesting_org)
        else:
            form = VestingOrgForm(prefix = "a", instance=target_vesting_org)
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/manage_single_vesting_org.html', context)



@require_group(['registrar_user', 'registry_user'])
def manage_registrar_user(request):
    return list_users_in_group(request, 'registrar_user')

@require_group('registry_user')
def manage_single_registrar_user(request, user_id):
    return edit_user_in_group(request, user_id, 'registrar_user')

@require_group('registry_user')
def manage_single_registrar_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'registrar_user')
    
@require_group('registry_user')
def manage_single_registrar_user_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'registrar_user')



@require_group('registry_user')
def manage_user(request):
    return list_users_in_group(request, 'user')

@require_group('registry_user')
def manage_single_user(request, user_id):
    return edit_user_in_group(request, user_id, 'user')

@require_group('registry_user')
def manage_single_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'user')

@require_group('registry_user')
def manage_single_user_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'user')



@require_group(['registrar_user', 'registry_user', 'vesting_user'])
def manage_vesting_user(request):
    return list_users_in_group(request, 'vesting_user')

@require_group(['registrar_user', 'registry_user'])
def manage_single_vesting_user(request, user_id):
    return edit_user_in_group(request, user_id, 'vesting_user')

@require_group('registry_user')
def manage_single_vesting_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'vesting_user')

@require_group('registry_user')
def manage_single_vesting_user_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'vesting_user')



def list_users_in_group(request, group_name):
    """
        Show list of users with given group name.
    """

    is_registry = False
    is_registrar = False
    added_user = request.REQUEST.get('added_user')

    def sorts():
        DEFAULT_SORT = ['last_name']
        sorts = DEFAULT_SORT

        sort = request.GET.get('sort', DEFAULT_SORT)
        if sort not in valid_member_sorts:
            sorts = DEFAULT_SORT
        elif sort == 'admin':
            sorts = ['is_active', 'password']
        elif sort == '-admin':
            sorts = ['-is_active', '-password']
        else:
            sorts[0] = sort
        return sorts

    registrar_filter = request.GET.get('registrar', '')
    page = request.GET.get('page', 1)
    if page < 1:
        page = 1

    users = None
    registrars = None
    vesting_orgs = None
    if request.user.has_group('registry_user'):
        users = LinkUser.objects.select_related('vesting_org').filter(groups__name=group_name).order_by(*sorts()).annotate(vested_links_count=Count('vested_links', distinct=True))
        if registrar_filter:
            vesting_orgs = VestingOrg.objects.filter(registrar__id=registrar_filter).order_by('name')
        else:
            vesting_orgs = VestingOrg.objects.all().order_by('name')
        registrars = Registrar.objects.all().order_by('name')
        is_registry = True
    elif request.user.has_group('registrar_user'):
        if group_name == 'vesting_user':
            users = LinkUser.objects.filter(groups__name=group_name, vesting_org__registrar=request.user.registrar).order_by(*sorts()).annotate(vested_links_count=Count('vested_links', distinct=True))
            vesting_orgs = VestingOrg.objects.filter(registrar_id=request.user.registrar_id).order_by('name')
        else:
            users = LinkUser.objects.filter(groups__name=group_name, registrar=request.user.registrar).exclude(id=request.user.id).order_by(*sorts()).annotate(vested_links_count=Count('vested_links', distinct=True))
        is_registrar = True
    elif request.user.has_group('vesting_user'):
        users = LinkUser.objects.filter(groups__name=group_name, vesting_org=request.user.vesting_org).exclude(id=request.user.id).order_by(*sorts()).annotate(vested_links_count=Count('vested_links', distinct=True))
    
    sort_url = ''
    
    # handle search
    search_query = request.GET.get('q', '')
    if search_query:
        users = get_search_query(users, search_query, ['email', 'first_name', 'last_name', 'vesting_org__name'])
        sort_url = '&q={search_query}'.format(search_query=search_query)
        
    # handle status filter
    status = request.GET.get('status', '')
    if status:
        sort_url = '{sort_url}&status={status}'.format(sort_url=sort_url, status=status)
        if status == 'active':
            users = users.filter(is_confirmed=True, is_active=True)
        elif status == 'deactivated':
            users = users.filter(is_confirmed=True, is_active=False)
        elif status == 'unactivated':
            users = users.filter(is_confirmed=False, is_active=False)
        
    # handle vesting org filter
    vesting_org_filter = request.GET.get('vesting_org', '')
    if vesting_org_filter:
        users = users.filter(vesting_org__id=vesting_org_filter)
        sort_url = '{sort_url}&vesting_org={vesting_org_filter}'.format(sort_url=sort_url, vesting_org_filter=vesting_org_filter)
        vesting_org_filter = VestingOrg.objects.get(pk=vesting_org_filter)
        
    # handle registrar filter
    if registrar_filter:
        if group_name == 'vesting_user':
            users = users.filter(vesting_org__registrar__id=registrar_filter)
        elif group_name == 'registrar_user':
            users = users.filter(registrar__id=registrar_filter)
        sort_url = '{sort_url}&registrar={registrar_filter}'.format(sort_url=sort_url, registrar_filter=registrar_filter)
        registrar_filter = Registrar.objects.get(pk=registrar_filter)

    users = users.select_related('vesting_org')
    active_users = users.filter(is_active=True, is_confirmed=True).count()
    deactivated_users = None
    if is_registry:
        deactivated_users = users.filter(is_confirmed=True, is_active=False).count()
    unactivated_users = users.filter(is_confirmed=False, is_active=False).count()
    users_count = users.count()
    total_vested_links_count = users.aggregate(count=Sum('vested_links_count'))
    paginator = Paginator(users, settings.MAX_USER_LIST_SIZE)
    users = paginator.page(page)
    logger.debug('users_{group_name}s'.format(group_name=group_name))
    context = {
        'this_page': 'users_{group_name}s'.format(group_name=group_name),
        'users': users,
        'users_count': users_count,
        'active_users': active_users,
        'deactivated_users': deactivated_users,
        'unactivated_users': unactivated_users,
        'vesting_orgs': vesting_orgs,
        'total_vested_links_count': total_vested_links_count,
        'registrars': registrars,
        'added_user': added_user,
        'group_name':group_name,
        'pretty_group_name':group_name.replace('_', ' ').capitalize(),
        'user_list_url':'user_management_manage_{group_name}'.format(group_name=group_name),
        'reactivate_user_url':'user_management_manage_single_{group_name}_reactivate'.format(group_name=group_name),
        'single_user_url':'user_management_manage_single_{group_name}'.format(group_name=group_name),
        'delete_user_url':'user_management_manage_single_{group_name}_delete'.format(group_name=group_name),
        
        'sort': sorts()[0],
        'search_query': search_query,
        'registrar_filter': registrar_filter,
        'vesting_org_filter': vesting_org_filter,
        'status': status,
        'sort_url': sort_url
    }
    context['pretty_group_name_plural'] = context['pretty_group_name'] + "s"

    form = None
    form_data = request.POST or None
    if group_name == 'registrar_user':
        form = CreateUserFormWithRegistrar(form_data, prefix="a")
    elif group_name == 'vesting_user':
        if is_registry:
            form = CreateUserFormWithVestingOrg(form_data, prefix="a")
        elif is_registrar:
            form = CreateUserFormWithVestingOrg(form_data, prefix="a", registrar_id=request.user.registrar_id)
    if not form:
        form = CreateUserForm(form_data, prefix = "a")

    if request.method == 'POST':

        if form.is_valid():
            new_user = form.save()

            new_user.is_active = False

            if group_name == 'vesting_user':
                if is_registry or is_registrar:
                    vesting_org = new_user.vesting_org
                else:
                    new_user.vesting_org = request.user.vesting_org

            new_user.save()
            new_user.groups = [Group.objects.get(name=group_name)]

            email_new_user(request, new_user)

            messages.add_message(request, messages.INFO, '<h4>Account created!</h4> <strong>%s</strong> will receive an email with instructions on how to activate the account and create a password.' % new_user.email, extra_tags='safe')
            return HttpResponseRedirect(reverse(context['user_list_url']))

    context['form'] = form

    context = RequestContext(request, context)

    return render_to_response('user_management/manage_users.html', context)


def edit_user_in_group(request, user_id, group_name):
    """
        Edit particular user with given group name.
    """

    is_registrar = request.user.has_group('registrar_user')
    is_registry = request.user.has_group('registry_user')

    target_user = get_object_or_404(LinkUser, id=user_id)

    # Registrar members can only edit their own vesting members
    if not is_registry:
        if group_name == 'vesting_user' and request.user.registrar != target_user.vesting_org.registrar:
            raise Http404
        if group_name == 'registrar_user' or group_name == 'user' or group_name == 'registry_user':
            raise Http404

    context = {
        'target_user': target_user, 'group_name':group_name,
        'this_page': 'users_{group_name}s'.format(group_name=group_name),
        'pretty_group_name':group_name.replace('_', ' ').capitalize(),
        'user_list_url':'user_management_manage_{group_name}'.format(group_name=group_name),
        'delete_user_url':'user_management_manage_single_{group_name}_delete'.format(group_name=group_name),
    }

    form_data = request.POST or None
    if group_name == 'registrar_user' and is_registry:
        form = RegistrarMemberFormEdit(form_data, prefix="a", instance=target_user)
    elif group_name == 'registrar_user' and is_registrar:
        form = VestingMemberFormEdit(form_data, prefix="a", instance=target_user) 
    elif group_name == 'vesting_user':
        if is_registry:
            form = VestingMemberWithGroupFormEdit(form_data, prefix="a", instance=target_user)
        else:
            form = VestingMemberWithVestingOrgFormEdit(form_data, prefix="a", instance=target_user, registrar_id=request.user.registrar_id)
    else:
        form = UserFormEdit(form_data, prefix="a", instance=target_user)

    if request.method == 'POST':

        if form.is_valid():
            new_user = form.save()
            
            if is_registry:
                if form.cleaned_data['group'].name != 'vesting_user':
                    new_user.vesting_org = None
                if form.cleaned_data['group'].name != 'registrar_user':
                    new_user.registrar = None
                new_user.save()
            
            if group_name == 'user' and group_name != form.cleaned_data['group'].name:
                request.session['old_group'] = group_name
                if form.cleaned_data['group'].name == 'registrar_user':
                    return HttpResponseRedirect(reverse('user_management_user_add_registrar', kwargs={'user_id' : user_id}))
                elif form.cleaned_data['group'].name in ('vesting_user'):
                    return HttpResponseRedirect(reverse('user_management_user_add_vesting_org', kwargs={'user_id' : user_id}))

            return HttpResponseRedirect(reverse(context['user_list_url']))

    context['form'] = form

    context = RequestContext(request, context)

    return render_to_response('user_management/manage_single_user.html', context)


@require_group(['registrar_user', 'vesting_user'])
def vesting_user_add_user(request):
    """
        Delete particular user with given group name.
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
        if request.user.has_group('registrar_user'):
            form = CreateUserFormWithVestingOrg(form_data, prefix = "a", initial={'email': user_email}, registrar_id=request.user.registrar_id)
        else:
            form = CreateUserForm(form_data, prefix = "a", initial={'email': user_email})
    else:
        if target_user.has_group('user'):
            cannot_add = False
        if request.user.has_group('registrar_user'):
            form = UserAddVestingOrgForm(form_data, prefix = "a", registrar_id=request.user.registrar_id)
        else:
            form = None
            
    context = {'this_page': 'users_vesting_users', 'user_email': user_email, 'form': form, 'target_user': target_user, 'cannot_add': cannot_add}

    if request.method == 'POST': 
        if ((form and form.is_valid()) or form == None) and not cannot_add:
            if target_user == None:
                target_user = form.save()
                is_new_user = True
    
            if request.user.has_group('registrar_user'):
                vesting_org = form.cleaned_data['vesting_org']
                target_user.vesting_org = vesting_org
            else:
                target_user.vesting_org = request.user.vesting_org

            target_user.groups = [Group.objects.get(name='vesting_user')]
    
            if is_new_user:
                target_user.is_active = False
                email_new_user(request, target_user)
                messages.add_message(request, messages.INFO, '<h4>Account created!</h4> <strong>%s</strong> will receive an email with instructions on how to activate the account and create a password.' % target_user.email, extra_tags='safe')
            else:
                email_new_vesting_user(request, target_user)
                messages.add_message(request, messages.INFO, '<h4>Success!</h4> <strong>%s</strong> is now a vesting user.' % target_user.email, extra_tags='safe')
            
            target_user.save()

            return HttpResponseRedirect(reverse('user_management_manage_vesting_user'))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_add_to_vesting_confirm.html', context)
    

@require_group('registrar_user')
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
        form = CreateUserForm(form_data, prefix = "a", initial={'email': user_email})
    else:
        if target_user.has_group('user'):
            cannot_add = False
        form = None
            
    context = {'this_page': 'users_registrar_users', 'user_email': user_email, 'form': form, 'target_user': target_user, 'cannot_add': cannot_add}

    if request.method == 'POST': 
        if ((form and form.is_valid()) or form == None) and not cannot_add:
            if target_user == None:
                target_user = form.save()
                is_new_user = True
    
            target_user.registrar = request.user.registrar
            target_user.groups = [Group.objects.get(name='registrar_user')]
    
            if is_new_user:
                target_user.is_active = False
                email_new_user(request, target_user)
                messages.add_message(request, messages.INFO, '<h4>Account created!</h4> <strong>%s</strong> will receive an email with instructions on how to activate the account and create a password.' % target_user.email, extra_tags='safe')
            else:
                email_new_registrar_user(request, target_user)
                messages.add_message(request, messages.INFO, '<h4>Success!</h4> <strong>%s</strong> is now a registrar user.' % target_user.email, extra_tags='safe')
            
            target_user.save()

            return HttpResponseRedirect(reverse('user_management_manage_registrar_user'))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_add_to_registrar_confirm.html', context)
    

@require_group(['vesting_user'])
def vesting_user_leave_vesting_org(request):

    context = {'this_page': 'settings', 'user': request.user}

    if request.method == 'POST':
        request.user.vesting_org = None
        request.user.save()
        request.user.groups = [Group.objects.get(name='user')]

        return HttpResponseRedirect(reverse('user_management_manage_account'))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_leave_confirm.html', context)


@require_group('registry_user')
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
            target_member.vesting_org = None
            target_member.registrar = None
            target_member.save()
            target_member.groups = [Group.objects.get(name='user')]
        else:
            target_member.delete()

        return HttpResponseRedirect(reverse('user_management_manage_{group_name}'.format(group_name=group_name)))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_delete_confirm.html', context)


@require_group(['vesting_user', 'registrar_user'])
def manage_single_vesting_user_remove(request, user_id):
    """
        Basically demote a vesting user to a regular user.
    """

    target_member = get_object_or_404(LinkUser, id=user_id)
    is_registrar = request.user.has_group('registrar_user')

    # Vesting managers can only edit their own vesting members
    if is_registrar:
        if request.user.registrar != target_member.vesting_org.registrar:
            raise Http404
    else:
        if request.user.vesting_org != target_member.vesting_org:
            raise Http404

    context = {'target_member': target_member,
               'this_page': 'users_vesting_user'}

    if request.method == 'POST':
        target_member.vesting_org = None
        target_member.save()
        target_member.groups = [Group.objects.get(name='user')]

        return HttpResponseRedirect(reverse('user_management_manage_vesting_user'))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_remove_vesting_confirm.html', context)
    
    
@require_group('registrar_user')
def manage_single_registrar_user_remove(request, user_id):
    """
        Basically demote a vesting user to a regular user.
    """

    target_member = get_object_or_404(LinkUser, id=user_id)

    # Registrar users can only edit their own registrar members
    if not request.user.has_group(['registrar_user']):
        if request.user.registrar != target_member.registrar:
            raise Http404

    context = {'target_member': target_member,
               'this_page': 'users_vesting_user'}

    if request.method == 'POST':
        target_member.registrar = None
        target_member.save()
        target_member.groups = [Group.objects.get(name='user')]

        return HttpResponseRedirect(reverse('user_management_manage_registrar_user'))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_remove_registrar_confirm.html', context)


@require_group('registry_user')
def reactive_user_in_group(request, user_id, group_name):
    """
        Reactivate particular user with given group name.
    """

    target_member = get_object_or_404(LinkUser, id=user_id)

    # Registrar members can only edit their own vesting members
    if not request.user.has_group('registry_user'):
        if request.user.registrar != target_member.vesting_org.registrar:
            return HttpResponseRedirect(reverse('link_browser'))

    # Vesting managers can only edit their own vesting members
    if not request.user.has_group(['registry_user', 'registrar_user', 'vesting_user']):
        if request.user.vesting_org != target_member.vesting_org:
            return HttpResponseRedirect(reverse('link_browser'))

    context = {'target_member': target_member,
               'this_page': 'users_{group_name}s'.format(group_name=group_name)}

    if request.method == 'POST':
        target_member.is_active = True
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_{group_name}'.format(group_name=group_name)))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_reactivate_confirm.html', context)


@require_group(['registry_user'])
def user_add_registrar(request, user_id):
    target_user = get_object_or_404(LinkUser, id=user_id)
    group_name = target_user.groups.all()[0].name
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
    
    
@require_group(['registry_user'])
def user_add_vesting_org(request, user_id):
    target_user = get_object_or_404(LinkUser, id=user_id)
    group_name = target_user.groups.all()[0].name
    old_group = request.session.get('old_group','')
    
    context = {'this_page': 'users_{old_group}s'.format(old_group=old_group)}
    
    if request.method == 'POST':
        form = UserAddVestingOrgForm(request.POST, prefix = "a")

        if form.is_valid():
            target_user.vesting_org = form.cleaned_data['vesting_org']
            target_vesting_org = VestingOrg.objects.get(name=target_user.vesting_org)
            target_user.registrar = target_vesting_org.registrar
            target_user.save()
            messages.add_message(request, messages.INFO, '<strong>%s</strong> is now a <strong>%s</strong>' % (target_user.email, group_name.replace('_', ' ').capitalize()), extra_tags='safe')

            return HttpResponseRedirect(reverse('user_management_manage_{old_group}'.format(old_group=old_group)))

    else:
        form = UserAddVestingOrgForm(prefix = "a")
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/user_add_vesting_org.html', context)
    

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
            
            messages.add_message(request, messages.INFO, 'Profile saved!', extra_tags='safe')

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
    

@require_group(['registrar_user', 'vesting_user'])
def settings_organizations(request):
    """
    Settings view organizations, leave organizations ...
    """

    context = {'next': request.get_full_path(), 'this_page': 'settings_organizations'}

    context = RequestContext(request, context)
    
    return render_to_response('user_management/settings-organizations.html', context)
    
    
@login_required
def settings_tools(request):
    """
    Settings tools ...
    """

    context = {'next': request.get_full_path(), 'this_page': 'settings_tools'}

    context = RequestContext(request, context)
    
    return render_to_response('user_management/settings-tools.html', context)


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


def get_mirror_cookie_domain(request):
    host = request.get_host().split(':')[0] # remove port
    if host.startswith(settings.MIRROR_USERS_SUBDOMAIN+'.'):
        host = host[len(settings.MIRROR_USERS_SUBDOMAIN+'.'):]
    return '.'+host


def logout(request):
    response = auth_views.logout(request, template_name='registration/logout.html')
    # on logout, delete the mirror cookie
    response.delete_cookie(settings.MIRROR_COOKIE_NAME,
                           domain=get_mirror_cookie_domain(request),
                           path=settings.SESSION_COOKIE_PATH)
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
            
            host = request.get_host()

            if settings.DEBUG == False:
                host = settings.HOST

            # Ensure the user-originating redirection url is safe.
            if not is_safe_url(url=redirect_to, host=host):
                redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())

            response = HttpResponseRedirect(redirect_to)

            if settings.MIRRORING_ENABLED:
                # Set the user-info cookie for mirror servers.
                # This will be set by the main server, e.g. //dashboard.perma.cc,
                # but will be readable by any mirror serving //perma.cc.
                user_info = serializers.serialize("json", [request.user], fields=['groups','registrar','vesting_org'])

                # The cookie should last as long as the login cookie, so cookie logic is copied from SessionMiddleware.
                if request.session.get_expire_at_browser_close():
                    max_age = None
                    expires = None
                else:
                    max_age = request.session.get_expiry_age()
                    expires_time = time.time() + max_age
                    expires = cookie_date(expires_time)

                response.set_cookie(settings.MIRROR_COOKIE_NAME,
                                    sign_message(user_info),
                                    max_age=max_age,
                                    expires=expires,
                                    domain=get_mirror_cookie_domain(request),
                                    path=settings.SESSION_COOKIE_PATH,
                                    secure=settings.SESSION_COOKIE_SECURE or None,
                                    httponly=settings.SESSION_COOKIE_HTTPONLY or None)

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

            new_user.groups = [Group.objects.get(name='user')]
            
            email_new_user(request, new_user)

            return HttpResponseRedirect(reverse('register_email_instructions'))
    else:
        form = UserRegForm()

    return render_to_response("registration/register.html",
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
            messages.add_message(request, messages.INFO, 'Your account is activated.  Log in below.')
            return HttpResponseRedirect(reverse('user_management_limited_login'))
    else:
        form = SetPasswordForm(user=user)

    return render_to_response('registration/set_password.html', {'form': form}, RequestContext(request))
    
    
def register_email_instructions(request):
    """
    After the user has registered, give the instructions for confirming
    """
    return render_to_response('registration/check_email.html', RequestContext(request))
    
    
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
    

def email_new_vesting_user(request, user):
    """
    Send email to newly created vesting accounts
    """

    host = request.get_host() if settings.DEBUG else settings.HOST

    content = '''Your Perma.cc account has been associated with %s.  You now have vesting privileges.  If this is a mistake, visit your account settings page to leave %s.

http://%s%s

''' % (user.vesting_org.name, user.vesting_org.name, host, reverse('user_management_manage_account'))

    send_mail(
        "Your Perma.cc account is now associated with {vesting_org}".format(vesting_org=user.vesting_org.name),
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

''' % (user.registrar.name, user.registrar.name, host, reverse('user_management_manage_account'))

    send_mail(
        "Your Perma.cc account is now associated with {registrar}".format(registrar=user.registrar.name),
        content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email], fail_silently=False
    )
