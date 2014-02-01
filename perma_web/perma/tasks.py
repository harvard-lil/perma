import os
import subprocess
import urllib
import glob
import shutil
import urlparse
import simplejson
import datetime
import smhasher
import logging
import robotparser
import re
import time
import oauth2 as oauth
import warcprox.warcprox as warcprox
import thread
from djcelery import celery
import lxml.html
import requests
import errno
from socket import error as socket_error

from django.conf import settings

from perma.models import Asset, Stat, Registrar, LinkUser, Link, VestingOrg
from perma.exceptions import BrokenURLError
from perma.settings import INSTAPAPER_KEY, INSTAPAPER_SECRET, INSTAPAPER_USER, INSTAPAPER_PASS, GENERATED_ASSETS_STORAGE


logger = logging.getLogger(__name__)


# helpers
def get_asset_query(link_guid):
    # we use Asset.objects.filter().update() style updates to avoid race conditions or blocking caused by loading and saving same asset in different threads
    return Asset.objects.filter(link__guid=link_guid)

def get_storage_path(base_storage_path):
    return os.path.join(settings.GENERATED_ASSETS_STORAGE, base_storage_path)

def create_storage_dir(storage_path):
    if not os.path.exists(storage_path):
        try:
            os.makedirs(storage_path)
        except OSError, e:
            # if we get OSError(17, 'File exists'), ignore it -- another thread made the dir at the same time
            if e.errno != 17:
                raise


@celery.task
def start_proxy_record_get_screen_cap(link_guid, target_url, base_storage_path ,user_agent=''):
    """
    start warcprox process. Warcprox is a MITM proxy server and needs to be running 
    before, during and after phantomjs gets a screenshot.

    Create an image from the supplied URL, write it to disk and update our asset model with the path.
    The heavy lifting is done by PhantomJS, our headless browser.

    This function is usually executed via a synchronous Celery call
    """
    # basic setup
    asset_query = get_asset_query(link_guid)
    storage_path = get_storage_path(base_storage_path)
    create_storage_dir(storage_path)

    # set up storage paths
    image_name = 'cap.png'
    warc_name = 'archive.warc.gz'
    image_path = os.path.join(storage_path, image_name)
    cert_path = os.path.join(storage_path, 'cert.pem')

    # connect warcprox to an open port
    prox_port = 27500
    recorded_url_q = warcprox.queue.Queue()
    for i in xrange(500):
        try:
            proxy = warcprox.WarcProxy(
                server_address=("127.0.0.1", prox_port),
                ca=warcprox.CertificateAuthority(cert_path, storage_path),
                recorded_url_q=recorded_url_q
            )
            break
        except socket_error as e:
            if e.errno != errno.EADDRINUSE:
                raise
        prox_port += 1
    else:
        raise Exception("WarcProx couldn't find an open port.")

    # create a WarcWriterThread subclass that knows how to rename resulting warc and save to DB when closing warc file
    class WarcWriter(warcprox.WarcWriterThread):
        def _close_writer(self):
            if self._fpath:
                super(WarcWriter, self)._close_writer()
                standardized_warc_name = os.path.join(storage_path, warc_name)
                try:
                    os.rename(os.path.join(storage_path, self._f_finalname), standardized_warc_name)
                    asset_query.update(warc_capture=warc_name)
                except OSError:
                    logger.info("Web Archive File creation failed for %s" % target_url)
                    asset_query.update(warc_capture='failed')

    # start warcprox listener
    warc_writer = WarcWriter(recorded_url_q=recorded_url_q,
                                   directory=storage_path, gzip=True,
                                   port=prox_port,
                                   rollover_idle_time=15)
    warcprox_controller = warcprox.WarcproxController(proxy, warc_writer)
    thread.start_new_thread(warcprox_controller.run_until_shutdown, ())

    # run phantomjs
    try:
        subprocess.call([
            settings.PHANTOMJS_BINARY,
            "--proxy=127.0.0.1:%s" % prox_port,
            "--ssl-certificates-path=%s" % cert_path,
            "--ignore-ssl-errors=true",
            os.path.join(settings.PROJECT_ROOT, 'lib/rasterize.js'),
            target_url,
            image_path,
            user_agent
        ])
        time.sleep(.5) # give warcprox a chance to save everything
    finally:
        # shutdown warcprox process
        warcprox_controller.stop.set()

    # save screenshot asset
    if os.path.exists(image_path):
        asset_query.update(image_capture="/"+image_name)
    else:
        asset_query.update(image_capture='failed')
        logger.info("Screen capture failed for %s" % target_url)


