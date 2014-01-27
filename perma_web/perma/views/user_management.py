import random, string, smtplib, logging, json
from email.mime.text import MIMEText

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import get_current_site
from django.db.models import Q
from django.utils.http import is_safe_url
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.shortcuts import render_to_response, get_object_or_404, resolve_url
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from django.core.paginator import Paginator
from django.contrib.auth.models import Group
from django.contrib import messages
from mptt.exceptions import InvalidMove
from ratelimit.decorators import ratelimit

from perma.forms import user_reg_form, registrar_form, vesting_manager_form_edit, vesting_manager_w_group_form_edit, vesting_member_form_edit, vesting_member_w_group_form_edit, registrar_member_form_edit, user_form_self_edit, user_form_edit, set_password_form, create_user_form, create_user_form_w_registrar, vesting_org_w_registrar_form, create_user_form_w_vesting_org, vesting_member_w_vesting_org_form_edit, vesting_org_form, user_add_registrar_form, user_add_vesting_org_form
from perma.models import Registrar, Link, LinkUser, VestingOrg, Folder
from perma.utils import require_group

logger = logging.getLogger(__name__)
valid_member_sorts = ['-email', 'email', 'last_name', '-last_name', 'admin', '-admin', 'registrar__name', '-registrar__name', 'vesting_org__name', '-vesting_org__name']
valid_registrar_sorts = ['-email', 'email', 'name', '-name', 'website', '-website']
valid_link_sorts = ['-creation_timestamp', 'creation_timestamp', 'vested_timestamp', '-vested_timestamp', 'submitted_title', '-submitted_title']


@login_required
def manage(request):
    """
    The landing page for users who are signed in
    """

    if request.user.id >= 0:
      linky_links = list(Link.objects.filter(created_by=request.user).order_by('-creation_timestamp'))
    else:
      linky_links = None

    context = RequestContext(request, {'this_page': 'manage', 'user': request.user, 'linky_links': linky_links, 'next': request.get_full_path()})

    return render_to_response('user_management/manage.html', context)
    
@login_required
def create_link(request):
    """
    Create new links
    """

    if request.user.id >= 0:
      linky_links = list(Link.objects.filter(created_by=request.user).order_by('-creation_timestamp'))
    else:
      linky_links = None

    context = RequestContext(request, {'this_page': 'create_link', 'user': request.user, 'linky_links': linky_links, 'next': request.get_full_path()})

    return render_to_response('user_management/create-link.html', context)
    

@require_group('registry_member')
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


@require_group('registry_member')
def manage_single_registrar(request, registrar_id):
    """ Linky admins can manage registrars (libraries)
        in this view, we allow for edit/delete """

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
    
@require_group(['registry_member', 'registrar_member'])
def manage_vesting_org(request):
    """
    Registry and registrar members can manage vesting organizations (journals)
    """

    DEFAULT_SORT = 'name'
    is_registry = False

    sort = request.GET.get('sort', DEFAULT_SORT)
    if sort not in valid_registrar_sorts:
      sort = DEFAULT_SORT
      
    page = request.GET.get('page', 1)
    if page < 1:
        page = 1
        
    # If registry member, return all active vesting members. If registrar member, return just those vesting members that belong to the registrar member's registrar
    if request.user.groups.all()[0].name == 'registry_member':
        vesting_orgs = VestingOrg.objects.all().order_by(sort)
        is_registry = True;
    else:
      vesting_orgs = VestingOrg.objects.filter(registrar_id=request.user.registrar_id).order_by(sort)
    
    paginator = Paginator(vesting_orgs, settings.MAX_USER_LIST_SIZE)
    vesting_orgs = paginator.page(page)

    context = {'user': request.user, 'vesting_orgs_list': list(vesting_orgs), 'vesting_orgs': vesting_orgs,
        'this_page': 'users_vesting_orgs'}

    if request.method == 'POST':

        if is_registry:
          form = vesting_org_w_registrar_form(request.POST, prefix = "a")
        else:
          form = vesting_org_form(request.POST, prefix = "a")

        if form.is_valid():
            new_user = form.save()
            if not is_registry:
              new_user.registrar_id = request.user.registrar_id
              new_user.save()

            return HttpResponseRedirect(reverse('user_management_manage_vesting_org'))

        else:
            context.update({'form': form, 'add_error': True})
    else:
        if is_registry:
            form = vesting_org_w_registrar_form(prefix = "a")
        else:
            form = vesting_org_form(prefix = "a")
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/manage_vesting_orgs.html', context)


