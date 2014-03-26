import logging, json, os
from datetime import datetime
from urlparse import urlparse
from mimetypes import MimeTypes
import lxml.html, requests
from PIL import Image
from mptt.exceptions import InvalidMove
from pyPdf import PdfFileReader

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponseBadRequest, Http404, HttpResponseRedirect
from django.shortcuts import HttpResponse, render_to_response, get_object_or_404
from django.template import RequestContext

from perma.forms import UploadFileForm
from perma.models import Link, Asset, Folder
from perma.tasks import start_proxy_record_get_screen_cap, store_text_cap, get_pdf
from perma.utils import require_group
if not settings.USE_WARC_ARCHIVE:
    from perma.tasks import get_source


logger = logging.getLogger(__name__)
valid_link_sorts = ['-creation_timestamp', 'creation_timestamp', 'vested_timestamp', '-vested_timestamp', 'submitted_title', '-submitted_title']


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
        # set of results we can present the user (a title and an image capture of the page), we respond
        # back.

        # Sometimes a tab or a space gets placed in the form field (by the
        # user copying and pasting?). Trim it here.
        target_url = request.POST.get('url').strip(' \t\n\r').replace(" ", "")

        # If we don't get a protocol, assume http
        if target_url[0:4] != 'http':
            target_url = 'http://' + target_url

        # Does this thing look like a valid URL?
        validate = URLValidator()
        try:
            validate(target_url)
        except ValidationError, e:
            return HttpResponse(status=400)

        # Sometimes we can't get a title from the markup. If not, use the domain
        url_details = urlparse(target_url)
        target_title = url_details.netloc
        content = None

        # Get the markup. We get the mime-type and the title from this.
        try:
            r = requests.get(target_url, stream=True, verify=False,
                headers={'User-Agent': request.META['HTTP_USER_AGENT']})

            # Only get the content if we get a content-length header and if
            # it's less than one MB.
            if 'content-length' in r.headers and int(r.headers['content-length']) < 1024 * 1024:
                content = r.content
                parsed_html = lxml.html.fromstring(r.content)
                if len(parsed_html):
                    if parsed_html.find(".//title") is not None and parsed_html.find(".//title").text:
                        target_title = parsed_html.find(".//title").text.strip()
            else:
                raise IOError
        except IOError:
            logger.debug("Title capture from markup failed for %s, using the hostname" % target_url)

        # We have some markup and a title. Let's create a linky from it
        link = Link(submitted_url=target_url, submitted_title=target_title, created_by=request.user)
        link.save()

        # We pass the guid to our tasks
        guid = link.guid

        # Assets get stored in /storage/path/year/month/day/hour/unique-id/*
        # Get that path that we'll pass off to our workers to do the indexing. They'll store their results here
        now = datetime.now()
        time_tuple = now.timetuple()

        path_elements = [str(time_tuple.tm_year), str(time_tuple.tm_mon), str(time_tuple.tm_mday),
                         str(time_tuple.tm_hour), str(time_tuple.tm_min), guid]

        # Create a stub for our assets
        asset, created = Asset.objects.get_or_create(link=link)
        asset.base_storage_path = os.path.join(*path_elements)

        # If it appears as if we're trying to archive a PDF, only run our PDF retrieval tool
        if 'content-type' in r.headers and r.headers['content-type'] in ['application/pdf', 'application/x-pdf'] or \
                        target_url.split('.')[-1] == 'pdf':
            asset.pdf_capture = 'pending'
            asset.save()
            get_pdf.delay(guid, target_url, asset.base_storage_path, request.META['HTTP_USER_AGENT'])
            response_object = {'linky_id': guid, 'message_pdf': True, 'linky_title': link.submitted_title}

        else:  # else, it's not a PDF. Let's try our best to retrieve what we can

            asset.image_capture = 'pending'
            asset.text_capture = 'pending'
            asset.warc_capture = 'pending'
            asset.save()

            # start warcprox server to intercept and save traffic between the internet and the headless browser in get_screen_cap
            # Creates screencap with headless browser
            start_proxy_record_get_screen_cap.delay(guid, target_url, asset.base_storage_path,
                                                    user_agent=request.META['HTTP_USER_AGENT'])

            # Get the text capture of the page (through a service that follows pagination)
            store_text_cap.delay(guid, target_url, asset.base_storage_path, target_title)

            if not settings.USE_WARC_ARCHIVE:
                # Try to crawl the page (but don't follow any links)
                get_source.delay(guid, target_url, os.path.sep.join(path_elements), request.META['HTTP_USER_AGENT'])

            asset = Asset.objects.get(link__guid=guid)

            response_object = {'linky_id': guid, 'linky_title': link.submitted_title}

            # Sometimes our phantomjs capture fails. if it doesn't add it to our response object
            if asset.image_capture != 'pending' and asset.image_capture != 'failed':
                response_object['linky_cap'] = settings.STATIC_URL + asset.base_storage_path + '/' + asset.image_capture
                

        return HttpResponse(json.dumps(response_object), content_type="application/json", status=201)

    return render_to_response('user_management/create-link.html',
                              {'this_page': 'create_link'},
                              RequestContext(request))


