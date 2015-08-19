import logging

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from ..models import Link, Folder

logger = logging.getLogger(__name__)
valid_link_sorts = ['-creation_timestamp', 'creation_timestamp', 'vested_timestamp', '-vested_timestamp', 'submitted_title', '-submitted_title']


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

    return render(request, 'user_management/created-links.html', {
        'this_page': 'link_browser',
    })


@login_required
def folder_contents(request, folder_id):
    # helper vars
    user = request.user
    folder_access_filter = Folder.objects.user_access_filter(user)

    current_folder = get_object_or_404(Folder, folder_access_filter, pk=folder_id)

    # start with all links belonging to user
    links = Link.objects.accessible_to(user).select_related('vested_by_editor', 'created_by')

    # limit links to current folder
    links = links.filter(folders=current_folder)

    # handle sorting
    DEFAULT_SORT = '-creation_timestamp'
    sort = request.GET.get('sort', DEFAULT_SORT)
    if sort not in valid_link_sorts:
        sort = DEFAULT_SORT
    links = links.order_by(sort)

    shared_with_count = 0
    if current_folder.organization:
        shared_with_count = max(current_folder.organization.users.count()-1, 0)

    return render(request, 'user_management/includes/created-link-items.html', {
        'links': links,
        'current_folder': current_folder,
        'shared_with_count': shared_with_count,
        'in_iframe': request.GET.get('iframe'),
    })


###### link editing ######
@login_required
@user_passes_test(lambda user: user.is_staff or user.is_registrar_member() or user.is_organization_member)
def vest_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    folder = None
    try:
        latest = Link.objects.filter(vested_by_editor_id=request.user.id).latest('vested_timestamp')
    except:
        latest = None
        
    if latest:
        folder = latest.folders.exclude(organization_id__isnull=True)[0]

    if link.vested:
        return HttpResponseRedirect(reverse('single_linky', args=[guid]))

    return render(request, 'archive/confirm/link-vest-confirm.html', {
        'link': link,
        'latest': latest,
        'folder': folder,
    })


@login_required
def user_delete_link(request, guid):
    link = get_object_or_404(Link, guid=guid)

    return render(request, 'archive/confirm/link-delete-confirm.html', {
        'link': link,
    })


@login_required
def dark_archive_link(request, guid):
    link = get_object_or_404(Link, guid=guid)

    return render(request, 'archive/confirm/dark-archive-link.html', {
        'link': link,
    })
