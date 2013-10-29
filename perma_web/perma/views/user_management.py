import logging

from perma.forms import user_reg_form, registrar_form, journal_manager_form_edit, journal_manager_w_group_form_edit, journal_member_form_edit, journal_member_w_group_form_edit, regisrtar_member_form_edit, user_form_self_edit, user_form_edit, set_password_form, create_user_form, create_user_form_w_registrar
from perma.models import Registrar, Link
from perma.utils import base

from django.template import Template, context, RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import get_current_site
from django.utils.http import is_safe_url
from django.http import  HttpResponseRedirect
from django.template.response import TemplateResponse
from django.shortcuts import render_to_response, get_object_or_404, resolve_url
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from django.contrib import auth
from django.contrib.auth.models import User, Permission, Group
import random, string, smtplib
from email.mime.text import MIMEText
from django.core.paginator import Paginator
from perma.models import LinkUser
from ratelimit.decorators import ratelimit


logger = logging.getLogger(__name__)
valid_member_sorts = ['-email', 'email', 'last_name', '-last_name', 'admin', '-admin', 'registrar__name', '-registrar__name']
valid_registrar_sorts = ['-email', 'email', 'name', '-name', 'website', '-website']

@login_required
def manage(request):
    """
    The landing page for users who are signed in
    """

    if request.user.id >= 0:
      linky_links = list(Link.objects.filter(created_by=request.user).order_by('-creation_timestamp'))
    else:
      linky_links = None;

    context = RequestContext(request, {'this_page': 'manage', 'host': request.get_host(), 'user': request.user, 'linky_links': linky_links, 'next': request.get_full_path()})

    return render_to_response('user_management/manage.html', context)
    
@login_required
def create_link(request):
    """
    The landing page for users who are signed in
    """

    if request.user.id >= 0:
      linky_links = list(Link.objects.filter(created_by=request.user).order_by('-creation_timestamp'))
    else:
      linky_links = None;

    context = RequestContext(request, {'this_page': 'create_link', 'host': request.get_host(), 'user': request.user, 'linky_links': linky_links, 'next': request.get_full_path()})

    return render_to_response('user_management/create-link.html', context)
    

