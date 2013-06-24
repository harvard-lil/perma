import logging, json, subprocess, urllib2

import lxml.html


from linky.models import Link
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

    target_title = 'Title unknown'
    
    parsed_html = lxml.html.parse(urllib2.urlopen(target_url))
    
    if parsed_html:
        target_title = parsed_html.find(".//title").text
        
        
    link = Link(submitted_url=target_url, submitted_title=target_title)
    link.save()
    
    
    image_generation_command = INTERNAL['APP_FILEPATH'] + '/lib/phantomjs ' + INTERNAL['APP_FILEPATH'] + '/lib/rasterize.js "' + target_url + '" ' + INTERNAL['APP_FILEPATH'] + '/static/img/linkys/' + link.hash_id + '.png'
    subprocess.call(image_generation_command, shell=True)

    # if we want to do some file uploading
    #f = request.files['the_file']
    #f.save('/var/www/uploads/uploaded_file.txt')
    
    response_object = {'linky_id': link.hash_id, 'linky_url': 'http://' + request.get_host() + '/static/img/linkys/' + link.hash_id + '.png', 'linky_title': link.submitted_title}

    return HttpResponse(json.dumps(response_object), content_type="application/json", status=201)
