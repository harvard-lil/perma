import imghdr
import logging, json, os
from datetime import datetime
import socket
from urlparse import urlparse
from mimetypes import MimeTypes
from celery import chain
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
from ..models import Link, Asset, Folder
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
                headers={'User-Agent': request.META['HTTP_USER_AGENT']},
                timeout=HEADER_CHECK_TIMEOUT
            ).headers
        except (requests.ConnectionError, requests.Timeout):
            return HttpResponse("Couldn't load URL.", status=400)
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

    return render_to_response('user_management/create-link.html',
                              {'this_page': 'create_link', 'user': request.user},
                              RequestContext(request))


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
def created_links(request, path):
    """
    Anyone with an account can view the linky links they've created
    """
    return link_browser(request, path,
                        link_filter={'created_by':request.user, 'user_deleted':False},
                        this_page='created_links',
                        verb='created')


@require_group(['registrar_user', 'registry_user', 'vesting_user'])
def vested_links(request, path):
    """
    Linky admins and registrar members and vesting members can vest links
    """
    return link_browser(request, path,
                        link_filter={'vested_by_editor': request.user, 'user_deleted':False},
                        this_page='vested_links',
                        verb='vested')


def link_browser(request, path, link_filter, this_page, verb):
    """ Display a set of links with the given filter (created by or vested by user). """

    # find current folder based on path
    current_folder = None
    folder_breadcrumbs = []
    show_shared_folder_warning = request.user.vesting_org is not None  # TEMP
    if path:
        path = path.strip("/")
        if path:
            # get current folder
            folder_slugs = path.split("/")
            current_folder = get_object_or_404(Folder,slug=folder_slugs[-1],created_by=request.user)
            show_shared_folder_warning = show_shared_folder_warning and folder_slugs[0]!="my-links"  # TEMP

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

            # TEMP
            # prevent vested links being moved into My Links
            if show_shared_folder_warning:
                if target_folder and target_folder.get_ancestors(include_self=True).filter(name="My Links").exists():
                    move_ok = not Link.objects.filter(pk__in=request.POST.getlist('links'), vested=True).exists()
                    if move_ok:
                        for folder_id in request.POST.getlist('folders'):
                            folder = get_object_or_404(Folder, pk=folder_id, created_by=request.user)
                            if folder.get_descendants(include_self=True).filter(links__vested=True).exists():
                                move_ok = False
                                break
                    if not move_ok:
                        return HttpResponseBadRequest("Sorry, vested links can't be moved into 'My Links'. They belong to your vesting organization.")

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

            # save title change
            elif posted_data['action'] == 'save_title':
                link = get_object_or_404(Link, pk=posted_data['link_id'], **link_filter)
                link.submitted_title = posted_data['title']
                link.save()

            return HttpResponse(json.dumps(out), content_type="application/json")

    # start with all links belonging to user
    linky_links = Link.objects.filter(**link_filter)

    # handle search
    search_query = request.GET.get('q', '')
    if search_query:
        linky_links = get_search_query(linky_links, search_query, ['guid', 'submitted_url', 'submitted_title', 'notes'])
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
    base_url = reverse(this_page)
    link_count = Link.objects.filter(**link_filter).count()

    context = {'linky_links': linky_links, 'link_count':link_count,
               'sort': sort,
               'search_query':search_query,
               'search_placeholder':"Search %s" % (current_folder if current_folder else "links"),
               'this_page': this_page, 'verb': verb,
               'subfolders':subfolders, 'path':path, 'folder_breadcrumbs':folder_breadcrumbs,
               'current_folder':current_folder,
               'all_folders':all_folders,
               'show_shared_folder_warning':show_shared_folder_warning,  # TEMP
               'base_url':base_url}

    context = RequestContext(request, context)

    return render_to_response('user_management/created-links.html', context)


###### link editing ######
@require_group(['registrar_user', 'registry_user', 'vesting_user'])
def vest_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    if request.method == 'POST' and not link.vested and request.user.vesting_org:

        # TEMP
        # make sure this link is outside My Links, or user has told us to save it there
        target_folder = None
        move_to_target_folder = False
        if request.POST.get('folder'):
            if request.POST['folder'] == 'ROOT':
                target_folder = None
            else:
                target_folder = get_object_or_404(Folder, pk=request.POST['folder'], created_by=request.user)
            move_to_target_folder = True
        else:
            try:
                target_folder = Folder.objects.get(created_by=request.user, links=link)
            except Folder.DoesNotExist:
                pass
        if target_folder and target_folder.get_ancestors(include_self=True).filter(name="My Links").exists():
            return render(request, 'link-vest-confirm.html', {
                'folder_tree': Folder.objects.filter(created_by=request.user),
                'link': link,
            })
        if move_to_target_folder:
            link.move_to_folder_for_user(target_folder, request.user)

        # vest
        link.vested = True
        link.vested_by_editor = request.user
        link.vesting_org = request.user.vesting_org
        link.vested_timestamp = datetime.now()
        link.save()

        run_task(poke_mirrors, link_guid=guid)

        if settings.UPLOAD_TO_INTERNET_ARCHIVE:
            run_task(upload_to_internet_archive, link_guid=guid)

    return HttpResponseRedirect(reverse('single_link_header', args=[guid]))
    
    
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
        return HttpResponseRedirect(reverse('single_link_header', args=[guid]))
    return render_to_response('dark-archive-link.html', {'link': link, 'asset': asset}, RequestContext(request))