@login_required
def manage_registrar(request):
    """
    Linky admins can manage registrars (libraries)
    """

    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    DEFAULT_SORT = 'name'

    sort = request.GET.get('sort', DEFAULT_SORT)
    if sort not in valid_registrar_sorts:
      sort = DEFAULT_SORT
      
    page = request.GET.get('page', 1)
    if page < 1:
        page = 1
    registrars = Registrar.objects.all().order_by(sort)
    
    paginator = Paginator(registrars, settings.MAX_USER_LIST_SIZE)
    registrars = paginator.page(page)

    context = {'user': request.user, 'registrars_list': list(registrars), 'registrars': registrars,
        'this_page': 'users_registrars'}

    if request.method == 'POST':

        form = registrar_form(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save()

            return HttpResponseRedirect(reverse('user_management_manage_registrar'))

        else:
            context.update({'form': form, 'add_error': True})
    else:
        form = registrar_form(prefix = "a")
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/manage_registrars.html', context)


@login_required
def manage_single_registrar(request, registrar_id):
    """ Linky admins can manage registrars (libraries)
        in this view, we allow for edit/delete """

    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    target_registrar = get_object_or_404(Registrar, id=registrar_id)

    context = {'user': request.user, 'target_registrar': target_registrar,
        'this_page': 'users_registrars'}

    if request.method == 'POST':

        form = registrar_form(request.POST, prefix = "a", instance=target_registrar)

        if form.is_valid():
            new_user = form.save()
            
            return HttpResponseRedirect(reverse('user_management_manage_registrar'))

        else:
            context.update({'form': form,})
    else:
        form = registrar_form(prefix = "a", instance=target_registrar)
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/manage_single_registrar.html', context)


@login_required
def manage_registrar_member(request):
    """
    Linky admins can manage registrar members (librarians)
    """

    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))
    
    added_user = request.REQUEST.get('added_user')
    
    def sorts():
      DEFAULT_SORT = ['email']
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
    
    page = request.GET.get('page', 1)
    if page < 1:
        page = 1

    registrar_members = LinkUser.objects.filter(groups__name='registrar_member').order_by(*sorts())
    
    paginator = Paginator(registrar_members, settings.MAX_USER_LIST_SIZE)
    registrar_members = paginator.page(page)

    context = {'user': request.user, 'registrar_members_list': list(registrar_members), 'registrar_members': registrar_members,
        'this_page': 'users_registrar_members', 'added_user': added_user}

    if request.method == 'POST':

        form = create_user_form_w_registrar(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save()

            new_user.backend='django.contrib.auth.backends.ModelBackend'
            
            new_user.is_active = False
            new_user.save()
            
            group = Group.objects.get(name='registrar_member')
            new_user.groups.add(group)
            
            email_new_user(request, new_user)

            redirect_url = reverse('user_management_manage_registrar_member')
            extra_params = '?added_user=%s' % new_user.email
            full_redirect_url = '%s%s' % (redirect_url, extra_params)
            return HttpResponseRedirect(full_redirect_url)

        else:
            context.update({'form': form, 'add_error': True})
    else:
        form = create_user_form_w_registrar(prefix = "a")
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_registrar_members.html', context)


@login_required
def manage_single_registrar_member(request, user_id):
    """
    Linky admins can manage registrar members (librarians)
    in this view, we allow for edit
    """

    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    target_registrar_member = get_object_or_404(LinkUser, id=user_id)

    context = {'user': request.user, 'target_registrar_member': target_registrar_member,
        'this_page': 'users_registrar_members'}

    if request.method == 'POST':

        form = regisrtar_member_form_edit(request.POST, prefix = "a", instance=target_registrar_member)

        if form.is_valid():
            new_user = form.save()

            return HttpResponseRedirect(reverse('user_management_manage_registrar_member'))

        else:
            context.update({'form': form,})
    else:
        form = regisrtar_member_form_edit(prefix = "a", instance=target_registrar_member)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_registrar_member.html', context)


@login_required
def manage_single_registrar_member_delete(request, user_id):
    """
    Linky admins can manage registrar members. Delete a single registrar member here.
    """

    # Only registry members can delete registrar members
    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    target_member = get_object_or_404(LinkUser, id=user_id)

    context = {'user': request.user, 'target_member': target_member,
        'this_page': 'users_registrar_members'}

    if request.method == 'POST':
        target_member.is_active = False
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_registrar_member'))
    else:
        form = journal_member_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_registrar_member_delete_confirm.html', context)
    
@login_required
def manage_single_registrar_member_reactivate(request, user_id):
    """
    Perma admins can manage registrar members. Reactivate a single registrar member here.
    """

    # Only registry members can delete registrar members
    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    target_member = get_object_or_404(LinkUser, id=user_id)

    context = {'user': request.user, 'target_member': target_member,
        'this_page': 'users_registrar_members'}

    if request.method == 'POST':
        target_member.is_active = True
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_registrar_member'))
    else:
        form = journal_member_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_registrar_member_reactivate_confirm.html', context)

@login_required
def manage_user(request):
    """
    Linky admins can manage regular users
    """

    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))
        
    added_user = request.REQUEST.get('added_user')
    
    def sorts():
      DEFAULT_SORT = ['email']
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
    
    page = request.GET.get('page', 1)
    if page < 1:
        page = 1

    users = LinkUser.objects.filter(groups__name='user').order_by(*sorts())
    
    paginator = Paginator(users, settings.MAX_USER_LIST_SIZE)
    users = paginator.page(page)

    context = {'user': request.user, 'users_list': list(users),
        'this_page': 'users_users', 'users': users, 'added_user': added_user}

    if request.method == 'POST':

        form = create_user_form(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save()

            new_user.backend='django.contrib.auth.backends.ModelBackend'
            
            new_user.is_active = False
            new_user.save()
            
            group = Group.objects.get(name='user')
            new_user.groups.add(group)
            
            email_new_user(request, new_user)

            redirect_url = reverse('user_management_manage_user')
            extra_params = '?added_user=%s' % new_user.email
            full_redirect_url = '%s%s' % (redirect_url, extra_params)
            return HttpResponseRedirect(full_redirect_url)

        else:
            context.update({'form': form, 'add_error': True})
    else:
        form = create_user_form(prefix = "a")
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_users.html', context)


@login_required
def manage_single_user(request, user_id):
    """
    Linky admins can manage regular users
    in this view, we allow for edit
    """

    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    target_user = get_object_or_404(LinkUser, id=user_id)

    context = {'user': request.user, 'target_user': target_user,
        'this_page': 'users_users'}

    if request.method == 'POST':

        form = user_form_edit(request.POST, prefix = "a", instance=target_user)

        if form.is_valid():
            new_user = form.save()

            return HttpResponseRedirect(reverse('user_management_manage_user'))

        else:
            context.update({'form': form,})
    else:
        form = user_form_edit(prefix = "a", instance=target_user)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_user.html', context)


@login_required
def manage_single_user_delete(request, user_id):
    """
    Linky admins can manage regular users. Delete a single user here.
    """

    # Only registry members can delete registrar members
    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    target_member = get_object_or_404(LinkUser, id=user_id)

    context = {'user': request.user, 'target_member': target_member,
        'this_page': 'users_users'}

    if request.method == 'POST':
        target_member.is_active = False
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_user'))
    else:
        form = user_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_user_delete_confirm.html', context)
    
@login_required
def manage_single_user_reactivate(request, user_id):
    """
    Linky admins can manage regular users. Delete a single user here.
    """

    # Only registry members can delete registrar members
    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    target_member = get_object_or_404(LinkUser, id=user_id)

    context = {'user': request.user, 'target_member': target_member,
        'this_page': 'users_users'}

    if request.method == 'POST':
        target_member.is_active = True
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_user'))
    else:
        form = user_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_user_reactivate_confirm.html', context)


@login_required
def manage_journal_manager(request):
    """
    Linky admins and registrars can manage vesting members
    """

    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))
        
    is_registry = False;
    added_user = request.REQUEST.get('added_user')
    
    def sorts():
      DEFAULT_SORT = ['email']
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
    
    page = request.GET.get('page', 1)
    if page < 1:
        page = 1

    # If registry member, return all active vesting members. If registrar member, return just those vesting members that belong to the registrar member's registrar
    if request.user.groups.all()[0].name == 'registry_member':
        journal_managers = LinkUser.objects.filter(groups__name='vesting_manager').order_by(*sorts())
        is_registry = True
    else:
        journal_managers = LinkUser.objects.filter(groups__name='vesting_manager', registrar=request.user.registrar).exclude(id=request.user.id).order_by(*sorts())
    
    paginator = Paginator(journal_managers, settings.MAX_USER_LIST_SIZE)
    journal_managers = paginator.page(page)

    context = {'user': request.user, 'journal_managers_list': list(journal_managers), 'journal_managers': journal_managers,
        'this_page': 'users_vesting_managers', 'added_user': added_user}

    if request.method == 'POST':

        if is_registry:
          form = create_user_form_w_registrar(request.POST, prefix="a")
        else:
          form = create_user_form(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save()

            new_user.backend='django.contrib.auth.backends.ModelBackend'
            
            new_user.is_active = False
            new_user.save()
            
            if not is_registry:
              new_user.registrar = request.user.registrar
            new_user.save()

            group = Group.objects.get(name='vesting_manager')
            new_user.groups.add(group)
            
            email_new_user(request, new_user)

            redirect_url = reverse('user_management_manage_journal_manager')
            extra_params = '?added_user=%s' % new_user.email
            full_redirect_url = '%s%s' % (redirect_url, extra_params)
            return HttpResponseRedirect(full_redirect_url)

        else:
            context.update({'form': form, 'add_error': True})
    else:
      if is_registry:
        form = create_user_form_w_registrar(prefix="a")
      else:
        form = create_user_form(prefix = "a")
        
      context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_journal_managers.html', context)


@login_required
def manage_single_journal_manager(request, user_id):
    """
    Linky admins and registrars can manage vesting members. Edit a single vesting member here.
    """

    # Only registry members and registrar memebers can edit vesting members
    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))
        
    is_registry = False;
    if request.user.groups.all()[0].name == 'registry_member':
      is_registry = True;

    target_member = get_object_or_404(LinkUser, id=user_id)

    # Registrar members can only edit their own vesting members
    if request.user.groups.all()[0].name not in ['registry_member']:
        if request.user.registrar != target_member.registrar:
            return HttpResponseRedirect(reverse('user_management_created_links'))

    context = {'user': request.user, 'target_member': target_member,
        'this_page': 'users_vesting_managers'}

    if request.method == 'POST':

        if is_registry:
          form = journal_manager_w_group_form_edit(request.POST, prefix = "a", instance=target_member)
        else:
          form = journal_manager_form_edit(request.POST, prefix = "a", instance=target_member)

        if form.is_valid():
            form.save()

            return HttpResponseRedirect(reverse('user_management_manage_journal_manager'))

        else:
            context.update({'form': form,})
    else:
        if is_registry:
          form = journal_manager_w_group_form_edit(prefix = "a", instance=target_member)
        else: 
          form = journal_manager_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_journal_manager.html', context)