@celery.task
def get_pdf(link_guid, target_url, base_storage_path, user_agent):
    """
    Download a PDF from the network

    This function is usually executed via a synchronous Celery call
    """
    # basic setup
    asset_query = get_asset_query(link_guid)
    storage_path = get_storage_path(base_storage_path)
    create_storage_dir(storage_path)

    pdf_name = 'cap.pdf'
    pdf_path = os.path.join(storage_path, pdf_name)

    # Get the PDF from the network
    r = requests.get(target_url, stream = True, headers={'User-Agent': user_agent})

    try:
        with open(pdf_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
            
                # Limit our filesize
                if f.tell() > settings.MAX_ARCHIVE_FILE_SIZE:
                    raise
                
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
                    
    except Exception, e:
        logger.info("PDF capture too big, %s" % target_url)
        os.remove(pdf_path)

    if os.path.exists(pdf_path):
        # TODO: run some sort of validation check on the PDF
        asset_query.update(pdf_capture=pdf_name)
    else:
        logger.info("PDF capture failed for %s" % target_url)
        asset_query.update(pdf_capture='failed')


def instapaper_capture(url, title):
    consumer = oauth.Consumer(INSTAPAPER_KEY, INSTAPAPER_SECRET)
    client = oauth.Client(consumer)

    resp, content = client.request('https://www.instapaper.com/api/1/oauth/access_token', "POST", urllib.urlencode({
                'x_auth_mode': 'client_auth',
                'x_auth_username': INSTAPAPER_USER,
                'x_auth_password': INSTAPAPER_PASS,
                }))

    token = dict(urlparse.parse_qsl(content))
    try:
        token = oauth.Token(token['oauth_token'], token['oauth_token_secret'])
    except KeyError:
        return None, None, False # login failed -- maybe no instapaper config in settings
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
def store_text_cap(link_guid, target_url, base_storage_path, title):
    # basic setup
    asset_query = get_asset_query(link_guid)
    storage_path = get_storage_path(base_storage_path)
    create_storage_dir(storage_path)

    bid, tdata, success = instapaper_capture(target_url, title)
    
    if success:
        with open(storage_path + '/instapaper_cap.html', 'wb') as f:
            f.write(tdata)

        if os.path.exists(storage_path + '/instapaper_cap.html'):
            text_capture = 'instapaper_cap.html'
        else:
            logger.info("Text (instapaper) capture failed for %s" % target_url)
            text_capture = 'failed'

        asset_query.update(
            text_capture=text_capture,
            instapaper_timestamp=datetime.datetime.now(),
            instapaper_hash=smhasher.murmur3_x86_128(tdata),
            instapaper_id=bid
        )
    else:
        # Must have received something other than an HTTP 200 from Instapaper, or no response object at all
        logger.info("Text (instapaper) capture failed for %s" % target_url)
        asset_query.update(text_capture='failed')


@celery.task
def get_robots_txt(url, link_guid, content):
    """
    A task (hopefully called asynchronously) to get the meta element for a
    noarchive value andto get the robots.txt rule for PermaBot.
    We will still grab the content (we're not a crawler), but we'll "darchive
    it."
    
    If we see a "noarchive" value for a meta element with the name 'robots' or
    'permabot' we'll send the arvhive to the darachive.
    
    If we don't see noarchive rule in a meta element, check the robots.txt to 
    see if permabot is specifically denied.
    """
    
    # Sometimes we don't get markup. Only look for meta values if we get markup
    if content:
        parsed_html = lxml.html.fromstring(content)
        metas = parsed_html.xpath('//meta')
        
        # Look at all meta elements and grab any that have a name of 'robots' or
        # 'permabot'. If we see any, send to the darchive if the have a value
        # of 'noarchive' in the 'content atrribute'
        # So, something like this will be sent to the darchive:
        # <meta name="ROBOTS" content="NOARCHIVE" />
        for meta in metas:
            meta_name = meta.get('name')
            if meta_name and meta_name.lower() in ['robots', 'permabot']:
                meta_content = meta.get('content')
                if meta_content:
                    bot_values = meta_content.split(',')
                    bot_values = [item.lower() for item in bot_values]
                    if 'noarchive' in bot_values:
                        link = Link.objects.get(guid=link_guid)
                        link.dark_archived_robots_txt_blocked = True
                        link.save()

                        return
    
    # Didn't see a noarchive value in a meta element. let's look at robots.txt
    
    # Parse the URL so and build the robots.txt location
    parsed_url = urlparse.urlparse(url)
    robots_text_location = parsed_url.scheme + '://' + parsed_url.netloc + '/robots.txt'
    
    # We only want to respect robots.txt if PermaBot is specifically asked not crawl (we're not a crawler)
    response = requests.get(robots_text_location)
    
    # We found PermaBot specifically mentioned
    if re.search('PermaBot', response.text) is not None:
        # Get the robots.txt ruleset
        # TODO: use reppy or something else here. it's dumb that we're
        # getting robots.txt twice
        rp = robotparser.RobotFileParser()
        rp.set_url(robots_text_location)
        rp.read()

        # If we're not allowed, set a flag in the model
        if not rp.can_fetch('PermaBot', url):
            link = Link.objects.get(guid=link_guid)
            link.dark_archived_robots_txt_blocked = True
            link.save()


    
@celery.task
def get_nigthly_stats():
    """
    A periodic task (probably running nightly) to get counts of user types, disk usage.
    Write them into a DB for our stats view
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
    total_vesting_orgs = VestingOrg.objects.all().count()
    
    # Two types of links
    total_count_unvested_links = Link.objects.filter(vested=False).count()
    total_count_vested_links = Link.objects.filter(vested=True).count()
    
    # Get things in the darchive
    total_count_darchive_takedown_links = Link.objects.filter(dark_archived=True).count()
    total_count_darchive_robots_links = Link.objects.filter(dark_archived_robots_txt_blocked=True).count()
    
    # Get the path of yesterday's file storage tree
    now = datetime.datetime.now() - datetime.timedelta(days=1)
    time_tuple = now.timetuple()
    path_elements = [str(time_tuple.tm_year), str(time_tuple.tm_mon), str(time_tuple.tm_mday)]
    disk_path = settings.GENERATED_ASSETS_STORAGE + '/' + os.path.sep.join(path_elements)
    
    # Get disk usage total
    # If we start deleting unvested archives, we'll have to do some periodic corrrections here (this is only additive)
    # Get the sum of the diskspace of all files in yesterday's tree
    latest_day_usage = 0
    for root, dirs, files in os.walk(disk_path):
        latest_day_usage = latest_day_usage + sum(os.path.getsize(os.path.join(root, name)) for name in files)
        
    # Get the total disk usage (that we calculated yesterday)
    stat = Stat.objects.all().order_by('-creation_timestamp')[:1]
    
    # Sum total usage with yesterday's usage
    new_total_disk_usage = stat[0].disk_usage + latest_day_usage
    
    # We've now gathered all of our data. Let's write it to the model
    stat = Stat(
        regular_user_count=total_count_regular_users,
        vesting_member_count=total_count_vesting_members,
        vesting_manager_count=total_count_vesting_managers,
        registrar_member_count=total_count_registrar_members,
        registry_member_count=total_count_registry_members,
        registrar_count=total_count_registrars,
        vesting_org_count=total_vesting_orgs,
        unvested_count=total_count_unvested_links,
        darchive_takedown_count = total_count_darchive_takedown_links,
        darchive_robots_count = total_count_darchive_robots_links,
        vested_count=total_count_vested_links,
        disk_usage = new_total_disk_usage,
        )

    stat.save()