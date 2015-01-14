import logging

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, render
from django.template import RequestContext

from ..models import Link, Asset, Folder
from ..utils import require_group

# The api app conflicts with the legacy api view
# so we have to import via string.
# FIXME: If this is still here when upgrading to Django 1.7,
# import_by_path changed to import_string
from django.utils.module_loading import import_by_path
LinkUserResource = import_by_path('api.resources.LinkUserResource')
LinkResource = import_by_path('api.resources.LinkResource')

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

    lur = LinkUserResource()
    lur_bundle = lur.build_bundle(obj=request.user, request=request)

    return render(request, 'user_management/created-links.html', {
        'this_page': 'link_browser',
        'current_user': lur.serialize(None, lur.full_dehydrate(lur_bundle), 'application/json'),
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
    if current_folder.vesting_org:
        shared_with_count = max(current_folder.vesting_org.users.count()-1, 0)

    return render(request, 'user_management/includes/created-link-items.html', {
        'links': links,
        'current_folder': current_folder,
        'shared_with_count': shared_with_count,
        'in_iframe': request.GET.get('iframe'),
    })


###### link editing ######
@require_group(['registrar_user', 'registry_user', 'vesting_user'])
def vest_link(request, guid):
    link = get_object_or_404(Link, guid=guid)

    if link.vested:
        return HttpResponseRedirect(reverse('single_linky', args=[guid]))

    lr = LinkResource()
    lr_bundle = lr.build_bundle(obj=link, request=request)
    archive_json = lr.serialize(None, lr.full_dehydrate(lr_bundle), 'application/json')

    return render(request, 'link-vest-confirm.html', {
        'link': link,
        'archive_json': archive_json,
    })


@login_required
def user_delete_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    asset = Asset.objects.get(link=link)

    lr = LinkResource()
    lr_bundle = lr.build_bundle(obj=link, request=request)
    archive_json = lr.serialize(None, lr.full_dehydrate(lr_bundle), 'application/json')

    return render_to_response('link-delete-confirm.html',
                              {'link': link,
                               'asset': asset,
                               'archive_json': archive_json},
                              RequestContext(request))


@login_required
def dark_archive_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    asset = Asset.objects.get(link=link)

    lr = LinkResource()
    lr_bundle = lr.build_bundle(obj=link, request=request)
    archive_json = lr.serialize(None, lr.full_dehydrate(lr_bundle), 'application/json')

    return render_to_response('dark-archive-link.html',
                              {'link': link,
                               'asset': asset,
                               'archive_json': archive_json},
                              RequestContext(request))