@login_required
def manage_single_journal_manager_delete(request, user_id):
    """
    Linky admins and registrars can manage vesting members. Delete a single vesting member here.
    """

    # Only registry members and registrar memebers can edit vesting managers
    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    target_member = get_object_or_404(LinkUser, id=user_id)

    # Registrar members can only edit their own vesting members
    if request.user.groups.all()[0].name not in ['registry_member']:
        if request.user.registrar != target_member.registrar:
            return HttpResponseRedirect(reverse('user_management_created_links'))

    context = {'user': request.user, 'target_member': target_member,
        'this_page': 'users_vesting_managers'}

    if request.method == 'POST':
        target_member.is_active = False
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_journal_manager'))
    else:
        form = journal_manager_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_journal_manager_delete_confirm.html', context)
    
@login_required
def manage_single_journal_manager_reactivate(request, user_id):
    """
    Perma admins and registrars can manage vesting managers. Reactivate a single vesting manager here.
    """

    # Only registry members and registrar memebers can edit vesting managers
    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    target_member = get_object_or_404(LinkUser, id=user_id)

    # Registrar members can only edit their own vesting members
    if request.user.groups.all()[0].name not in ['registry_member']:
        if request.user.registrar != target_member.registrar:
            return HttpResponseRedirect(reverse('user_management_created_links'))

    context = {'user': request.user, 'target_member': target_member,
        'this_page': 'users_vesting_managers'}

    if request.method == 'POST':
        target_member.is_active = True
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_journal_manager'))
    else:
        form = journal_manager_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_journal_manager_reactivate_confirm.html', context)

