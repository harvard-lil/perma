from datetime import datetime, timedelta
import logging, json, subprocess, urllib2, re, os
from datetime import datetime
from urlparse import urlparse

import lxml.html, requests
from PIL import Image
from pyPdf import PdfFileReader

from linky.models import Link, Asset
from linky.forms import UploadFileForm
from linky.utils import base
from linky.tasks import get_screen_cap, get_source, store_text_cap

from django.shortcuts import render_to_response, HttpResponse
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

try:
    from linky.local_settings import *
except ImportError, e:
    logger.error('Unable to load local_settings.py: %s', e)

# TODO: If we're going to csrf exempt this, we should keep an eye on things
@csrf_exempt
def linky_post(request):
    """
    We've received a request to archive a URL. That process is managed here.
    We create a new entry in our datastore and pass the work off to our indexing
    workers. They do their thing, updating the model as they go. When we get some minimum
    set of results we can present the uesr (a title and an image capture of the page), we respond
    back.
    """

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

    # Somtimes we can't get a title from the markup. If not, use the domain
    url_details = urlparse(target_url)
    target_title = url_details.netloc

    # Get the markup
    try:
        r = requests.get(target_url)
        parsed_html = lxml.html.fromstring(r.content)
    except IOError:
        # TODO: log urls the fail
        return HttpResponse(status=400)

    # TODO: this fails for some sites. fix.
    if len(parsed_html):
        if parsed_html.find(".//title") is not None and parsed_html.find(".//title").text:
            target_title = parsed_html.find(".//title").text.strip()

    # We have some markup and a title. Let's create a linky from it
    link = Link(submitted_url=target_url, submitted_title=target_title)

    if request.user.is_authenticated():
        link.created_by = request.user

    link.save()

    # Assets get stored in /storage/path/year/month/day/hour/unique-id/*
    # Get that path that we'll pass off to our workers to do the indexing. They'll store their results here
    now = dt = datetime.now()
    time_tuple = now.timetuple()

    path_elements = [str(time_tuple.tm_year), str(time_tuple.tm_mon), str(time_tuple.tm_mday), str(time_tuple.tm_hour), link.guid]

    # Create a stub for our assets
    asset, created = Asset.objects.get_or_create(link=link)
    asset.base_storage_path = os.path.sep.join(path_elements)
    asset.save()

    # Run our synchronus screen cap task (use the headless browser to create a static image)
    # TODO: try catch the scren cap. if we fail, alert the user that they should upload their screen cap
    get_screen_cap(link.guid, target_url, os.path.sep.join(path_elements))
    store_text_cap(target_url, target_title, link)
    try:
        get_source.delay(link.guid, target_url, os.path.sep.join(path_elements), request.META['HTTP_USER_AGENT'])
    except Exception, e:
        # TODO: Log the failed url
        asset.warc_capture = 'failed'
        asset.save()

    asset= Asset.objects.get(link__guid=link.guid)

    response_object = {'linky_id': link.guid, 'linky_cap': settings.STATIC_URL + asset.base_storage_path + '/' + asset.image_capture, 'linky_title': link.submitted_title}

    return HttpResponse(json.dumps(response_object), content_type="application/json", status=201)


def validate_upload_file(upload):
    # Make sure files are not corrupted.
    extention = upload.name[-4:]
    if extention in ['.jpg', 'jpeg']:
        try:
            i = Image.open(upload)
            if i.format == 'JPEG':
                return True
        except IOError:
            return False
    elif extention == '.png':
        try:
            i = Image.open(upload)
            if i.format =='PNG':
                return True
        except IOError:
            return False
    elif extention == '.pdf':
        doc = PdfFileReader(upload)
        if all([doc.documentInfo, doc.numPages]):
            return True
    return False


@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        print 'FOO'
        if form.is_valid():
            print 'BAR'
            if validate_upload_file(request.FILES['file']):
                link = Link(submitted_url=form.cleaned_data['url'], submitted_title=form.cleaned_data['title'])
                if request.user.is_authenticated():
                  link.created_by = request.user
                link.save()
                now = dt = datetime.now()
                time_tuple = now.timetuple()
                path_elements = [str(time_tuple.tm_year), str(time_tuple.tm_mon), str(time_tuple.tm_mday), str(time_tuple.tm_hour), link.guid]

                linky_home_disk_path = settings.GENERATED_ASSETS_STORAGE + '/' + os.path.sep.join(path_elements)

                if not os.path.exists(linky_home_disk_path):
                    os.makedirs(linky_home_disk_path)

                file_name = '/cap.' + request.FILES['file'].name.split('.')[-1]
                request.FILES['file'].file.seek(0)
                f = open(linky_home_disk_path + file_name, 'w')
                f.write(request.FILES['file'].file.read())
                os.fsync(f)
                f.close()
                if request.FILES['file'].name.split('.')[-1] == 'pdf':
                    pass
                    #print linky_home_disk_path + file_name
                    #png = PythonMagick.Image(linky_home_disk_path + file_name)
                    #png.write("file_out.png")
                    #params = ['convert', linky_home_disk_path + file_name, 'out.png']
                    #subprocess.check_call(params)

                response_object = {'status':'success', 'linky_id':link.guid, 'linky_hash':link.guid}
                url_details = urlparse(form.cleaned_data['url'])

                asset, created = Asset.objects.get_or_create(link=link)
                asset.base_storage_path = os.path.sep.join(path_elements)
                asset.save()

                try:
                	r = requests.get(form.cleaned_data['url'])
                	parsed_html = lxml.html.fromstring(r.content)
                except IOError:
                	pass

                return HttpResponse(json.dumps(response_object), 'application/json')
            else:
                return HttpResponseBadRequest(json.dumps({'status':'failed', 'reason':'Invalid file.'}), 'application/json')
        else:
            return HttpResponseBadRequest(json.dumps({'status':'failed', 'reason':'Missing file.'}), 'application/json')
    return HttpResponseBadRequest(json.dumps({'status':'failed', 'reason':form.errors}), 'application/json')


def urldump(request, since=None):
    """
    Give basic JSON encoding of GUID/URL pairs created since 'since'
    """
    ### XXX some day we should probably cache this and/or use some
    ### sort of sweet checkpointing system, but this is a start
    if since is None:
        dt = datetime.now() - timedelta(days=1)
    else:
        dt = datetime.strptime(since, "%Y-%m-%d")
    links = Link.objects.filter(creation_timestamp__gte=dt)
    data = []
    for link in links:
        datum = {'guid': link.guid, 'url': link.submitted_url}
        data.append(datum)
    response = json.dumps(data)
    return HttpResponse(response, 'application/json')
