import logging

from linky.forms import user_reg_form, regisrtar_member_form, registrar_form, journal_member_form
from linky.models import Registrar, Link

from django.contrib.auth.decorators import login_required
from django.http import  HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from django.contrib import auth
from django.contrib.auth.models import User, Permission, Group


logger = logging.getLogger(__name__)

try:
    from linky.local_settings import *
except ImportError, e:
    logger.error('Unable to load local_settings.py:', e)


@login_required
def landing(request):
    """ The logged-in user's dashboard """
    
    context = {'user': request.user}

    return render_to_response('user_management/landing.html', context)
    
@login_required
def manage_members(request):
    """ registry and registrar members can manage journal members (the folks that vest links) """
    
    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))
    
    context = {'user': request.user, 'registrar_members': list(registrars)}
    context.update(csrf(request))

    if request.method == 'POST':

        form = regisrtar_member_form(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save()

            new_user.backend='django.contrib.auth.backends.ModelBackend'

            group = Group.objects.get(name='registrar_member')
            group.user_set.add(new_user)

            return HttpResponseRedirect(reverse('user_management_manage_registrar_member'))

        else:
            context.update({'regisrtar_register_form': form,})                      
    else:
        form = regisrtar_member_form(prefix = "a")
        context.update({'regisrtar_register_form': form,}) 

    return render_to_response('user_management/manage_registrar_members.html', context)
    
@login_required
def manage_registrar(request):
    """ Linky admins can manage registrars (libraries) """

    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    # TODO: support paging at some point
    registrars = Registrar.objects.all()[:500]

    context = {'user': request.user, 'registrars': list(registrars)}
    context.update(csrf(request))
    
    if request.method == 'POST':

        form = registrar_form(request.POST, prefix = "a")
        
        if form.is_valid():
            new_user = form.save()
            
            return HttpResponseRedirect(reverse('user_management_manage_registrar'))
        
        else:
            context.update({'form': form,})                      
    else:
        form = registrar_form(prefix = "a")
        context.update({'form': form,}) 

    return render_to_response('user_management/manage_registrars.html', context)
    
@login_required
def manage_registrar_member(request):
    """ Linky admins can manage registrar members (librarians) """

    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    if request.user.groups.all()[0].name == "registry_member":
        registrar_members = User.objects.filter(groups__name='registrar_member')
    elif request.user.groups.all()[0].name == "registrar_member":
        profile = request.user.get_profile()
        registrar_members = User.objects.filter(userprofile__registrar=profile.registrar)
    else:
        return HttpResponseRedirect(reverse('user_management_landing'))

    context = {'user': request.user, 'registrar_members': list(registrar_members)}
    context.update(csrf(request))
    
    if request.method == 'POST':

        form = regisrtar_member_form(request.POST, prefix = "a")
        
        if form.is_valid():
            new_user = form.save()

            new_user.backend='django.contrib.auth.backends.ModelBackend'

            group = Group.objects.get(name='registrar_member')
            group.user_set.add(new_user)
            
            return HttpResponseRedirect(reverse('user_management_manage_registrar_member'))
        
        else:
            context.update({'form': form,})                      
    else:
        form = regisrtar_member_form(prefix = "a")
        context.update({'form': form,})

    return render_to_response('user_management/manage_registrar_members.html', context)
    
@login_required
def manage_journal_member(request):
    """ Linky admins and registrars can manage journal members """

    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    journal_members = User.objects.filter(groups__name='journal_member')

    context = {'user': request.user, 'journal_members': list(journal_members)}
    context.update(csrf(request))

    if request.method == 'POST':

        form = journal_member_form(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save()

            new_user.backend='django.contrib.auth.backends.ModelBackend'

            group = Group.objects.get(name='journal_member')
            group.user_set.add(new_user)
            
            
            logged_in_user_profile = request.user.get_profile()
            
            new_user_profile = new_user.get_profile()
            new_user_profile.registrar = logged_in_user_profile.registrar
            new_user_profile.save()

            return HttpResponseRedirect(reverse('user_management_manage_journal_member'))

        else:
            context.update({'form': form,})                      
    else:
        form = journal_member_form(prefix = "a")
        context.update({'form': form,})

    return render_to_response('user_management/manage_journal_members.html', context)
    
@login_required
def manage_links(request):
    """ Linky admins and registrar members and journal members can vest link links """

    if request.user.groups.all()[0].name not in ['journal_member', 'registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    linky_links = Link.objects.filter(vested_by_editor=request.user)
    
    context = {'user': request.user, 'linky_links': list(linky_links), 'host': request.get_host()}

    return render_to_response('user_management/links.html', context)
    
@login_required
def manage_account(request):
    """ Account mangement stuff. Change password, change email, ... """

    context = {'user': request.user, }

    return render_to_response('user_management/manage-account.html', context)


@login_required
def sponsoring_library(request):
    """ Journal members can view their sponsoring library (for contact info) """

    profile = request.user.get_profile()

    context = {'user': request.user, 'sponsoring_library_name': profile.registrar.name}

    return render_to_response('user_management/sponsoring-library.html', context)


def process_register(request):
    """Register a new user"""
    c = {}
    c.update(csrf(request))

    if request.method == 'POST':

        reg_key = request.POST.get('reg_key', '')
                
        editor_reg_form = user_reg_form(request.POST, prefix = "a")
        
        if editor_reg_form.is_valid():
            new_user = editor_reg_form.save()
            
            new_user.backend='django.contrib.auth.backends.ModelBackend'

            group = Group.objects.get(name='user')
            group.user_set.add(new_user)
            
            return HttpResponseRedirect(reverse('landing'))
        
        else:
            c.update({'editor_reg_form': editor_reg_form,})
                      
            return render_to_response('registration/register.html', c)
    else:
        editor_reg_form = user_reg_form (prefix = "a")
        
        c.update({'editor_reg_form': editor_reg_form,})
        return render_to_response("registration/register.html", c)