valid_sorts = ['-creation_timestamp', 'creation_timestamp', 'vested_timestamp', '-vested_timestamp']


@login_required
def manage_journal_member(request):
    """
    Linky admins and registrars can manage vesting members
    """

    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member', 'vesting_manager']:
        return HttpResponseRedirect(reverse('user_management_created_links'))
        
    is_registry = False;
    added_user = request.REQUEST.get('added_user')
    
    def sorts():
      DEFAULT_SORT = ['email']
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
    page = request.GET.get('page', 1)
    if page < 1:
        page = 1

    # If registry member, return all active vesting members. If registrar member, return just those vesting members that belong to the registrar member's registrar
    if request.user.groups.all()[0].name == 'registry_member':
        journal_members = LinkUser.objects.filter(groups__name='vesting_member').order_by(*sorts())
        is_registry = True;
    elif request.user.groups.all()[0].name == 'vesting_manager':
        journal_members = LinkUser.objects.filter(authorized_by=request.user).exclude(id=request.user.id).order_by(*sorts())
    else:
    	journal_members = LinkUser.objects.filter(groups__name='vesting_member', registrar=request.user.registrar).exclude(id=request.user.id).order_by(*sorts())
    	
    paginator = Paginator(journal_members, settings.MAX_USER_LIST_SIZE)
    journal_members = paginator.page(page)
    context = {'user': request.user, 'journal_members_list': list(journal_members), 'journal_members': journal_members,
        'this_page': 'users_vesting_users', 'added_user': added_user}

    if request.method == 'POST':

        if is_registry:
          form = create_user_form_w_registrar(request.POST, prefix="a")
        else:
          form = create_user_form(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save()

            new_user.backend='django.contrib.auth.backends.ModelBackend'
            
            new_user.is_active = False
            new_user.save()
            
            if not is_registry:
              new_user.registrar = request.user.registrar
            new_user.authorized_by = request.user
            new_user.save()

            group = Group.objects.get(name='vesting_member')
            new_user.groups.add(group)
            
            email_new_user(request, new_user)

            redirect_url = reverse('user_management_manage_journal_member')
            extra_params = '?added_user=%s' % new_user.email
            full_redirect_url = '%s%s' % (redirect_url, extra_params)
            return HttpResponseRedirect(full_redirect_url)

        else:
            context.update({'form': form, 'add_error': True})
    else:
      if is_registry:
        form = create_user_form_w_registrar(prefix = "a")
      else:
        form = create_user_form(prefix="a")
      context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_journal_members.html', context)


@login_required
def manage_single_journal_member(request, user_id):
    """
    Linky admins and registrars can manage vesting members. Edit a single vesting member here.
    """

    # Only registry members and registrar memebers can edit vesting members
    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member', 'vesting_manager']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    is_registry = False;
    
    if request.user.groups.all()[0].name == 'registry_member':
      is_registry = True;
    
    target_member = get_object_or_404(LinkUser, id=user_id)

    # Registrar members can only edit their own vesting members
    if request.user.groups.all()[0].name not in ['registry_member']:
        if request.user.registrar != target_member.registrar:
            return HttpResponseRedirect(reverse('user_management_created_links'))
            
    # Vesting managers can only edit their own vesting members
    if request.user.groups.all()[0].name not in ['registry_member', 'registrar_member']:
        if request.user != target_member.authorized_by:
            return HttpResponseRedirect(reverse('user_management_created_links'))


    context = {'user': request.user, 'target_member': target_member,
        'this_page': 'users_vesting_users'}

    if request.method == 'POST':
        if is_registry:
          form = journal_member_w_group_form_edit(request.POST, prefix = "a", instance=target_member)
        else:
          form = journal_member_form_edit(request.POST, prefix = "a", instance=target_member)

        if form.is_valid():
            form.save()

            return HttpResponseRedirect(reverse('user_management_created_links'))

        else:
            context.update({'form': form,})
    else:
        if is_registry:
          form = journal_member_w_group_form_edit(prefix = "a", instance=target_member)
        else: 
          form = journal_member_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_journal_member.html', context)


@login_required
def manage_single_journal_member_delete(request, user_id):
    """
    Linky admins and registrars can manage vesting members. Delete a single vesting member here.
    """

    # Only registry members and registrar memebers can edit vesting members
    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member', 'vesting_manager']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    target_member = get_object_or_404(LinkUser, id=user_id)

    # Registrar members can only edit their own vesting members
    if request.user.groups.all()[0].name not in ['registry_member']:
        if request.user.registrar != target_member.registrar:
            return HttpResponseRedirect(reverse('user_management_created_links'))
            
    # Vesting managers can only edit their own vesting members
    if request.user.groups.all()[0].name not in ['registry_member', 'registrar_member']:
        if request.user != target_member.authorized_by:
            return HttpResponseRedirect(reverse('user_management_created_links'))

    context = {'user': request.user, 'target_member': target_member,
        'this_page': 'users_vesting_users'}

    if request.method == 'POST':
        target_member.is_active = False
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_journal_member'))
    else:
        form = journal_member_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_journal_member_delete_confirm.html', context)
    
@login_required
def manage_single_journal_member_reactivate(request, user_id):
    """
    Perma admins and registrars can manage vesting members. Reactivate a single vesting member here.
    """

    # Only registry members and registrar memebers can edit vesting members
    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member', 'vesting_manager']:
        return HttpResponseRedirect(reverse('user_management_created_links'))

    target_member = get_object_or_404(LinkUser, id=user_id)

    # Registrar members can only edit their own vesting members
    if request.user.groups.all()[0].name not in ['registry_member']:
        if request.user.registrar != target_member.registrar:
            return HttpResponseRedirect(reverse('user_management_created_links'))
            
    # Vesting managers can only edit their own vesting members
    if request.user.groups.all()[0].name not in ['registry_member', 'registrar_member']:
        if request.user != target_member.authorized_by:
            return HttpResponseRedirect(reverse('user_management_created_links'))

    context = {'user': request.user, 'target_member': target_member,
        'this_page': 'users_vesting_users'}

    if request.method == 'POST':
        target_member.is_active = True
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_journal_member'))
    else:
        form = journal_member_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage_single_journal_member_reactivate_confirm.html', context)

valid_sorts = ['-creation_timestamp', 'creation_timestamp', 'vested_timestamp', '-vested_timestamp']


@login_required
def created_links(request):
    """
    Anyone with an account can view the linky links they've created
    """

    DEFAULT_SORT = '-creation_timestamp'

    sort = request.GET.get('sort', DEFAULT_SORT)
    if sort not in valid_sorts:
        sort = DEFAULT_SORT
    page = request.GET.get('page', 1)
    if page < 1:
        page = 1

    linky_links = Link.objects.filter(created_by=request.user).order_by(sort)
    total_created = len(linky_links)

    paginator = Paginator(linky_links, 10)
    linky_links = paginator.page(page)

    for linky_link in linky_links:
        #linky_link.id =  base.convert(linky_link.id, base.BASE10, base.BASE58)
        if len(linky_link.submitted_title) > 50:
          linky_link.submitted_title = linky_link.submitted_title[:50] + '...'
        if len(linky_link.submitted_url) > 79:
          linky_link.submitted_url = linky_link.submitted_url[:70] + '...'

    context = {'user': request.user, 'linky_links': linky_links, 'host': request.get_host(),
               'total_created': total_created, sort : sort, 'this_page': 'created_links'}

    context = RequestContext(request, context)
    
    return render_to_response('user_management/created-links.html', context)


@login_required
def vested_links(request):
    """
    Linky admins and registrar members and vesting members can vest link links
    """

    if request.user.groups.all()[0].name not in ['vesting_member', 'vesting_manager', 'registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_created_links'))
        
    
    DEFAULT_SORT = '-creation_timestamp'

    sort = request.GET.get('sort', DEFAULT_SORT)
    if sort not in valid_sorts:
        sort = DEFAULT_SORT
    page = request.GET.get('page', 1)
    if page < 1:
        page = 1

    linky_links = Link.objects.filter(vested_by_editor=request.user).order_by(sort)
    total_vested = len(linky_links)
    
    paginator = Paginator(linky_links, 10)
    linky_links = paginator.page(page)

    for linky_link in linky_links:
        #linky_link.id =  base.convert(linky_link.id, base.BASE10, base.BASE58)
        if len(linky_link.submitted_title) > 50:
          linky_link.submitted_title = linky_link.submitted_title[:50] + '...'
        if len(linky_link.submitted_url) > 79:
          linky_link.submitted_url = linky_link.submitted_url[:70] + '...'

    context = {'user': request.user, 'linky_links': linky_links, 'host': request.get_host(),
               'total_vested': total_vested, 'this_page': 'vested_links'}

    context = RequestContext(request, context)
    
    return render_to_response('user_management/vested-links.html', context)


