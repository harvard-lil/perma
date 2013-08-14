import os, sys, subprocess, urllib, glob, shutil
from celery import task
from django.conf import settings

from linky_web.linky.models import Asset
from linky_web.linky.exceptions import BrokenURLError

@task
def get_screen_cap(link_guid, target_url, base_storage_path):
    """ Create an image from the url, store it in a dir. use the id as part of the dir path """

    path_elements = [settings.GENERATED_ASSETS_STORAGE, base_storage_path, 'cap.png']

    if not os.path.exists(os.path.sep.join(path_elements[:2])):
        os.makedirs(os.path.sep.join(path_elements[:2]))

    image_generation_command = settings.PROJECT_ROOT + '/lib/phantomjs ' + settings.PROJECT_ROOT + '/lib/rasterize.js "' + target_url + '" ' + os.path.sep.join(path_elements)
    
    subprocess.call(image_generation_command, shell=True)

    if not os.path.exists(os.path.sep.join(path_elements)):
        return False

    asset = Asset.objects.get(link__guid=link_guid)
    asset.image_capture = os.path.sep.join(path_elements[2:])
    asset.save()
    
    return True
    
@task
def get_source(link_guid, target_url, base_storage_path, user_agent=''):

    path_elements = [settings.GENERATED_ASSETS_STORAGE, base_storage_path, 'source', 'index.html']

    directory = os.path.sep.join(path_elements[:3])

    headers = {
        'Accept': ','.join(settings.ACCEPT_CONTENT_TYPES),
        'User-Agent': user_agent,
    }

    """ Get the markup and assets, update our db, and write them to disk """
    # Construct wget command
    command = 'wget '
    command = command + '-q ' # Don't print output to the console
    command = command + '-p ' # Get page requisites
    command = command + '-k ' # Convert non-relative links to relative
    command = command + '-nd ' # Don't create subdirectories
    command = command + '-Q ' + settings.ARCHIVE_QUOTA + ' ' # Limit filesize, maybe 200k
    command = command + '--user-agent="' + user_agent + '" '
    command = command + '--limit-rate=' + settings.ARCHIVE_LIMIT_RATE + ' ' # Limit download rate
    command = command + '-e robots=off ' # Ignore robots.txt
    command = command + '-P ' + directory + ' ' # Storage directory prefix
    
    # Add headers (defined earlier in this function)
    for key, value in headers.iteritems():
        command = command + '--header="' + key + ': ' + value+ '" '
    command = command + target_url # Download the user-specified URL

    # Download page data and dependencies
    if not os.path.exists(directory):
        os.makedirs(directory)
    output = os.popen(command)


    # Verify success
    if '400 Bad Request' in output:
        raise BrokenURLError(target_url)
    # Rename file as index.html
    filename = urllib.unquote(target_url.split('/')[-1]).decode('utf8')
    if filename != '':
        try:
            src = os.path.join(directory, filename)
            des = os.path.join(directory, 'index.html')
            shutil.move(src, des)
        except:
            # Rename the file as index.html if it contains '<html'
            counter = 0
            for filename in glob.glob(directory + '/*'):
                with open(filename) as f:
                    if '<html' in f.read():
                        shutil.move(os.path.join(directory, filename), os.path.join(directory, 'index.html'))
                        counter = counter + 1
            if counter == 0:
                # Raise error if no HTML pages were retrieved
                raise BrokenURLError(target_url)
                os.system('rm -rf ' + directory)
                
            
    asset = Asset.objects.get(link__guid=link_guid)
    asset.warc_capture = os.path.sep.join(path_elements[2:])
    asset.save()
