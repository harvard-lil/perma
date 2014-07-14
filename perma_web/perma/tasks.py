from __future__ import absolute_import # to avoid importing local .celery instead of celery package

import os
import os.path
import tempfile
import threading
import urlparse
from celery import shared_task
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import ProxyType
import datetime
import logging
import robotparser
import time
import warcprox.warcprox as warcprox
import requests
import errno
import tempdir
from socket import error as socket_error

from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.template.loader import get_template
from django.template import Context
from django.forms.models import model_to_dict
from django.conf import settings

from perma.models import Asset, Stat, Registrar, LinkUser, Link, VestingOrg


logger = logging.getLogger(__name__)

### CONSTANTS ###

ROBOTS_TXT_TIMEOUT = 30 # seconds to wait before giving up on robots.txt
PAGE_LOAD_TIMEOUT = 60 # seconds to wait before proceeding as though onLoad event fired
ELEMENT_DISCOVERY_TIMEOUT = 2 # seconds before PhantomJS gives up running a DOM request (should be instant, assuming page is loaded)
AFTER_LOAD_TIMEOUT = 60 # seconds to allow page to keep loading additional resources after onLoad event fires

### HELPERS ###

def get_asset_query(link_guid):
    # we use Asset.objects.filter().update() style updates to avoid race conditions or blocking caused by loading and saving same asset in different threads
    return Asset.objects.filter(link__guid=link_guid)

def get_link_query(link_guid):
    # we use Link.objects.filter().update() style updates to avoid race conditions or blocking caused by loading and saving same asset in different threads
    return Link.objects.filter(pk=link_guid)

def get_storage_path(base_storage_path):
    return os.path.join(settings.MEDIA_ROOT, base_storage_path)

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
    return default_storage.store_data_to_file(png_data, image_path, overwrite=True)

def get_browser(user_agent, proxy_address, cert_path):
    """ Set up a Selenium browser with given user agent, proxy and SSL cert. """
    desired_capabilities = dict(DesiredCapabilities.PHANTOMJS)
    desired_capabilities["phantomjs.page.settings.userAgent"] = user_agent
    desired_capabilities["proxy"] = {"proxyType":ProxyType.MANUAL,"sslProxy":proxy_address,"httpProxy":proxy_address}
    browser = webdriver.PhantomJS(
        executable_path=getattr(settings, 'PHANTOMJS_BINARY', 'phantomjs'),
        desired_capabilities=desired_capabilities,
        service_args=[
            "--proxy=%s" % proxy_address,
            "--ssl-certificates-path=%s" % cert_path,
            "--ignore-ssl-errors=true",],
        service_log_path=settings.PHANTOMJS_LOG)
    browser.implicitly_wait(ELEMENT_DISCOVERY_TIMEOUT)
    browser.set_page_load_timeout(ROBOTS_TXT_TIMEOUT)
    return browser


### TASKS ##