@login_required
def manage_account(request):
    """
    Account mangement stuff. Change password, change email, ...
    """

    context = {'host': request.get_host(), 'user': request.user,
        'next': request.get_full_path(), 'this_page': 'settings'}
    context.update(csrf(request))
    if request.user.groups.all()[0].name in ['vesting_member', 'vesting_manager']:
      if request.user.registrar:
        context.update({'sponsoring_library_name': request.user.registrar.name, 'sponsoring_library_email': request.user.registrar.email, 'sponsoring_library_website': request.user.registrar.website})
      else:
        context.update({'no_registrar': True})
    
    if request.method == 'POST':

        form = user_form_self_edit(request.POST, prefix = "a", instance=request.user)

        if form.is_valid():
            form.save()

            return HttpResponseRedirect(reverse('user_management_manage_account'))

        else:
            context.update({'form': form,})
    else:
        form = user_form_self_edit(prefix = "a", instance=request.user)
        context.update({'form': form,})

    context = RequestContext(request, context)
    
    return render_to_response('user_management/manage-account.html', context)


@login_required
def batch_convert(request):
    """
    Detect and archive URLs from user input.
    """
    context = {'host': request.get_host(), 'user': request.user,
        'this_page': 'batch_convert'}
    context.update(csrf(request))
    return render_to_response('user_management/batch_convert.html', context)


