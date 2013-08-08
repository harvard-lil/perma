import logging

from linky.forms import user_reg_form, regisrtar_member_form, registrar_form, journal_member_form, journal_member_form_edit, regisrtar_member_form_edit
from linky.models import Registrar, Link
from linky.utils import base

from django.contrib.auth.decorators import login_required
from django.http import  HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from django.contrib import auth
from django.contrib.auth.models import User, Permission, Group


logger = logging.getLogger(__name__)

try:
    from linky.local_settings import *
except ImportError, e:
    logger.error('Unable to load local_settings.py: %s', e)


@login_required
def landing(request):
    """ The logged-in user's dashboard. """
    # TODO: do we need this? We were using this, but it's need has
    # vanished since we moved the admin panel to the left column (on all admin pages)

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
def manage_single_registrar(request, registrar_id):
    """ Linky admins can manage registrars (libraries)
        in this view, we allow for edit/delete"""

    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    target_registrar = get_object_or_404(Registrar, id=registrar_id)

    context = {'user': request.user, 'target_registrar': target_registrar}
    context.update(csrf(request))

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

    return render_to_response('user_management/manage_single_registrar.html', context)

@login_required
def manage_registrar_member(request):
    """ Linky admins can manage registrar members (librarians) """

    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    registrar_members = User.objects.filter(groups__name='registrar_member', is_active=True)

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
def manage_single_registrar_member(request, user_id):
    """ Linky admins can manage registrar members (librarians)
        in this view, we allow for edit"""

    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    target_registrar_member = get_object_or_404(User, id=user_id)

    context = {'user': request.user, 'target_registrar_member': target_registrar_member}
    context.update(csrf(request))

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

    return render_to_response('user_management/manage_single_registrar_member.html', context)

@login_required
def manage_single_registrar_member_delete(request, user_id):
    """ Linky admins can manage registrar members. Delete a single registrar member here. """

    # Only registry members can delete registrar members
    if request.user.groups.all()[0].name not in ['registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    target_member = get_object_or_404(User, id=user_id)

    context = {'user': request.user, 'target_member': target_member}
    context.update(csrf(request))

    if request.method == 'POST':
        target_member.is_active = False
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_registrar_member'))
    else:
        form = journal_member_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    return render_to_response('user_management/manage_single_registrar_member_delete_confirm.html', context)

@login_required
def manage_journal_member(request):
    """ Linky admins and registrars can manage journal members """

    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    # If registry member, return all active journal members. If registrar member, return just those journal members that belong to the registrar member's registrar
    if request.user.groups.all()[0].name == 'registry_member':
        journal_members = User.objects.filter(groups__name='journal_member', is_active=True)
    else:
        journal_members = User.objects.filter(userprofile__registrar=request.user.userprofile.registrar, is_active=True).exclude(id=request.user.id)

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
def manage_single_journal_member(request, user_id):
    """ Linky admins and registrars can manage journal members. Edit a single journal member here. """

    # Only registry members and registrar memebers can edit journal members
    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    target_member = get_object_or_404(User, id=user_id)

    # Registrar members can only edit their own journal members
    if request.user.groups.all()[0].name not in ['registry_member']:
        if request.user.get_profile().registrar != target_member.get_profile().registrar:
            return HttpResponseRedirect(reverse('user_management_landing'))


    context = {'user': request.user, 'target_member': target_member}
    context.update(csrf(request))

    if request.method == 'POST':

        form = journal_member_form_edit(request.POST, prefix = "a", instance=target_member)

        if form.is_valid():
            form.save()

            return HttpResponseRedirect(reverse('user_management_manage_journal_member'))

        else:
            context.update({'form': form,})
    else:
        form = journal_member_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    return render_to_response('user_management/manage_single_journal_member.html', context)


@login_required
def manage_single_journal_member_delete(request, user_id):
    """ Linky admins and registrars can manage journal members. Delete a single journal member here. """

    # Only registry members and registrar memebers can edit journal members
    if request.user.groups.all()[0].name not in ['registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    target_member = get_object_or_404(User, id=user_id)

    # Registrar members can only edit their own journal members
    if request.user.groups.all()[0].name not in ['registry_member']:
        if request.user.get_profile().registrar != target_member.get_profile().registrar:
            return HttpResponseRedirect(reverse('user_management_landing'))

    context = {'user': request.user, 'target_member': target_member}
    context.update(csrf(request))

    if request.method == 'POST':
        target_member.is_active = False
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_journal_member'))
    else:
        form = journal_member_form_edit(prefix = "a", instance=target_member)
        context.update({'form': form,})

    return render_to_response('user_management/manage_single_journal_member_delete_confirm.html', context)


@login_required
def created_links(request):
    """ Anyone with an account can view the linky links they've created """

    DEFAULT_SORT = '-creation_timestamp'

    sort = request.GET.get('sort', DEFAULT_SORT)

    #linky_links = list(Link.objects.filter(created_by=request.user).order_by('-creation_timestamp'))
    linky_links = Link.objects.filter(created_by=request.user).order_by(sort)

    for linky_link in linky_links:
        linky_link.id =  base.convert(linky_link.id, base.BASE10, base.BASE58)

    context = {'user': request.user, 'linky_links': linky_links, 'host': request.get_host(),
               'total_created': len(linky_links)}

    return render_to_response('user_management/created-links.html', context)

@login_required
def vested_links(request):
    """ Linky admins and registrar members and journal members can vest link links """

    if request.user.groups.all()[0].name not in ['journal_member', 'registrar_member', 'registry_member']:
        return HttpResponseRedirect(reverse('user_management_landing'))

    linky_links = list(Link.objects.filter(vested_by_editor=request.user).order_by('-vested_timestamp'))

    for linky_link in linky_links:
        linky_link.id =  base.convert(linky_link.id, base.BASE10, base.BASE58)

    context = {'user': request.user, 'linky_links': linky_links, 'host': request.get_host(),
               'total_vested': len(linky_links)}

    return render_to_response('user_management/vested-links.html', context)

@login_required
def manage_account(request):
    """ Account mangement stuff. Change password, change email, ... """

    context = {'host': request.get_host(), 'user': request.user, 'next': request.get_full_path()}
    context.update(csrf(request))

    return render_to_response('user_management/manage-account.html', context)

@login_required
def sponsoring_library(request):
    """ Journal members can view their sponsoring library (for contact info) """

    profile = request.user.get_profile()

    context = {'user': request.user, 'sponsoring_library_name': profile.registrar.name, 'sponsoring_library_email': profile.registrar.email, 'sponsoring_library_website': profile.registrar.website}

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