@shared_task(bind=True)
@tempdir.run_in_tempdir()
def proxy_capture(self, link_guid, target_url, base_storage_path, user_agent=''):
    """
    start warcprox process. Warcprox is a MITM proxy server and needs to be running 
    before, during and after phantomjs gets a screenshot.

    Create an image from the supplied URL, write it to disk and update our asset model with the path.
    The heavy lifting is done by PhantomJS, our headless browser.

    This whole function runs with the local dir set to a temp dir by run_in_tempdir().
    So we can use local paths for temp files, and they'll just disappear when the function exits.
    """
    # basic setup

    asset_query = get_asset_query(link_guid)
    link_query = get_link_query(link_guid)
    image_name = 'cap.png'
    warc_name = 'archive.warc.gz'
    image_path = os.path.join(base_storage_path, image_name)
    warc_path = os.path.join(base_storage_path, warc_name)

    print "%s: Fetching %s" % (link_guid, target_url)

    # create a request handler class that counts unique requests and responses
    #global unique_requests, unique_responses
    unique_requests = set()
    unique_responses = set()
    count_lock = threading.Lock()
    class CountingRequestHandler(warcprox.WarcProxyHandler):
        def _proxy_request(self):
            #global unique_requests, unique_responses
            with count_lock:
                unique_requests.add(self.url)
            warcprox.WarcProxyHandler._proxy_request(self)
            with count_lock:
                unique_responses.add(self.url)

    # connect warcprox to an open port
    warcprox_port = 27500
    recorded_url_queue = warcprox.queue.Queue()
    fake_cert_authority = warcprox.CertificateAuthority()
    for i in xrange(500):
        try:
            proxy = warcprox.WarcProxy(
                server_address=("127.0.0.1", warcprox_port),
                ca=fake_cert_authority,
                recorded_url_q=recorded_url_queue,
                req_handler_class=CountingRequestHandler
            )
            break
        except socket_error as e:
            if e.errno != errno.EADDRINUSE:
                raise
        warcprox_port += 1
    else:
        raise self.retry(exc=Exception("WarcProx couldn't find an open port."))
    proxy_address = "127.0.0.1:%s" % warcprox_port

    # start warcprox in the background
    warc_writer = warcprox.WarcWriterThread(recorded_url_q=recorded_url_queue, gzip=True, port=warcprox_port)
    warcprox_controller = warcprox.WarcproxController(proxy, warc_writer)
    warcprox_thread = threading.Thread(target=warcprox_controller.run_until_shutdown, name="warcprox", args=())
    warcprox_thread.start()

    print "WarcProx opened."

    # fetch robots.txt in the background
    def robots_txt_thread():
        print "Fetching robots.txt ..."
        parsed_url = urlparse.urlparse(target_url)
        robots_txt_location = parsed_url.scheme + '://' + parsed_url.netloc + '/robots.txt'
        robots_txt_browser = get_browser(user_agent, proxy_address, fake_cert_authority.ca_file)
        robots_txt_browser.get(robots_txt_location)
        # We only want to respect robots.txt if Perma is specifically asked not crawl (we're not a crawler)
        if 'Perma' in robots_txt_browser.page_source:
            # We found Perma specifically mentioned
            rp = robotparser.RobotFileParser()
            rp.parse([line.strip() for line in robots_txt_browser.page_source])
            if not rp.can_fetch('Perma', target_url):
                link_query.update(dark_archived_robots_txt_blocked=True)
        robots_txt_browser.quit()
        print "Robots.txt fetched."
    robots_txt_thread = threading.Thread(target=robots_txt_thread, name="robots")
    robots_txt_thread.start()

    # fetch page in the background
    # (we'll give
    print "Fetching url."
    browser = get_browser(user_agent, proxy_address, fake_cert_authority.ca_file)
    browser.set_window_size(1024, 800)
    page_load_thread = threading.Thread(target=browser.get, args=(target_url,))  # returns after onload
    page_load_thread.start()
    page_load_thread.join(PAGE_LOAD_TIMEOUT)
    if page_load_thread.is_alive():
        print "Waited 60 seconds for onLoad event -- giving up."
        if not unique_responses:
            # if nothing at all has loaded yet, give up on the capture
            asset_query.update(warc_capture='failed', image_capture='failed')
            browser.quit()  # shut down phantomjs
            robots_txt_thread.join()  # wait until robots thread is done
            warcprox_controller.stop.set()  # send signal to shut down warc thread
            warcprox_thread.join()
            return
    print "Finished fetching url."

    # get page title
    print "Getting title."
    if browser.title:
        link_query.update(submitted_title=browser.title)

    # check meta tags
    # (run this in a thread and give it long enough to find the tags, but then let other stuff proceed)
    print "Checking meta tags."
    def meta_thread():
        meta_tag = None
        try:
            # first look for <meta name='perma'>
            meta_tag = browser.find_element_by_xpath("//meta[@name='perma']")
        except NoSuchElementException:
            try:
                # else look for <meta name='robots'>
                meta_tag = browser.find_element_by_xpath("//meta[@name='robots']")
            except NoSuchElementException:
                pass
        if meta_tag and 'noarchive' in meta_tag.get_attribute("content"):
            link_query.update(dark_archived_robots_txt_blocked=True)
    meta_thread = threading.Thread(target=meta_thread)
    meta_thread.start()
    meta_thread.join(ELEMENT_DISCOVERY_TIMEOUT*2)

    # save preliminary screenshot immediately, and an updated version later
    # (we want to return results quickly, but also give javascript time to render final results)
    print "Saving first screenshot."
    save_screenshot(browser, image_path)
    asset_query.update(image_capture=image_name)

    # make sure all requests are finished
    print "Waiting for post-load requests."
    start_time = time.time()
    time.sleep(5)
    while len(unique_responses) < len(unique_requests):
        print "%s/%s finished" % (len(unique_responses), len(unique_requests))
        if time.time() - start_time > AFTER_LOAD_TIMEOUT:
            print "Waited 60 seconds to finish post-load requests -- giving up."
            break
        time.sleep(.5)

    # take second screenshot after all requests done
    print "Taking second screenshot."
    save_screenshot(browser, image_path)

    print "Shutting down browser and proxies."
    # teardown:
    browser.quit()  # shut down phantomjs
    robots_txt_thread.join()  # wait until robots thread is done
    meta_thread.join()  # wait until meta thread is done
    warcprox_controller.stop.set()  # send signal to shut down warc thread
    warcprox_thread.join()  # wait until warcprox thread is done writing out warc

    print "Saving WARC."
    # save generated warc file
    temp_warc_path = os.path.join(warc_writer.directory, warc_writer._f_finalname)
    try:
        with open(temp_warc_path, 'rb') as warc_file:
            warc_name = default_storage.store_file(warc_file, warc_path)
            asset_query.update(warc_capture=warc_name)
    except Exception as e:
        logger.info("Web Archive File creation failed for %s: %s" % (target_url, e))
        asset_query.update(warc_capture='failed')

    print "%s capture done." % link_guid