@login_required
def export(request):
    """
    Export a CSV of a user's library/
    """
    
    context = {'host': request.get_host(), 'user': request.user,
        'this_page': 'export'}
    context.update(csrf(request))
    return render_to_response('user_management/export.html', context)


@login_required
def custom_domain(request):
    """
    Instructions for a user to configure a custom domain.
    """
    context = {'host': request.get_host(), 'user': request.user,
        'this_page': 'custom_domain'}
    context.update(csrf(request))
    return render_to_response('user_management/custom_domain.html', context)
    
def not_active(request):
    """
    Informing a user that their account is not active.
    """
    email = request.REQUEST.get('email')
    if request.method == 'POST':
        target_user = get_object_or_404(LinkUser, email=email)
        email_new_user(request, target_user)

        redirect_url = reverse('user_management_limited_login')
        extra_params = '?resent=true'
        full_redirect_url = '%s%s' % (redirect_url, extra_params)
        return HttpResponseRedirect(full_redirect_url)
    else:
        context = {}
        context.update(csrf(request))
        return render_to_response('registration/not_active.html', context)
    

@ratelimit(field='email', method='POST', rate=settings.LOGIN_MINUTE_LIMIT, block='True', ip=True)
#@ratelimit(method='POST', rate=settings.LOGIN_HOUR_LIMIT, block='True', ip=True)
#@ratelimit(method='POST', rate=settings.LOGIN_DAY_LIMIT, block='True', ip=True)
def limited_login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    is_confirm = request.REQUEST.get('confirmed')
    is_resent = request.REQUEST.get('resent')
    request.session.set_test_cookie()

    if request.method == "POST":
        form = authentication_form(request, data=request.POST)
        username = request.POST.get('username')
        try:
          target_user = LinkUser.objects.get(email=username)
        except LinkUser.DoesNotExist:
          target_user = None
        if target_user and not target_user.is_active:
          #return HttpResponseRedirect(reverse('user_management_not_active'), request, {'id': target_user.id,})
          redirect_url = reverse('user_management_not_active')
          extra_params = '?email=%s' % target_user.email
          full_redirect_url = '%s%s' % (redirect_url, extra_params)
          return HttpResponseRedirect(full_redirect_url)
        if form.is_valid():

            # Ensure the user-originating redirection url is safe.
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())

            return HttpResponseRedirect(redirect_to)
    else:
        form = authentication_form(request)

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
        'is_confirm': is_confirm,
        'is_resent': is_resent,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)


