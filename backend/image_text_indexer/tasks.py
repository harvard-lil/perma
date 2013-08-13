from __future__ import absolute_import

import os, sys, subprocess
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.image_text_indexer.celery import celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "linky_web.linky.settings") 

from django.conf import settings

if not settings.configured:
    settings.configure()



@celery.task
def get_screen_cap(link_id, target_url):
    """ Create an image from the url, store it in a dir. use the id as part of the dir path """

    linky_home_disk_path = settings.PROJECT_ROOT + '/' + '/static/generated/' + str(link_id) + '/'

    now = dt = datetime.now()
    time_tuple = now.timetuple()

    # This is our set of path elements. select from this list as needed.
    path_elements = [settings.GENERATED_ASSETS_STORAGE, str(time_tuple.tm_year), str(time_tuple.tm_mon), str(time_tuple.tm_mday), str(time_tuple.tm_hour), str(link_id), 'cap.png']

    if not os.path.exists(os.path.sep.join(path_elements[:6])):
        os.makedirs(os.path.sep.join(path_elements[:6]))

    image_generation_command = settings.PROJECT_ROOT + '/lib/phantomjs ' + settings.PROJECT_ROOT + '/lib/rasterize.js "' + target_url + '" ' + os.path.sep.join(path_elements)
    
    print image_generation_command
    subprocess.call(image_generation_command, shell=True)

    return os.path.sep.join(path_elements[1:])