@require_group(['registrar_member', 'registry_member'])
def manage_single_vesting_org(request, vesting_org_id):
    """ Registry and registrar members can manage vesting organizations (journals)
        in this view, we allow for edit/delete """

    target_vesting_org = get_object_or_404(VestingOrg, id=vesting_org_id)

    context = {'user': request.user, 'target_vesting_org': target_vesting_org,
        'this_page': 'users_vesting_orgs'}

    if request.method == 'POST':

        form = vesting_org_form(request.POST, prefix = "a", instance=target_vesting_org)

        if form.is_valid():
            new_user = form.save()
            
            return HttpResponseRedirect(reverse('user_management_manage_vesting_org'))

        else:
            context.update({'form': form,})
    else:
        form = vesting_org_form(prefix = "a", instance=target_vesting_org)
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/manage_single_vesting_org.html', context)



@require_group('registry_member')
def manage_registrar_member(request):
    return list_users_in_group(request, 'registrar_member')

@require_group('registry_member')
def manage_single_registrar_member(request, user_id):
    return edit_user_in_group(request, user_id, 'registrar_member')

@require_group('registry_member')
def manage_single_registrar_member_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'registrar_member')
    
@require_group('registry_member')
def manage_single_registrar_member_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'registrar_member')



@require_group('registry_member')
def manage_user(request):
    return list_users_in_group(request, 'user')

@require_group('registry_member')
def manage_single_user(request, user_id):
    return edit_user_in_group(request, user_id, 'user')

@require_group('registry_member')
def manage_single_user_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'user')

@require_group('registry_member')
def manage_single_user_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'user')



@require_group(['registrar_member', 'registry_member'])
def manage_vesting_manager(request):
    return list_users_in_group(request, 'vesting_manager')

@require_group(['registrar_member', 'registry_member'])
def manage_single_vesting_manager(request, user_id):
    return edit_user_in_group(request, user_id, 'vesting_manager')

@require_group(['registrar_member', 'registry_member'])
def manage_single_vesting_manager_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'vesting_manager')

@require_group(['registrar_member', 'registry_member'])
def manage_single_vesting_manager_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'vesting_manager')



@require_group(['registrar_member', 'registry_member', 'vesting_manager'])
def manage_vesting_member(request):
    return list_users_in_group(request, 'vesting_member')

@require_group(['registrar_member', 'registry_member', 'vesting_manager'])
def manage_single_vesting_member(request, user_id):
    return edit_user_in_group(request, user_id, 'vesting_member')

@require_group(['registrar_member', 'registry_member', 'vesting_manager'])
def manage_single_vesting_member_delete(request, user_id):
    return delete_user_in_group(request, user_id, 'vesting_member')

@require_group(['registrar_member', 'registry_member', 'vesting_manager'])
def manage_single_vesting_member_reactivate(request, user_id):
    return reactive_user_in_group(request, user_id, 'vesting_member')



