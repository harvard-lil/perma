import logging, json, subprocess, urllib2, re, os
from urlparse import urlparse

import lxml.html


from linky.models import Link
from linky.utils import base
from django.shortcuts import render_to_response, HttpResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

try:
    from linky.local_settings import *
except ImportError, e:
    logger.error('Unable to load local_settings.py:', e)

# TODO: If we're going to csrf exempt this, we should keep an eye on things
@csrf_exempt
def linky_post(request):
    """ When we receive a Linky POST """
    target_url = request.POST.get('url')

    if not target_url:
        return HttpResponse(status=400)
        
    if target_url[0:4] != 'http':
        target_url = 'http://' + target_url

    url_details = urlparse(target_url)

    target_title = url_details.netloc
        
    try:
        parsed_html = lxml.html.parse(urllib2.urlopen(target_url))
    except IOError:
        pass
    
    if parsed_html:
        if parsed_html.find(".//title"):
            target_title = parsed_html.find(".//title").text
        
    link = Link(submitted_url=target_url, submitted_title=target_title)
    link.save()
    
    # We've created a linky. Let's create its home on disk
    
    linky_home_disk_path = INTERNAL['APP_FILEPATH'] + '/static/generated/' + str(link.id) + '/'
    
    if not os.path.exists(linky_home_disk_path):
        os.makedirs(linky_home_disk_path)
        
    manifest = {}
    
    linky_hash = base.convert(link.id, base.BASE10, base.BASE58)
    
    
    favicon_success = __get_favicon(target_url, parsed_html, link.id, linky_home_disk_path, url_details)
    
    image_generation_command = INTERNAL['APP_FILEPATH'] + '/lib/phantomjs ' + INTERNAL['APP_FILEPATH'] + '/lib/rasterize.js "' + target_url + '" ' + linky_home_disk_path + 'cap.png'
    subprocess.call(image_generation_command, shell=True)

    manifest['image'] = 'cap.png'
    
    # if we want to do some file uploading
    #f = request.files['the_file']
    #f.save('/var/www/uploads/uploaded_file.txt')
    
    response_object = {'linky_id': linky_hash, 'linky_url': 'http://' + request.get_host() + '/static/generated/' + str(link.id) + '/cap.png', 'linky_title': link.submitted_title}
    
    if favicon_success:
        response_object['favicon_url'] = 'http://' + request.get_host() + '/static/generated/' + str(link.id) + '/' + favicon_success
        manifest['favicon'] = favicon_success

    with open(linky_home_disk_path + 'manifest.json', 'w') as outfile:
      json.dump(manifest, outfile)

    return HttpResponse(json.dumps(response_object), content_type="application/json", status=201)
    
    
def __get_favicon(target_url, parsed_html, link_hash_id, disk_path, url_details):
    """ Given a URL and the markup, see if we can find a favicon.
        TODO: this is a rough draft. cleanup and move to an appropriate place. """
    
    # We already have the parsed HTML, let's see if there is a favicon in the META elements
    favicons = parsed_html.xpath('//link[@rel="icon"]/@href')
    
    favicon = None
    if len(favicons) > 0:
        favicon = favicons[0]
    elif not favicon:
        favicons = parsed_html.xpath('//link[@rel="shortcut"]/@href')
        if len(favicons) > 0:
            favicon = favicons[0]
    elif not favicon:
        favicons = parsed_html.xpath('//link[@rel="shortcut icon"]/@href')
        if len(favicons) > 0:
            favicon = favicons[0]

    if favicon:
        
        if not re.match(r'^http', favicon):
            favicon = url_details.scheme + '://' + url_details.netloc + favicon
        
        f = urllib2.urlopen(favicon)
        data = f.read()
        
        filepath_pieces = os.path.splitext(favicon)
        file_ext = filepath_pieces[1]
        
        with open(disk_path + 'fav' + file_ext, "wb") as asset:
            asset.write(data)

        return 'fav' + file_ext


    # If we haven't returned True above, we didn't find a favicon in the markup.
    # let's try the favicon convention: http://example.com/favicon.ico
    target_favicon_url = url_details.scheme + '://' + url_details.netloc + '/favicon.ico'
    
    try:
        f = urllib2.urlopen(target_favicon_url)
        data = f.read()
        with open(disk_path + 'fav.ico' , "wb") as asset:
            asset.write(data)

        return 'fav' + '.ico'
    except urllib2.HTTPError:
        pass
        
        
    return False