@ratelimit(method='POST', rate=settings.REGISTER_MINUTE_LIMIT, block='True', ip=True)
#@ratelimit(method='POST', rate=settings.REGISTER_HOUR_LIMIT, block='True', ip=True)
#@ratelimit(method='POST', rate=settings.REGISTER_DAY_LIMIT, block='True', ip=True)
def process_register(request):
    """
    Register a new user
    """
    c = {}

    if request.method == 'POST':

        reg_key = request.POST.get('reg_key', '')

        editor_reg_form = user_reg_form(request.POST, prefix = "a")

        if editor_reg_form.is_valid():
            new_user = editor_reg_form.save()

            new_user.backend='django.contrib.auth.backends.ModelBackend'
            
            new_user.is_active = False
            
            new_user.save()

            group = Group.objects.get(name='user')
            new_user.groups.add(group)
            
            email_new_user(request, new_user)

            return HttpResponseRedirect(reverse('register_email_instructions'))

        else:
            c.update({'editor_reg_form': editor_reg_form,})
            
            c = RequestContext(request, c)

            return render_to_response('registration/register.html', c)
    else:
        editor_reg_form = user_reg_form (prefix = "a")

        c.update({'editor_reg_form': editor_reg_form,})
        c = RequestContext(request, c)
        return render_to_response("registration/register.html", c)


