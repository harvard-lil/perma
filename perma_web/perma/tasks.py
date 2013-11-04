import os, sys, subprocess, urllib, glob, shutil, urlparse, simplejson, datetime, smhasher, logging
from djcelery import celery
import requests
from django.conf import settings

from perma.models import Asset, Stat, Registrar, LinkUser, Link
from perma.exceptions import BrokenURLError
from perma.settings import INSTAPAPER_KEY, INSTAPAPER_SECRET, INSTAPAPER_USER, INSTAPAPER_PASS, GENERATED_ASSETS_STORAGE

import oauth2 as oauth

logger = logging.getLogger(__name__)

@celery.task
def get_screen_cap(link_guid, target_url, base_storage_path, user_agent=''):
    """
    Create an image from the supplied URL, write it to disk and update our asset model with the path.
    The heavy lifting is done by PhantomJS, our headless browser.

    This function is usually executed via a synchronous Celery call
    """

    path_elements = [settings.GENERATED_ASSETS_STORAGE, base_storage_path, 'cap.png']

    if not os.path.exists(os.path.sep.join(path_elements[:2])):
        os.makedirs(os.path.sep.join(path_elements[:2]))

    image_generation_command = settings.PROJECT_ROOT + '/lib/phantomjs ' + settings.PROJECT_ROOT + '/lib/rasterize.js "' + target_url + '" ' + os.path.sep.join(path_elements) + ' "' + user_agent + '"'

    subprocess.call(image_generation_command, shell=True)


    if os.path.exists(os.path.sep.join(path_elements)):
        asset = Asset.objects.get(link__guid=link_guid)
        asset.image_capture = os.path.sep.join(path_elements[2:])
        asset.save()
    else:
        logger.info("Screen capture failed for %s" % target_url)
        asset = Asset.objects.get(link__guid=link_guid)
        asset.image_capture = 'failed'
        asset.save()
        logger.info("Screen capture failed for %s" % target_url)

@celery.task
def get_source(link_guid, target_url, base_storage_path, user_agent=''):
    """
    Download the source that is used to generate the page at the supplied URL.
    Assets are written to disk, in a directory called "source". If things go well, we update our
    assets model with the path.
    We use a robust wget command for this.

    This function is usually executed via an asynchronous Celery call
    """

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
    else:
        logger.info("Source capture failed for %s" % target_url)
        asset = Asset.objects.get(link__guid=link_guid)
        asset.warc_capture = 'failed'
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

    try:
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
            
                # Limit our filesize
                if f.tell() > settings.MAX_ARCHIVE_FILE_SIZE:
                    raise
                
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
                    
    except Exception, e:
        logger.info("PDF capture too big, %s" % target_url)
        os.remove(file_path)

    if os.path.exists(os.path.sep.join(path_elements)):
        # TODO: run some sort of validation check on the PDF
        asset.pdf_capture = os.path.sep.join(path_elements[2:])
        asset.save()
    else:
        logger.info("PDF capture failed for %s" % target_url)
        asset.pdf_capture = 'failed'
        asset.save()


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

    response, data = http.request('https://www.instapaper.com/api/1/bookmarks/add', method='POST', body=urllib.urlencode({'url':url, 'title': unicode(title).encode('utf-8')}))

    res = simplejson.loads(data)

    bid = res[0]['bookmark_id']

    tresponse, tdata = http.request('https://www.instapaper.com/api/1/bookmarks/get_text', method='POST', body=urllib.urlencode({'bookmark_id':bid}))

    # If didn't get a response or we got something other than an HTTP 200, count it as a failure
    success = True
    if not tresponse or tresponse.status != 200:
        success = False
    
    return bid, tdata, success


@celery.task
def store_text_cap(url, title, link_guid):
    
    bid, tdata, success = instapaper_capture(url, title)
    
    if success:
        asset = Asset.objects.get(link__guid=link_guid)
        asset.instapaper_timestamp = datetime.datetime.now()
        h = smhasher.murmur3_x86_128(tdata)
        asset.instapaper_hash = h
        asset.instapaper_id = bid
        asset.save()
    
        file_path = GENERATED_ASSETS_STORAGE + '/' + asset.base_storage_path
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        f = open(file_path + '/instapaper_cap.html', 'w')
        f.write(tdata)
        os.fsync(f)
        f.close

        if os.path.exists(file_path + '/instapaper_cap.html'):
            asset.text_capture = 'instapaper_cap.html'
            asset.save()
        else:
            logger.info("Text (instapaper) capture failed for %s" % target_url)
            asset.text_capture = 'failed'
            asset.save()
    else:
        # Must have received something other than an HTTP 200 from Instapaper, or no response object at all
        logger.info("Text (instapaper) capture failed for %s" % target_url)
        asset = Asset.objects.get(link__guid=link_guid)
        asset.text_capture = 'failed'
        asset.save()
    
    
@celery.task
def get_nigthly_stats():
    """
    A periodic task (probably running nightly) to get counts of user types
    and jam them into a DB for our stats view
    """
    
    # Five types user accounts
    total_count_regular_users = LinkUser.objects.filter(groups__name='user').count()
    total_count_vesting_members = LinkUser.objects.filter(groups__name='vesting_member').count()
    total_count_vesting_managers = LinkUser.objects.filter(groups__name='vesting_manager').count()
    total_count_registrar_members = LinkUser.objects.filter(groups__name='registrar_member').count()
    total_count_registry_members = LinkUser.objects.filter(groups__name='registry_member').count()
    
    # Registrar count
    total_count_registrars = Registrar.objects.all().count()
    
    # Journal account
    # TODO: add this in when Annie merges in the journal account logic
    
    # Two types of links
    total_count_unvested_links = Link.objects.filter(vested=False).count()
    total_count_vested_links = Link.objects.filter(vested=True).count()
    
    # Size count
    # TODO: we probably shouldn't be doing this every night. since we split our dirs based on
    # dates, we can obviously traverse just the day's dir and add it to the previous number
    f = settings.GENERATED_ASSETS_STORAGE
    
    total_disk_usage = 0
    for root, dirs, files in os.walk(GENERATED_ASSETS_STORAGE):
        total_disk_usage = total_disk_usage + sum(os.path.getsize(os.path.join(root, name)) for name in files)
    
    # We've now gathered all of our data. Let's write it to the model.
    stat = Stat(
        regular_user_count=total_count_regular_users,
        vesting_member_count=total_count_vesting_members,
        vesting_manager_count=total_count_vesting_managers,
        registrar_member_count=total_count_registrar_members,
        registry_member_count=total_count_registry_members,
        registrar_count=total_count_registrars,
        #todo: put journal count here
        unvested_count=total_count_unvested_links,
        vested_count=total_count_vested_links,
        disk_usage = total_disk_usage,
        )

    stat.save()