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
from mptt.exceptions import InvalidMove
from PyPDF2 import PdfFileReader

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponseBadRequest, Http404, HttpResponseRedirect
from django.shortcuts import HttpResponse, render_to_response, get_object_or_404, render
from django.template import RequestContext

from mirroring.tasks import compress_link_assets, poke_mirrors

from ..forms import UploadFileForm
from ..models import Link, Asset, Folder, VestingOrg, FolderException
from ..tasks import get_pdf, proxy_capture, upload_to_internet_archive
from ..utils import require_group, run_task, get_search_query


logger = logging.getLogger(__name__)
valid_link_sorts = ['-creation_timestamp', 'creation_timestamp', 'vested_timestamp', '-vested_timestamp', 'submitted_title', '-submitted_title']

HEADER_CHECK_TIMEOUT = 10 # seconds to wait before giving up when checking headers for requested link

###### LINK CREATION ######

@login_required
def create_link(request):
    """
    Create new links
    """
    if request.POST:
        # We've received a request to archive a URL. That process is managed here.
        # We create a new entry in our datastore and pass the work off to our indexing
        # workers. They do their thing, updating the model as they go. When we get some minimum
        # set of results we can present the user (a guid for the link), we respond back.

        target_url = request.POST.get('url').strip()

        # If we don't get a protocol, assume http
        if target_url[:4] != 'http':
            target_url = 'http://' + target_url

        # Does this thing look like a valid URL?
        validate = URLValidator()
        try:
            validate(target_url)
        except ValidationError:
            return HttpResponseBadRequest("Not a valid URL.")

        # By default, use the domain as title
        url_details = urlparse(target_url)
        target_title = url_details.netloc

        # Check for banned IP.
        try:
            target_ip = socket.gethostbyname(url_details.netloc.split(':')[0])
        except socket.gaierror:
            return HttpResponseBadRequest("Couldn't resolve domain.")
        for banned_ip_range in settings.BANNED_IP_RANGES:
            if IPAddress(target_ip) in IPNetwork(banned_ip_range):
                return HttpResponseBadRequest("Not a valid IP.")

        # Get target url headers. We get the mime-type and content length from this.
        try:
            target_url_headers = requests.head(
                target_url,
                verify=False, # don't check SSL cert?
                headers={'User-Agent': request.META['HTTP_USER_AGENT'], 'Accept-Encoding':'*'},
                timeout=HEADER_CHECK_TIMEOUT
            ).headers
        except (requests.ConnectionError, requests.Timeout):
            return HttpResponseBadRequest("Couldn't load URL.")
        try:
            if int(target_url_headers.get('content-length', 0)) > 1024 * 1024 * 100:
                return HttpResponseBadRequest("Target page is too large (max size 1MB).")
        except ValueError:
            # Weird -- content-length header wasn't an integer. Carry on.
            pass

        # Create link.
        link = Link(submitted_url=target_url, created_by=request.user, submitted_title=target_title)
        link.save()

        guid = link.guid
        asset = Asset(link=link)
        response_object = {'linky_id': guid, 'linky_title':''}

        # celery tasks to run after scraping is complete
        postprocessing_tasks = []
        if settings.MIRRORING_ENABLED:
            postprocessing_tasks += [
                compress_link_assets.s(guid=guid),
                poke_mirrors.s(link_guid=guid),
            ]

        # If it appears as if we're trying to archive a PDF, only run our PDF retrieval tool
        if target_url_headers.get('content-type',None) in ['application/pdf', 'application/x-pdf'] or target_url.endswith('.pdf'):
            asset.pdf_capture = 'pending'
            asset.save()

            # run background celery tasks as a chain (each finishes before calling the next)
            run_task(chain(
                get_pdf.s(guid, target_url, asset.base_storage_path, request.META['HTTP_USER_AGENT']),
                *postprocessing_tasks
            ))

            response_object['message_pdf'] = True

        else:  # else, it's not a PDF. Let's try our best to retrieve what we can

            asset.image_capture = 'pending'
            asset.text_capture = 'pending'
            asset.warc_capture = 'pending'
            asset.save()

            # run background celery tasks as a chain (each finishes before calling the next)
            run_task(chain(
                proxy_capture.s(guid, target_url, asset.base_storage_path, request.META['HTTP_USER_AGENT']),
                *postprocessing_tasks
            ))

        return HttpResponse(json.dumps(response_object), content_type="application/json", status=201) # '201 Created' status

    return render(request, 'user_management/create-link.html', {
        'this_page': 'create_link',
    })


