import os, sys, subprocess, urllib, glob, shutil, urlparse, simplejson, datetime, smhasher
from djcelery import celery
import requests
from django.conf import settings

from linky.models import Asset
from linky.exceptions import BrokenURLError
from linky.settings import INSTAPAPER_KEY, INSTAPAPER_SECRET, INSTAPAPER_USER, INSTAPAPER_PASS, GENERATED_ASSETS_STORAGE

import oauth2 as oauth

@celery.task
def get_screen_cap(link_guid, target_url, base_storage_path):
    """
    Create an image from the supplied URL, write it to disk and update our asset model with the path.
    The heavy lifting is done by PhantomJS, our headless browser.

    This function is usually executed via a synchronous Celery call
    """

    path_elements = [settings.GENERATED_ASSETS_STORAGE, base_storage_path, 'cap.png']

    if not os.path.exists(os.path.sep.join(path_elements[:2])):
        os.makedirs(os.path.sep.join(path_elements[:2]))

    image_generation_command = settings.PROJECT_ROOT + '/lib/phantomjs ' + settings.PROJECT_ROOT + '/lib/rasterize.js "' + target_url + '" ' + os.path.sep.join(path_elements)

    subprocess.call(image_generation_command, shell=True)


    asset = Asset.objects.get(link__guid=link_guid)

    if os.path.exists(os.path.sep.join(path_elements)):
        asset.image_capture = os.path.sep.join(path_elements[2:])
        asset.save()
    else:
        logger.info("Screen capture failed for %s" % target_url)
        asset.image_capture = 'failed'
        asset.save()

        raise BrokenURLError(target_url)

@celery.task
def get_source(link_guid, target_url, base_storage_path, user_agent=''):
    """
    Download the source that is used to generate the page at the supplied URL.
    Assets are written to disk, in a directory called "source". If things go well, we update our
    assets model with the path.
    We use a robust wget command for this.

    This function is usually executed via an asynchronous Celery call
    """

    asset = Asset.objects.get(link__guid=link_guid)
    asset.warc_capture = 'pending'
    asset.save()

    path_elements = [settings.GENERATED_ASSETS_STORAGE, base_storage_path, 'source', 'index.html']

    directory = os.path.sep.join(path_elements[:3])

    headers = {
        #'Accept': ','.join(settings.ACCEPT_CONTENT_TYPES),
        #'User-Agent': user_agent,
    }

    """ Get the markup and assets, update our db, and write them to disk """
    # Construct wget command
    command = 'wget '
    command = command + '--quiet ' # turn off wget's output
    command = command + '--tries=' + str(settings.NUMBER_RETRIES) + ' ' # number of retries (assuming no 404 or the like)
    command = command + '--wait=' + str(settings.WAIT_BETWEEN_TRIES) + ' ' # number of seconds between requests (lighten the load on a page that has a lot of assets)
    command = command + '--quota=' + settings.ARCHIVE_QUOTA + ' ' # only store this amount
    command = command + '--random-wait ' # random wait between .5 seconds and --wait=
    command = command + '--limit-rate=' + settings.ARCHIVE_LIMIT_RATE  + ' ' # we'll be performing multiple archives at once. let's not download too much in one stream
    command = command + '--adjust-extension '  # if a page is served up at .asp, adjust to .html. (this is the new --html-extension flag)
    command = command + '--span-hosts ' # sometimes things like images are hosted at a CDN. let's span-hosts to get those
    command = command + '--convert-links ' # rewrite links in downloaded source so they can be viewed in our local version
    command = command + '-e robots=off ' # we're not crawling, just viewing the page exactly as you would in a web-browser.
    command = command + '--page-requisites ' # get the things required to render the page later. things like images.
    command = command + '--no-directories ' # when downloading, flatten the source. we don't need a bunch of dirs.
    command = command + '--no-check-certificate ' # We don't care too much about busted certs
    command = command + '--user-agent="' + user_agent + '" ' # pass through our user's user agent
    command = command + '--directory-prefix=' + directory + ' ' # store our downloaded source in this directory

    # Add headers (defined earlier in this function)
    for key, value in headers.iteritems():
        command = command + '--header="' + key + ': ' + value + '" '

    command = command + target_url

    # Download page data and dependencies
    if not os.path.exists(directory):
        os.makedirs(directory)

    #TODO replace os.popen with subprocess
    output = os.popen(command)

    # Verify success
    if '400 Bad Request' in output:
        logger.info("Source capture failed for %s" % target_url)
        asset = Asset.objects.get(link__guid=link_guid)
        asset.warc_capture = 'failed'
        asset.save()

    filename = urllib.unquote(target_url.split('/')[-1]).decode('utf8')
    if filename != '' and 'index.html' not in os.listdir(directory):
        try:
            src = os.path.join(directory, filename)
            des = os.path.sep.join(path_elements)
            shutil.move(src, des)
        except:
            # Rename the file as index.html if it contains '<html'
            counter = 0
            for filename in glob.glob(directory + '/*'):
                with open(filename) as f:
                    if '<html' in f.read():
                        shutil.move(os.path.join(directory, filename), os.path.sep.join(path_elements))
                        counter = counter + 1
            if counter == 0:
                # If we still don't have an index.html file, raise an exception and record it to the DB
                asset = Asset.objects.get(link__guid=link_guid)
                asset.warc_capture = 'failed'
                asset.save()

                logger.info("Source capture got some content, but couldn't rename to index.html for %s" % target_url)
                os.system('rm -rf ' + directory)

    if os.path.exists(os.path.sep.join(path_elements)):
        asset = Asset.objects.get(link__guid=link_guid)
        asset.warc_capture = os.path.sep.join(path_elements[2:])
        asset.save()


