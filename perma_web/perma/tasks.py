import os
import subprocess
import threading
import urllib
import glob
import shutil
import urlparse
from django.core.files.storage import default_storage
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import ProxyType
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


logger = logging.getLogger(__name__)


### HELPERS ###

def get_asset_query(link_guid):
    # we use Asset.objects.filter().update() style updates to avoid race conditions or blocking caused by loading and saving same asset in different threads
    return Asset.objects.filter(link__guid=link_guid)

def get_link_query(link_guid):
    # we use Link.objects.filter().update() style updates to avoid race conditions or blocking caused by loading and saving same asset in different threads
    return Link.objects.filter(pk=link_guid)

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

def save_screenshot(driver, image_path):
    """ Given selenium webdriver and path, save screenshot using Django's default_storage. """
    png_data = driver.get_screenshot_as_png()
    with default_storage.open(image_path, 'wb') as image_file:
        image_file.write(png_data)

def get_browser(user_agent, proxy_address, cert_path):
    """ Set up a Selenium browser with given user agent, proxy and SSL cert. """
    desired_capabilities = dict(DesiredCapabilities.PHANTOMJS)
    desired_capabilities["phantomjs.page.settings.userAgent"] = user_agent
    desired_capabilities["proxy"] = {"proxyType":ProxyType.MANUAL,"sslProxy":proxy_address,"httpProxy":proxy_address}
    browser = webdriver.PhantomJS(desired_capabilities=desired_capabilities,
                                  service_args=[
                                      "--proxy=%s" % proxy_address,
                                      "--ssl-certificates-path=%s" % cert_path,
                                      "--ignore-ssl-errors=true",
                                  ],
                                  service_log_path=settings.PHANTOMJS_LOG)
    browser.implicitly_wait(30)
    browser.set_page_load_timeout(30)
    return browser

### TASKS ##