def register_email_code_confirmation(request, code):
    """
    Confirm a user's account when the user follows the email confirmation link.
    """
    user = get_object_or_404(LinkUser, confirmation_code=code)
    user.is_active = True
    user.save()
    redirect_url = reverse('user_management_limited_login')
    extra_params = '?confirmed=true'
    full_redirect_url = '%s%s' % (redirect_url, extra_params)
    return HttpResponseRedirect(full_redirect_url)
    

def register_email_code_password(request, code):
    """
    Allow system created accounts to create a password.
    """
    #user = get_or_none(LinkUser, confirmation_code=code)
    try:
      user = LinkUser.objects.get(confirmation_code=code)
    except LinkUser.DoesNotExist:
      user = None
    if not user:
      context = {'no_code': True}
      context = RequestContext(request, context)
      return render_to_response('registration/set_password.html', context)
    else:
      if request.method == "POST":
        form = set_password_form(user=user, data=request.POST)
        if form.is_valid():
          form.save()
          user.is_active = True
          user.save()
          redirect_url = reverse('user_management_limited_login')
          extra_params = '?confirmed=true'
          full_redirect_url = '%s%s' % (redirect_url, extra_params)
          return HttpResponseRedirect(full_redirect_url)
        else:
          context = {'form': form}
          context = RequestContext(request, context)
          return render_to_response('registration/set_password.html', context)
      else:
        form = set_password_form(user=user)
      
        context = {'form': form}
        context = RequestContext(request, context)
        return render_to_response('registration/set_password.html', context)
    
    
def register_email_instructions(request):
    """
    After the user has registered, give the instructions for confirming
    """
    return render_to_response('registration/check_email.html', {})
    
def email_new_user(request, user):
    """
    Send email to newly created accounts
    """
    if not user.confirmation_code:
      user.confirmation_code = \
        ''.join(random.choice(string.ascii_uppercase + \
        string.ascii_lowercase + string.digits) for x in range(30))
      user.save()
    from_address = settings.DEFAULT_FROM_EMAIL
    to_address = user.email
    content = '''To activate your account, please click the link below or copy it to your web browser.  You will need to create a new password.

http://%s/register/password/%s/

''' % (request.get_host(), user.confirmation_code)

    logger.debug(content)

    msg = MIMEText(content)
    msg['Subject'] = "A perma account has been created for you"
    msg['From'] = from_address
    msg['To'] = to_address
        
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()