@celery.task
def get_pdf(link_guid, target_url, base_storage_path, user_agent):
    """
    Dowload a PDF from the network

    This function is usually executed via a synchronous Celery call
    """
    asset = Asset.objects.get(link__guid=link_guid)
    asset.pdf_capture = 'pending'
    asset.save()
    
    path_elements = [settings.GENERATED_ASSETS_STORAGE, base_storage_path, 'cap.pdf']

    if not os.path.exists(os.path.sep.join(path_elements[:2])):
        os.makedirs(os.path.sep.join(path_elements[:2]))

    # Get the PDF from the network
    headers = {
        'User-Agent': user_agent,
    }
    r = requests.get(target_url, stream = True, headers=headers)
    file_path = os.path.sep.join(path_elements)

    with open(file_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()

    if os.path.exists(os.path.sep.join(path_elements)):
        # TODO: run some sort of validation check on the PDF
        asset.pdf_capture = os.path.sep.join(path_elements[2:])
        asset.save()
    else:
        logger.info("PDF capture failed for %s" % target_url)
        asset.pdf_capture = 'failed'
        asset.save()

        raise BrokenURLError(target_url)


def instapaper_capture(url, title):
    consumer = oauth.Consumer(INSTAPAPER_KEY, INSTAPAPER_SECRET)
    client = oauth.Client(consumer)

    resp, content = client.request('https://www.instapaper.com/api/1/oauth/access_token', "POST", urllib.urlencode({
                'x_auth_mode': 'client_auth',
                'x_auth_username': INSTAPAPER_USER,
                'x_auth_password': INSTAPAPER_PASS,
                }))

    token = dict(urlparse.parse_qsl(content))
    token = oauth.Token(token['oauth_token'], token['oauth_token_secret'])
    http = oauth.Client(consumer, token)

    response, data = http.request('https://www.instapaper.com/api/1/bookmarks/add', method='POST', body=urllib.urlencode({'url':url, 'title': title}))

    res = simplejson.loads(data)

    bid = res[0]['bookmark_id']

    tresponse, tdata = http.request('https://www.instapaper.com/api/1/bookmarks/get_text', method='POST', body=urllib.urlencode({'bookmark_id':bid}))

    return bid, tdata

@celery.task
def store_text_cap(url, title, asset):
    bid, tdata = instapaper_capture(url, title)
    asset.instapaper_timestamp = datetime.datetime.now()
    h = smhasher.murmur3_x86_128(tdata)
    asset.instapaper_hash = h
    file_path = GENERATED_ASSETS_STORAGE + '/' + asset.base_storage_path
    if not os.path.exists(file_path):
        os.makedirs(file_path)


    f = open(file_path + '/instapaper_cap.html', 'w')
    f.write(tdata)
    os.fsync(f)
    f.close

    asset.instapaper_id = bid
    asset.save()