def list_users_in_group(request, group_name):
    """
        Show list of users with given group name.
    """

    is_registry = False
    is_registrar = False
    added_user = request.REQUEST.get('added_user')

    def sorts():
        DEFAULT_SORT = ['email']
        sorts = DEFAULT_SORT

        sort = request.GET.get('sort', DEFAULT_SORT)
        print sort
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

    users = None
    if request.user.has_group('registry_member'):
        users = LinkUser.objects.filter(groups__name=group_name).order_by(*sorts())
        is_registry = True
    elif request.user.has_group('registrar_member'):
        users = LinkUser.objects.filter(groups__name=group_name, registrar=request.user.registrar).exclude(id=request.user.id).order_by(*sorts())
        is_registrar = True
    elif request.user.has_group('vesting_manager'):
        users = LinkUser.objects.filter(vesting_org=request.user.vesting_org).exclude(id=request.user.id).order_by(*sorts())

    paginator = Paginator(users, settings.MAX_USER_LIST_SIZE)
    users = paginator.page(page)

    context = {
        'user': request.user,
        'users_list': list(users),
        'this_page': 'users_{group_name}s'.format(group_name=group_name),
        'users': users,
        'added_user': added_user,
        'group_name':group_name,
        'pretty_group_name':group_name.replace('_', ' ').capitalize(),
        'user_list_url':'user_management_manage_{group_name}'.format(group_name=group_name),
        'reactivate_user_url':'user_management_manage_single_{group_name}_reactivate'.format(group_name=group_name),
        'single_user_url':'user_management_manage_single_{group_name}'.format(group_name=group_name),
        'delete_user_url':'user_management_manage_single_{group_name}_delete'.format(group_name=group_name),
        'sort': sorts()[0],
    }
    context['pretty_group_name_plural'] = context['pretty_group_name'] + "s"

    form = None
    form_data = request.POST or None
    if group_name == 'registrar_member':
        form = create_user_form_w_registrar(form_data, prefix="a")
    elif group_name in ('vesting_member','vesting_manager'):
        if is_registry:
            form = create_user_form_w_vesting_org(form_data, prefix="a")
        elif is_registrar:
            form = create_user_form_w_vesting_org(form_data, prefix="a", registrar_id=request.user.registrar_id)
    if not form:
        form = create_user_form(form_data, prefix = "a")

    if request.method == 'POST':

        if form.is_valid():
            new_user = form.save()

            new_user.backend='django.contrib.auth.backends.ModelBackend'

            new_user.is_active = False

            if group_name == 'vesting_member':
                new_user.authorized_by = request.user

            if group_name in ('vesting_member','vesting_manager'):
                if is_registry or is_registrar:
                    vesting_org = VestingOrg.objects.get(id=new_user.vesting_org_id)
                    new_user.registrar_id = vesting_org.registrar.id
                else:
                    new_user.vesting_org_id = request.user.vesting_org_id
                    new_user.registrar_id = request.user.registrar_id

            new_user.save()

            group = Group.objects.get(name=group_name)
            new_user.groups.add(group)

            email_new_user(request, new_user)

            messages.add_message(request, messages.INFO, '<h4>Account created!</h4> <strong>%s</strong> will receive an email with instructions on how to activate the account and create a password.' % new_user.email, extra_tags='safe')
            return HttpResponseRedirect(reverse(context['user_list_url']))

        else:
            context['add_error'] = True

    context['form'] = form

    context = RequestContext(request, context)

    return render_to_response('user_management/manage_users.html', context)


def edit_user_in_group(request, user_id, group_name):
    """
        Edit particular user with given group name.
    """

    is_registrar = request.user.has_group('registrar_member')
    is_registry = request.user.has_group('registry_member')

    target_user = get_object_or_404(LinkUser, id=user_id)

    # Registrar members can only edit their own vesting members
    if not is_registry:
        if request.user.registrar != target_user.registrar:
            return HttpResponseRedirect(reverse('user_management_created_links'))

    # Vesting managers can only edit their own vesting members
    if not is_registry and not is_registrar:
        if request.user.vesting_org != target_user.vesting_org:
            return HttpResponseRedirect(reverse('user_management_created_links'))

    context = {
        'user': request.user,
        'target_user': target_user,
        'this_page': 'users_{group_name}s'.format(group_name=group_name),
        'pretty_group_name':group_name.replace('_', ' ').capitalize(),
        'user_list_url':'user_management_manage_{group_name}'.format(group_name=group_name),
        'delete_user_url':'user_management_manage_single_{group_name}_delete'.format(group_name=group_name),
    }

    form = None
    form_data = request.POST or None
    if group_name == 'registrar_member':
        form = registrar_member_form_edit(form_data, prefix="a", instance=target_user)
    elif group_name in ('vesting_member', 'vesting_manager'):
        if is_registry:
            form = vesting_member_w_group_form_edit(form_data, prefix="a", instance=target_user,
                                                    registrar_id=target_user.registrar_id)
        elif is_registrar:
            form = vesting_member_w_vesting_org_form_edit(form_data, prefix="a", instance=target_user,
                                                          registrar_id=request.user.registrar_id)
        else:
            form = vesting_member_form_edit(form_data, prefix="a", instance=target_user)
    else:
        form = user_form_edit(form_data, prefix="a", instance=target_user)

    if request.method == 'POST':

        if form.is_valid():
            form.save()    
            
            if group_name == 'user' and group_name != form.cleaned_data['group'].name:
                request.session['old_group'] = group_name
                if form.cleaned_data['group'].name == 'registrar_member':
                    return HttpResponseRedirect(reverse('user_management_user_add_registrar', kwargs={'user_id' : user_id}))
                elif form.cleaned_data['group'].name in ('vesting_member', 'vesting_manager'):
                    return HttpResponseRedirect(reverse('user_management_user_add_vesting_org', kwargs={'user_id' : user_id}))

            return HttpResponseRedirect(reverse(context['user_list_url']))

    context['form'] = form

    context = RequestContext(request, context)

    return render_to_response('user_management/manage_single_user.html', context)