def validate_upload_file(upload, mime_type):
    # Make sure files are not corrupted.

    if mime_type == 'image/jpeg':
        return imghdr.what(upload) == 'jpeg'
    elif mime_type == 'image/png':
        return imghdr.what(upload) == 'png'
    elif mime_type == 'image/gif':
        return imghdr.what(upload) == 'gif'
    elif mime_type == 'application/pdf':
        doc = PdfFileReader(upload)
        if doc.numPages >= 0:
            return True
    return False

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():

            mime = MimeTypes()
            uploaded_file = request.FILES['file']
            mime_type = mime.guess_type(uploaded_file.name)

            # Get mime type string from tuple
            if mime_type[0]:
                mime_type = mime_type[0]
            else:
                return HttpResponseBadRequest(json.dumps({'status':'failed', 'reason':'Invalid file.'}), 'application/json')

            if validate_upload_file(uploaded_file, mime_type) and uploaded_file.size <= settings.MAX_ARCHIVE_FILE_SIZE:
                link = Link(submitted_url=form.cleaned_data['url'], submitted_title=form.cleaned_data['title'], created_by = request.user)
                link.save()

                asset = Asset(link=link)
                file_name = 'cap' + mime.guess_extension(mime_type)
                file_path = os.path.join(asset.base_storage_path, file_name)

                uploaded_file.file.seek(0)
                file_name = default_storage.store_file(uploaded_file, file_path)

                if mime_type == 'application/pdf':
                    asset.pdf_capture = file_name
                else:
                    asset.image_capture = file_name
                asset.save()

                response_object = {'status':'success', 'linky_id':link.guid, 'linky_hash':link.guid}

                return HttpResponse(json.dumps(response_object), 'application/json', 201)  # '201 Created' status
            else:
                return HttpResponseBadRequest(json.dumps({'status':'failed', 'reason':'Invalid file.'}), 'application/json')
        else:
            return HttpResponseBadRequest(json.dumps({'status':'failed', 'reason':'Missing file.'}), 'application/json')

    return HttpResponseBadRequest(json.dumps({'status':'failed', 'reason':'No file submitted.'}), 'application/json')


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

                    current_folder.name = request.POST['name']
                    current_folder.set_slug()
                    current_folder.save()

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
    links = Link.objects.accessible_to(user)

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
        'shared_with_count': shared_with_count
    })

###### link editing ######
@require_group(['registrar_user', 'registry_user', 'vesting_user'])
def vest_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    user = request.user
    if request.method == 'POST' and not link.vested:

        # if user isn't associated with a vesting org, make them pick one
        vesting_org = user.vesting_org
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

        # make sure this link is either already in the vesting org's shared folder, or user has told us to save to one
        target_folder = None
        if request.POST.get('folder'):
            target_folder = get_object_or_404(Folder, pk=request.POST['folder'], vesting_org=vesting_org)
        elif not link.folders.filter(vesting_org=vesting_org).exists():
            return render(request, 'link-vest-confirm.html', {
                'folder_tree': vesting_org.shared_folder.get_descendants(include_self=True),
                'link': link,
                'vesting_org': vesting_org
            })

        # vest
        link.vested = True
        link.vested_by_editor = user
        link.vesting_org = vesting_org
        link.vested_timestamp = datetime.now()
        link.save()

        if target_folder:
            link.move_to_folder_for_user(target_folder, request.user)

        run_task(poke_mirrors, link_guid=guid)

        if settings.UPLOAD_TO_INTERNET_ARCHIVE:
            run_task(upload_to_internet_archive, link_guid=guid)

    return HttpResponseRedirect(reverse('single_linky', args=[guid]))
    
    
@login_required    
def user_delete_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    asset = Asset.objects.get(link=link)
    if request.method == 'POST':
        if not link.user_deleted and not link.vested:
            link.user_deleted=True
            link.user_deleted_timestamp=datetime.now()
            link.save()

        return HttpResponseRedirect(reverse('created_links'))
    return render_to_response('link-delete-confirm.html', {'link': link, 'asset': asset}, RequestContext(request))


@require_group('registry_user')
def dark_archive_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    asset = Asset.objects.get(link=link)
    if request.method == 'POST':
        if not link.dark_archived:
            link.dark_archived=True
            link.save()
            run_task(poke_mirrors, link_guid=guid)
        return HttpResponseRedirect(reverse('single_linky', args=[guid]))
    return render_to_response('dark-archive-link.html', {'link': link, 'asset': asset}, RequestContext(request))