@shared_task
def get_pdf(link_guid, target_url, base_storage_path, user_agent):
    """
    Download a PDF from the network

    This function is executed via an asynchronous Celery call
    """

    # basic setup
    asset_query = get_asset_query(link_guid)
    pdf_name = 'cap.pdf'
    pdf_path = os.path.join(base_storage_path, pdf_name)

    # Get the PDF from the network
    pdf_request = requests.get(target_url, stream = True, verify=False,
        headers={'User-Agent': user_agent})

    # write PDF out to a temp file
    temp = tempfile.TemporaryFile()
    for chunk in pdf_request.iter_content(chunk_size=1024):

        if chunk: # filter out keep-alive new chunks
            temp.write(chunk)
            temp.flush()

        # Limit our filesize
        if temp.tell() > settings.MAX_ARCHIVE_FILE_SIZE:
            logger.info("PDF capture too big, %s" % target_url)
            asset_query.update(pdf_capture='failed')
            return

    # store temp file
    temp.seek(0)
    pdf_name = default_storage.store_file(temp, pdf_path)
    asset_query.update(pdf_capture=pdf_name)


@shared_task
def get_nightly_stats():
    """
    A periodic task (probably running nightly) to get counts of user types, disk usage.
    Write them into a DB for our stats view
    """
    
    # Five types user accounts
    total_count_regular_users = LinkUser.objects.filter(groups__name='user').count()
    total_count_vesting_members = LinkUser.objects.filter(groups__name='vesting_user').count()
    total_count_registrar_members = LinkUser.objects.filter(groups__name='registrar_user').count()
    total_count_registry_members = LinkUser.objects.filter(groups__name='registry_user').count()
    
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
    disk_path = settings.MEDIA_ROOT + '/' + os.path.sep.join(path_elements)
    
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

@shared_task
def email_weekly_stats():
    """
    We bundle up our stats weekly and email them to a developer and then
    onto our interested mailing lists
    """

    previous_stats_query_set = Stat.objects.order_by('-creation_timestamp')[:8][7]
    current_stats_query_set = Stat.objects.filter().latest('creation_timestamp')

    format = '%b %d, %Y, %H:%M %p'

    context = {
        'start_time': previous_stats_query_set.creation_timestamp.strftime(format),
        'end_time': current_stats_query_set.creation_timestamp.strftime(format),
    }

    # Convert querysets to dicts so that we can access them easily in our print_stats_line util
    previous_stats = model_to_dict(previous_stats_query_set)
    current_stats = model_to_dict(current_stats_query_set)

    context.update({
        'num_regular_users_added': current_stats['regular_user_count'] - previous_stats['regular_user_count'],
        'prev_regular_users_count': previous_stats['regular_user_count'],
        'current_regular_users_count': current_stats['regular_user_count'],

        'num_vesting_members_added': current_stats['vesting_member_count'] - previous_stats['vesting_member_count'],
        'prev_vesting_members_count': previous_stats['vesting_member_count'],
        'current_vesting_members_count': current_stats['vesting_member_count'],

        'num_registar_members_added': current_stats['registrar_member_count'] - previous_stats['registrar_member_count'],
        'prev_registrar_members_count': previous_stats['registrar_member_count'],
        'current_registrar_members_count': current_stats['registrar_member_count'],

        'num_registry_members_added': current_stats['registry_member_count'] - previous_stats['registry_member_count'],
        'prev_registry_members_count': previous_stats['registry_member_count'],
        'current_registry_members_count': current_stats['registry_member_count'],

        'num_vesting_orgs_added': current_stats['vesting_org_count'] - previous_stats['vesting_org_count'],
        'prev_vesting_orgs_count': previous_stats['vesting_org_count'],
        'current_vesting_orgs_count': current_stats['vesting_org_count'],

        'num_registrars_added': current_stats['registrar_count'] - previous_stats['registrar_count'],
        'prev_registrars_count': previous_stats['registrar_count'],
        'current_registrars_count': current_stats['registrar_count'],

        'num_unvested_links_added': current_stats['unvested_count'] - previous_stats['unvested_count'],
        'prev_unvested_links_count': previous_stats['unvested_count'],
        'current_unvested_links_count': current_stats['unvested_count'],

        'num_vested_links_added': current_stats['vested_count'] - previous_stats['vested_count'],
        'prev_vested_links_count': previous_stats['vested_count'],
        'current_vested_links_count': current_stats['vested_count'],

        'num_darchive_takedown_added': current_stats['darchive_takedown_count'] - previous_stats['darchive_takedown_count'],
        'prev_darchive_takedown_count': previous_stats['darchive_takedown_count'],
        'current_darchive_takedown_count': current_stats['darchive_takedown_count'],

        'num_darchive_robots_added': current_stats['darchive_robots_count'] - previous_stats['darchive_robots_count'],
        'prev_darchive_robots_count': previous_stats['darchive_robots_count'],
        'current_darchive_robots_count': current_stats['darchive_robots_count'],

        'disk_added': float(current_stats['disk_usage'] - previous_stats['disk_usage'])/1024/1024/1024,
        'prev_disk': float(previous_stats['disk_usage'])/1024/1024/1024,
        'current_disk': float(current_stats['disk_usage'])/1024/1024/1024,
    })

    send_mail(
        'This week in Perma.cc -- the numbers',
        get_template('email/stats.html').render(
            Context(context)
        ),
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEVELOPER_EMAIL],
        fail_silently = False
    )