@celery.task(bind=True)
def proxy_capture(self, link_guid, target_url, base_storage_path ,user_agent=''):
    """
    start warcprox process. Warcprox is a MITM proxy server and needs to be running 
    before, during and after phantomjs gets a screenshot.

    Create an image from the supplied URL, write it to disk and update our asset model with the path.
    The heavy lifting is done by PhantomJS, our headless browser.
    """
    # basic setup
    asset_query = get_asset_query(link_guid)
    link_query = get_link_query(link_guid)
    storage_path = get_storage_path(base_storage_path)
    create_storage_dir(storage_path)
    image_name = 'cap.png'
    warc_name = 'archive.warc.gz'
    image_path = os.path.join(storage_path, image_name)
    cert_path = os.path.join(storage_path, 'cert.pem')

    # connect warcprox to an open port
    warcprox_port = 27500
    recorded_url_queue = warcprox.queue.Queue()
    for i in xrange(500):
        try:
            proxy = warcprox.WarcProxy(
                server_address=("127.0.0.1", warcprox_port),
                ca=warcprox.CertificateAuthority(cert_path, storage_path),
                recorded_url_q=recorded_url_queue
            )
            break
        except socket_error as e:
            if e.errno != errno.EADDRINUSE:
                raise
        warcprox_port += 1
    else:
        raise self.retry(exc=Exception("WarcProx couldn't find an open port."))
    proxy_address = "127.0.0.1:%s" % warcprox_port

    # start warcprox listener
    warc_writer = warcprox.WarcWriterThread(recorded_url_q=recorded_url_queue,
                                   directory=storage_path, gzip=True,
                                   port=warcprox_port,
                                   rollover_idle_time=15)
    warcprox_controller = warcprox.WarcproxController(proxy, warc_writer)
    warcprox_thread = threading.Thread(target=warcprox_controller.run_until_shutdown, name="warcprox", args=())
    warcprox_thread.start()

    # fetch robots.txt in background
    def robots_txt_thread():
        parsed_url = urlparse.urlparse(target_url)
        robots_txt_location = parsed_url.scheme + '://' + parsed_url.netloc + '/robots.txt'
        robots_txt_browser = get_browser(user_agent, proxy_address, cert_path)
        robots_txt_browser.get(robots_txt_location)
        # We only want to respect robots.txt if Perma is specifically asked not crawl (we're not a crawler)
        if 'Perma' in robots_txt_browser.page_source:
            # We found Perma specifically mentioned
            rp = robotparser.RobotFileParser()
            rp.parse([line.strip() for line in robots_txt_browser.page_source])
            if not rp.can_fetch('Perma', target_url):
                link_query.update(dark_archived_robots_txt_blocked=True)
        robots_txt_browser.quit()
    robots_txt_thread = threading.Thread(target=robots_txt_thread, name="robots")
    robots_txt_thread.start()

    # fetch page
    browser = get_browser(user_agent, proxy_address, cert_path)
    browser.set_window_size(1024, 800)
    browser.get(target_url)  # returns after onload

    # get page title
    if browser.title:
        link_query.update(submitted_title=browser.title)

    # save screenshot immediately, and an updated version after 5 seconds
    # (we want to return results quickly, but also give javascript time to render final results)
    save_screenshot(browser, image_path)
    asset_query.update(image_capture=image_name)
    time.sleep(5)
    save_screenshot(browser, image_path)

    # check meta tags
    meta_tag = None
    try:
        # first look for <meta name='perma'>
        meta_tag = browser.find_element_by_xpath("//meta[@name='perma']")
    except NoSuchElementException:
        try:
            # else look for <meta name='robots'>
            browser.find_element_by_xpath("//meta[@name='robots']")
        except NoSuchElementException:
            pass
    if meta_tag and 'noarchive' in meta_tag.get_attribute("content"):
        link_query.update(dark_archived_robots_txt_blocked=True)

    # teardown:
    browser.quit()  # shut down phantomjs
    robots_txt_thread.join()  # wait until robots thread is done
    warcprox_controller.stop.set()  # send signal to shut down warc thread
    warcprox_thread.join()  # wait until warcprox thread is done writing out warc

    # save generated warc file
    temp_warc_path = os.path.join(storage_path, warc_writer._f_finalname)
    final_warc_path = os.path.join(storage_path, warc_name)
    try:
        os.rename(temp_warc_path, final_warc_path)
        if settings.USE_WARC_ARCHIVE:
            asset_query.update(warc_capture=warc_name)
    except OSError as e:
        logger.info("Web Archive File creation failed for %s: %s" % (target_url, e))
        if settings.USE_WARC_ARCHIVE:
            asset_query.update(warc_capture='failed')


@celery.task
def get_source(link_guid, target_url, base_storage_path, user_agent=''):
    """
Download the source that is used to generate the page at the supplied URL.
Assets are written to disk, in a directory called "source". If things go well, we update our
assets model with the path.
We use a robust wget command for this.

This function is usually executed via an asynchronous Celery call
"""
    asset_query = get_asset_query(link_guid)

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
    command = command + '--limit-rate=' + settings.ARCHIVE_LIMIT_RATE + ' ' # we'll be performing multiple archives at once. let's not download too much in one stream
    command = command + '--adjust-extension ' # if a page is served up at .asp, adjust to .html. (this is the new --html-extension flag)
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
        asset_query.update(warc_capture='failed')

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
                asset_query.update(warc_capture='failed')

                logger.info("Source capture got some content, but couldn't rename to index.html for %s" % target_url)
                os.system('rm -rf ' + directory)

    if os.path.exists(os.path.sep.join(path_elements)):
        asset_query.update(warc_capture=os.path.sep.join(path_elements[2:]))
    else:
        logger.info("Source capture failed for %s" % target_url)
        asset_query.update(warc_capture='failed')


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
    r = requests.get(target_url, stream = True, verify=False,
        headers={'User-Agent': user_agent})

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
    consumer = oauth.Consumer(settings.INSTAPAPER_KEY, settings.INSTAPAPER_SECRET)
    client = oauth.Client(consumer)

    resp, content = client.request('https://www.instapaper.com/api/1/oauth/access_token', "POST", urllib.urlencode({
                'x_auth_mode': 'client_auth',
                'x_auth_username': settings.INSTAPAPER_USER,
                'x_auth_password': settings.INSTAPAPER_PASS,
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