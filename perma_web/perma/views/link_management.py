import imghdr
import logging, json, os
from datetime import datetime
import socket
from urlparse import urlparse
from mimetypes import MimeTypes
from celery import chain
from django.db import transaction
from django.contrib import messages
from netaddr import IPAddress, IPNetwork
import requests
from PyPDF2 import PdfFileReader

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import HttpResponse, render_to_response, get_object_or_404, render
from django.template import RequestContext

from ..models import Link, Asset, Folder, VestingOrg, FolderException
from ..tasks import get_pdf, proxy_capture, upload_to_internet_archive
from ..utils import require_group, run_task


logger = logging.getLogger(__name__)
valid_link_sorts = ['-creation_timestamp', 'creation_timestamp', 'vested_timestamp', '-vested_timestamp', 'submitted_title', '-submitted_title']

HEADER_CHECK_TIMEOUT = 10  # seconds to wait before giving up when checking headers for requested link


###### LINK CREATION ######

@login_required
def create_link(request):
    return render(request, 'user_management/create-link.html', {
        'this_page': 'create_link',
    })


###### LINK BROWSING ######

@login_required
def link_browser(request, path):
    """ Display links created by or vested by user, or attached to user's vesting org. """

    # handle updates to individual links
    if request.POST:
        out = {'success': 1}
        action = request.POST.get('action')

        # save notes/title
        if action == 'save_link_attribute':
            if request.POST.get('name') not in ['notes', 'submitted_title']:
                return HttpResponseBadRequest("Attribute not recognized.")
            link = get_object_or_404(Link, Link.objects.user_access_filter(request.user), pk=request.POST['link_id'])
            setattr(link, request.POST['name'], request.POST['value'])
            link.save()

        else:
            return HttpResponseBadRequest("Action not recognized.")

        return HttpResponse(json.dumps(out), content_type="application/json")

    return render(request, 'user_management/created-links.html', {
        'this_page': 'link_browser',
    })