def delete_user_in_group(request, user_id, group_name):
    """
        Delete particular user with given group name.
    """

    target_member = get_object_or_404(LinkUser, id=user_id)

    # Registrar members can only edit their own vesting members
    if not request.user.has_group('registry_member'):
        if request.user.registrar != target_member.registrar:
            return HttpResponseRedirect(reverse('user_management_created_links'))

    # Vesting managers can only edit their own vesting members
    if not request.user.has_group(['registry_member', 'registrar_member']):
        if request.user != target_member.authorized_by:
            return HttpResponseRedirect(reverse('user_management_created_links'))

    context = {'user': request.user, 'target_member': target_member,
               'this_page': 'users_{group_name}s'.format(group_name=group_name)}

    if request.method == 'POST':
        if target_member.is_confirmed:
            target_member.is_active = False
            target_member.save()
        else:
            target_member.delete()

        return HttpResponseRedirect(reverse('user_management_manage_{group_name}'.format(group_name=group_name)))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_delete_confirm.html', context)



def reactive_user_in_group(request, user_id, group_name):
    """
        Reactivate particular user with given group name.
    """

    target_member = get_object_or_404(LinkUser, id=user_id)

    # Registrar members can only edit their own vesting members
    if not request.user.has_group('registry_member'):
        if request.user.registrar != target_member.registrar:
            return HttpResponseRedirect(reverse('user_management_created_links'))

    # Vesting managers can only edit their own vesting members
    if not request.user.has_group(['registry_member', 'registrar_member']):
        if request.user != target_member.authorized_by:
            return HttpResponseRedirect(reverse('user_management_created_links'))

    context = {'user': request.user, 'target_member': target_member,
               'this_page': 'users_{group_name}s'.format(group_name=group_name)}

    if request.method == 'POST':
        target_member.is_active = True
        target_member.save()

        return HttpResponseRedirect(reverse('user_management_manage_{group_name}'.format(group_name=group_name)))

    context = RequestContext(request, context)

    return render_to_response('user_management/user_reactivate_confirm.html', context)


@require_group(['registry_member'])
def user_add_registrar(request, user_id):
    target_user = get_object_or_404(LinkUser, id=user_id)
    group_name = target_user.groups.all()[0].name
    old_group = request.session.get('old_group','')
    
    context = {'user': request.user, 'this_page': 'users_{old_group}s'.format(old_group=old_group)}
    
    if request.method == 'POST':
        form = user_add_registrar_form(request.POST, prefix = "a")

        if form.is_valid():
            target_user.registrar = form.cleaned_data['registrar']
            target_user.save()
            messages.add_message(request, messages.INFO, '<strong>%s</strong> is now a <strong>%s</strong>' % (target_user.email, group_name.replace('_', ' ').capitalize()), extra_tags='safe')

            return HttpResponseRedirect(reverse('user_management_manage_{old_group}'.format(old_group=old_group)))

    else:
        form = user_add_registrar_form(prefix = "a")
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/user_add_registrar.html', context)
    
    
@require_group(['registry_member'])
def user_add_vesting_org(request, user_id):
    target_user = get_object_or_404(LinkUser, id=user_id)
    group_name = target_user.groups.all()[0].name
    old_group = request.session.get('old_group','')
    
    context = {'user': request.user, 'this_page': 'users_{old_group}s'.format(old_group=old_group)}
    
    if request.method == 'POST':
        form = user_add_vesting_org_form(request.POST, prefix = "a")

        if form.is_valid():
            target_user.vesting_org = form.cleaned_data['vesting_org']
            target_vesting_org = VestingOrg.objects.get(name=target_user.vesting_org)
            target_user.registrar = target_vesting_org.registrar
            target_user.save()
            messages.add_message(request, messages.INFO, '<strong>%s</strong> is now a <strong>%s</strong>' % (target_user.email, group_name.replace('_', ' ').capitalize()), extra_tags='safe')

            return HttpResponseRedirect(reverse('user_management_manage_{old_group}'.format(old_group=old_group)))

    else:
        form = user_add_vesting_org_form(prefix = "a")
        context.update({'form': form,})
    
    context = RequestContext(request, context)

    return render_to_response('user_management/user_add_vesting_org.html', context)
    


