from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.conf import settings

from ..models import Link, Folder, Organization

valid_link_sorts = ['-creation_timestamp', 'creation_timestamp', 'submitted_title', '-submitted_title']


###### LINK CREATION ######

@login_required
def create_link(request):
    try:
        selected_org = Link.objects.filter(created_by_id=request.user.id).latest('creation_timestamp').organization
    except:
        selected_org = Organization.objects.accessible_to(request.user).first()

    if not selected_org:
        org_id = None
    else:
        org_id = selected_org.id

    try:
        org = get_object_or_404(Organization, id=org_id)
    except:
        org = None

    folder_id = request.user.root_folder_id
    if org:
        folder_id = org.shared_folder_id
    folder = Folder.objects.get(id=folder_id)

    deleted = request.GET.get('deleted', '')
    if deleted:
        try:
            link = Link.objects.all_with_deleted().get(guid=deleted)
        except Link.DoesNotExist:
            link = None
        if link:
            messages.add_message(request, messages.INFO, 'Deleted - ' + link.submitted_title)

    links_remaining = request.user.get_links_remaining()
    if links_remaining < 0:
        links_remaining = 0

    if 'url' in request.GET:
        suppress_reminder = 'true'
    else:
        suppress_reminder = request.COOKIES.get('suppress_reminder')

    max_size = settings.MAX_ARCHIVE_FILE_SIZE / 1024 / 1024

    return render(request, 'user_management/create-link.html', {
        'this_page': 'create_link',
        'links_remaining': links_remaining,
        'folder': folder,
        'suppress_reminder': suppress_reminder,
        'max_size': max_size
    })


###### LINK BROWSING ######

@login_required
def folder_contents(request, folder_id):
    # helper vars
    user = request.user
    folder_access_filter = Folder.objects.user_access_filter(user)

    current_folder = get_object_or_404(Folder, folder_access_filter, pk=folder_id)

    # start with all links belonging to user
    links = Link.objects.accessible_to(user).select_related('created_by')

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

@login_required
def user_delete_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    if not request.user.can_delete(link):
        raise Http404

    return render(request, 'archive/confirm/link-delete-confirm.html', {
        'link': link,
    })