@login_required
def folder_contents(request, folder_id):
    # helper vars
    user = request.user
    folder_access_filter = Folder.objects.user_access_filter(user)
    link_access_filter = Link.objects.user_access_filter(user)

    current_folder = get_object_or_404(Folder, folder_access_filter, pk=folder_id)

    # handle forms
    if request.POST:
        class BadRequest(Exception):
            pass

        out = {'success': 1}

        # we wrap all the edits in a try/except and a transaction, so we can roll back everything if we hit an error
        try:
            with transaction.atomic():
                action = request.POST.get('action')

                # move items
                if action == 'move_items':
                    # move links
                    for link_id in request.POST.getlist('links'):
                        link = get_object_or_404(Link, link_access_filter, pk=link_id)
                        if link.vested and link.vesting_org != current_folder.vesting_org:
                            raise BadRequest("Can't move vested link out of organization's shared folder.")
                        link.move_to_folder_for_user(current_folder, user)

                    # move folders
                    for folder_id in request.POST.getlist('folders'):
                        folder = get_object_or_404(Folder, folder_access_filter, pk=folder_id)
                        try:
                            folder.move_to_folder(current_folder)
                        except FolderException as e:
                            raise BadRequest(e.message)

                # new folder
                elif action == 'new_folder':
                    new_folder = Folder(name=request.POST['name'].strip(), parent=current_folder, created_by=user)
                    new_folder.save()
                    out['new_folder_id'] = new_folder.pk

                # rename folder
                elif action == 'rename_folder':
                    if current_folder.is_shared_folder or current_folder.is_root_folder:
                        raise BadRequest("Not a valid action for this folder.")
                    current_folder.rename(request.POST['name'])

                # delete folder
                elif action == 'delete_folder':
                    if current_folder.is_shared_folder or current_folder.is_root_folder:
                        raise BadRequest("Not a valid action for this folder.")
                    if not current_folder.is_empty():
                        raise BadRequest("Folders can only be deleted if they are empty.")
                    current_folder.delete()

                # save notes
                elif action == 'save_notes':
                    link = get_object_or_404(Link, link_access_filter, pk=request.POST['link_id'])
                    link.notes = request.POST['notes']
                    link.save()

                # save title change
                elif action == 'save_title':
                    link = get_object_or_404(Link, link_access_filter, pk=request.POST['link_id'])
                    link.submitted_title = request.POST['title']
                    link.save()

                else:
                    raise BadRequest("Action not recognized.")

        except BadRequest as e:
            return HttpResponseBadRequest(e.message)

        if request.is_ajax():
            return HttpResponse(json.dumps(out), content_type="application/json")

    # start with all links belonging to user
    links = Link.objects.accessible_to(user).select_related('vested_by_editor', 'created_by')

    # handle search
    search_query = request.GET.get('q', None)
    if search_query:
        links = links.filter(
            Q(guid__icontains=search_query) |
            Q(submitted_url__icontains=search_query) |
            Q(submitted_title__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    else:
        # limit links to current folder
        links = links.filter(folders=current_folder)

    # handle sorting
    DEFAULT_SORT = '-creation_timestamp'
    sort = request.GET.get('sort', DEFAULT_SORT)
    if sort not in valid_link_sorts:
        sort = DEFAULT_SORT
    links = links.order_by(sort)

    shared_with_count = 0
    if current_folder.vesting_org:
        shared_with_count = max(current_folder.vesting_org.users.count()-1, 0)

    return render(request, 'user_management/includes/created-link-items.html', {
        'links': links,
        'current_folder': current_folder,
        'search_query': search_query,
        'shared_with_count': shared_with_count,
        'in_iframe': request.GET.get('iframe'),
    })

###### link editing ######
@require_group(['registrar_user', 'registry_user', 'vesting_user'])
def vest_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    if link.vested:
        return HttpResponseRedirect(reverse('single_linky', args=[guid]))

    user = request.user
    vesting_org = user.vesting_org

    # make user pick a vesting org, if they have more than one
    if not vesting_org:
        if request.POST.get('vesting_org'):
            vesting_org = get_object_or_404(VestingOrg, pk=request.POST['vesting_org'], **({'registrar':user.registrar} if user.registrar else {}))
        else:
            if user.registrar:
                vesting_orgs = VestingOrg.objects.filter(registrar=user.registrar)
            else:
                vesting_orgs = VestingOrg.objects.all()
            vesting_orgs = list(vesting_orgs)
            if not vesting_orgs:
                messages.add_message(request, messages.ERROR, "Please create a vesting organization before vesting links.")
                return HttpResponseRedirect(reverse('single_linky', args=[guid]))
            elif len(vesting_orgs)==1:
                vesting_org = vesting_orgs[0]
            else:
                return render(request, 'link-vest-confirm.html', {
                    'vesting_orgs':vesting_orgs,
                    'link': link,
                })

    # make user pick a folder in the vesting org's shared folder
    if not request.POST.get('folder'):
        try:
            selected_folder = link.folders.get(vesting_org=vesting_org)
        except Folder.DoesNotExist:
            selected_folder = None
        return render(request, 'link-vest-confirm.html', {
            'folder_tree': vesting_org.shared_folder.get_descendants(include_self=True),
            'link': link,
            'vesting_org': vesting_org,
            'selected_folder': selected_folder,
        })

    # vest
    if request.POST.get('vest'):
        target_folder = get_object_or_404(Folder, pk=request.POST['folder'], vesting_org=vesting_org)
        link.vested = True
        link.vested_by_editor = user
        link.vesting_org = vesting_org
        link.vested_timestamp = datetime.now()
        link.save()

        link.move_to_folder_for_user(target_folder, request.user)

        if settings.UPLOAD_TO_INTERNET_ARCHIVE and link.can_upload_to_internet_archive():
            run_task(upload_to_internet_archive, link_guid=guid)

    return HttpResponseRedirect(reverse('single_linky', args=[guid]))

    
    
@login_required    
def user_delete_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    asset = Asset.objects.get(link=link)
    if request.method == 'POST':
        if not request.user == link.created_by:
            return HttpResponseRedirect(reverse('single_linky', args=[guid]))
            
        if not link.user_deleted and not link.vested:
            link.user_deleted=True
            link.user_deleted_timestamp=datetime.now()
            link.save()

        return HttpResponseRedirect(reverse('link_browser'))
    return render_to_response('link-delete-confirm.html', {'link': link, 'asset': asset}, RequestContext(request))


@login_required
def dark_archive_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    asset = Asset.objects.get(link=link)
    if request.method == 'POST':
        if request.user.has_group('registrar_user'):
            if not link.vesting_org.registrar == request.user.registrar and not request.user == link.created_by:
                return HttpResponseRedirect(reverse('single_linky', args=[guid]))
        elif request.user.has_group('vesting_user'): 
            if not link.vesting_org == request.user.vesting_org and not request.user == link.created_by:
                return HttpResponseRedirect(reverse('single_linky', args=[guid]))
        elif not request.user == link.created_by:
            return HttpResponseRedirect(reverse('single_linky', args=[guid]))
            
        if not link.dark_archived:
            link.dark_archived=True
            link.dark_archived_by = request.user
            link.save()
        return HttpResponseRedirect(reverse('single_linky', args=[guid]))
    return render_to_response('dark-archive-link.html', {'link': link, 'asset': asset}, RequestContext(request))