def validate_upload_file(upload, mime_type):
    # Make sure files are not corrupted.

    if mime_type == 'image/jpeg':
        try:
            i = Image.open(upload)
            if i.format == 'JPEG':
                return True
        except IOError:
            return False
    elif mime_type == 'image/png':
        try:
            i = Image.open(upload)
            if i.format =='PNG':
                return True
        except IOError:
            return False
    elif mime_type == 'image/gif':
        try:
            i = Image.open(upload)
            if i.format =='GIF':
                return True
        except IOError:
            return False
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
            mime_type = mime.guess_type(request.FILES['file'].name)

            # Get mime type string from tuple
            if mime_type[0]:
                mime_type = mime_type[0]
            else:
                return HttpResponseBadRequest(json.dumps({'status':'failed', 'reason':'Invalid file.'}), 'application/json')


            if validate_upload_file(request.FILES['file'], mime_type) and request.FILES['file'].size <= settings.MAX_ARCHIVE_FILE_SIZE:
                link = Link(submitted_url=form.cleaned_data['url'], submitted_title=form.cleaned_data['title'], created_by = request.user)
                link.save()

                now = datetime.now()
                time_tuple = now.timetuple()
                path_elements = [str(time_tuple.tm_year), str(time_tuple.tm_mon), str(time_tuple.tm_mday), str(time_tuple.tm_hour), str(time_tuple.tm_min), link.guid]

                linky_home_disk_path = settings.GENERATED_ASSETS_STORAGE + '/' + os.path.sep.join(path_elements)

                if not os.path.exists(linky_home_disk_path):
                    os.makedirs(linky_home_disk_path)

                asset, created = Asset.objects.get_or_create(link=link)
                asset.base_storage_path = os.path.sep.join(path_elements)
                asset.save()

                file_name = '/cap' + mime.guess_extension(mime_type)

                if mime_type == 'application/pdf':
                    asset.pdf_capture = file_name
                else:
                    asset.image_capture = file_name

                asset.save()

                request.FILES['file'].file.seek(0)
                f = open(linky_home_disk_path + file_name, 'w')
                f.write(request.FILES['file'].file.read())
                os.fsync(f)
                f.close()

                response_object = {'status':'success', 'linky_id':link.guid, 'linky_hash':link.guid}

                return HttpResponse(json.dumps(response_object), 'application/json')
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

            # save title change
            elif posted_data['action'] == 'save_title':
                link = get_object_or_404(Link, pk=posted_data['link_id'], **link_filter)
                link.submitted_title = posted_data['title']
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
               'base_url':base_url}

    context = RequestContext(request, context)

    return render_to_response('user_management/created-links.html', context)


###### LINK EDITING ######

@require_group(['registrar_member', 'registry_member', 'vesting_manager', 'vesting_member'])
def vest_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    if request.method == 'POST':
        if not link.vested:
            link.vested=True
            link.vested_by_editor=request.user
            link.vested_timestamp=datetime.now()
            link.save()
    return HttpResponseRedirect(reverse('single_linky', args=[guid]))


@require_group('registry_member')
def dark_archive_link(request, guid):
    link = get_object_or_404(Link, guid=guid)
    if request.method == 'POST':
        if not link.dark_archived:
            link.dark_archived=True
            link.save()
        return HttpResponseRedirect(reverse('single_linky', args=[guid]))
    return render_to_response('dark-archive-link.html', {'linky': link}, RequestContext(request))