@login_required
def created_links(request, path):
    """
    Anyone with an account can view the linky links they've created
    """
    return link_browser(request, path,
                        link_filter={'created_by':request.user},
                        this_page='created_links',
                        verb='created')


@require_group(['registrar_member', 'registry_member', 'vesting_manager', 'vesting_member'])
def vested_links(request, path):
    """
    Linky admins and registrar members and vesting members can vest links
    """
    return link_browser(request, path,
                        link_filter={'vested_by_editor': request.user},
                        this_page='vested_links',
                        verb='vested')


def link_browser(request, path, link_filter, this_page, verb):
    """ Display a set of links with the given filter (created by or vested by user). """

    # find current folder based on path
    current_folder = None
    folder_breadcrumbs = []
    if path:
        path = path.strip("/")
        if path:
            # get current folder
            folder_slugs = path.split("/")
            current_folder = get_object_or_404(Folder,slug=folder_slugs[-1],created_by=request.user)

            # check ancestor slugs and generate breadcrumbs
            ancestors = current_folder.get_ancestors()
            for i, ancestor in enumerate(ancestors):
                if folder_slugs[i] != ancestor.slug:
                    raise Http404
                folder_breadcrumbs.append([ancestor, u"/".join(folder_slugs[:i+1])])

    # make sure path has leading and trailing slashes, or is just one slash if empty
    path = u"/%s/" % path if path else "/"

    # handle forms
    if request.POST:

        # new folder
        if 'new_folder_submit' in request.POST:
            if 'new_folder_name' in request.POST:
                Folder(name=request.POST['new_folder_name'], created_by=request.user, parent=current_folder).save()

        # move link
        elif 'move_selected_items_to' in request.POST:
            if request.POST['move_selected_items_to'] == 'ROOT':
                target_folder=None
            else:
                target_folder = get_object_or_404(Folder, created_by=request.user, pk=request.POST['move_selected_items_to'])
            for link_id in request.POST.getlist('links'):
                link = get_object_or_404(Link, pk=link_id, **link_filter)
                link.move_to_folder_for_user(target_folder, request.user)
            for folder_id in request.POST.getlist('folders'):
                folder = get_object_or_404(Folder, pk=folder_id, created_by=request.user)
                folder.parent=target_folder
                try:
                    folder.save()
                except InvalidMove:
                    # can't move a folder under itself
                    continue
            if request.is_ajax():
                return HttpResponse(json.dumps({'success': 1}), content_type="application/json")

        elif request.is_ajax():
            posted_data = json.loads(request.body)
            out = {'success': 1}

            # rename folder
            if posted_data['action'] == 'rename_folder':
                current_folder.name = posted_data['name']
                current_folder.save()

            # delete folder
            elif posted_data['action'] == 'delete_folder':
                if current_folder.is_empty():
                    current_folder.delete()
                else:
                    out = {'error':"Folders can only be deleted if they are empty."}

            # save notes
            elif posted_data['action'] == 'save_notes':
                link = get_object_or_404(Link, pk=posted_data['link_id'], **link_filter)
                link.notes = posted_data['notes']
                link.save()

            return HttpResponse(json.dumps(out), content_type="application/json")

    # start with all links belonging to user
    linky_links = Link.objects.filter(**link_filter)

    # handle search
    search_query = request.GET.get('q', None)
    if search_query:
        linky_links = linky_links.filter(
            Q(guid__icontains=search_query) |
            Q(submitted_url__icontains=search_query) |
            Q(submitted_title__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
        if current_folder:
            # limit search to current folder
            linky_links = linky_links.filter(folders__in=current_folder.get_descendants(include_self=True))

    elif current_folder:
        # limit links to current folder
        linky_links = linky_links.filter(folders=current_folder)

    else:
        # top level -- find links with no related folder for this user
        linky_links = linky_links.exclude(folders__created_by=request.user)

    # handle sorting
    DEFAULT_SORT = '-creation_timestamp'
    sort = request.GET.get('sort', DEFAULT_SORT)
    if sort not in valid_link_sorts:
        sort = DEFAULT_SORT
    linky_links = linky_links.order_by(sort)

    # handle pagination
    # page = request.GET.get('page', 1)
    # if page < 1:
    #     page = 1
    # paginator = Paginator(linky_links, 10)
    # linky_links = paginator.page(page)

    subfolders = list(Folder.objects.filter(created_by=request.user, parent=current_folder))
    all_folders = Folder.objects.filter(created_by=request.user)
    base_url = reverse('user_management_'+this_page)
    link_count = Link.objects.filter(**link_filter).count()

    context = {'user': request.user, 'linky_links': linky_links, 'link_count':link_count,
               'sort': sort, 'search_query':search_query, 'this_page': this_page, 'verb': verb,
               'subfolders':subfolders, 'path':path, 'folder_breadcrumbs':folder_breadcrumbs,
               'current_folder':current_folder,
               'all_folders':all_folders,
               'base_url':base_url}

    context = RequestContext(request, context)
    
    return render_to_response('user_management/created-links.html', context)


@login_required
def manage_account(request):
    """
    Account management stuff. Change password, change email, ...
    """

    context = {'user': request.user,
        'next': request.get_full_path(), 'this_page': 'settings'}
    context.update(csrf(request))
    if request.user.has_group(['vesting_member', 'vesting_manager']):
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
    context = {'user': request.user,
        'this_page': 'batch_convert'}
    context.update(csrf(request))
    return render_to_response('user_management/batch_convert.html', context)


@login_required
def export(request):
    """
    Export a CSV of a user's library/
    """
    
    context = {'user': request.user,
        'this_page': 'export'}
    context.update(csrf(request))
    return render_to_response('user_management/export.html', context)


@login_required
def custom_domain(request):
    """
    Instructions for a user to configure a custom domain.
    """
    context = {'user': request.user,
        'this_page': 'custom_domain'}
    context.update(csrf(request))
    return render_to_response('user_management/custom_domain.html', context)
    
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
        return render_to_response('registration/not_active.html', context)
        
        
def account_is_deactivated(request):
    """
    Informing a user that their account has been deactivated.
    """
    return render_to_response('user_management/deactivated.html')
    

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

            return HttpResponseRedirect(redirect_to)
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
    user.is_confirmed = True
    user.save()
    messages.add_message(request, messages.INFO, 'Your account is activated.  Log in below.')
    #redirect_url = reverse('user_management_limited_login')
    #extra_params = '?confirmed=true'
    #full_redirect_url = '%s%s' % (redirect_url, extra_params)
    return HttpResponseRedirect(reverse('user_management_limited_login'))
    

def register_email_code_password(request, code):
    """
    Allow system created accounts to create a password.
    """
    
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
            user.is_confirmed = True
            user.save()
            messages.add_message(request, messages.INFO, 'Your account is activated.  Log in below.')
            return HttpResponseRedirect(reverse('user_management_limited_login'))
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
      
    host = request.get_host()

    if settings.DEBUG == False:
      host = settings.HOST
      
    from_address = settings.DEFAULT_FROM_EMAIL
    to_address = user.email
    content = '''To activate your account, please click the link below or copy it to your web browser.  You will need to create a new password.

http://%s/register/password/%s/

''' % (host, user.confirmation_code)

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
