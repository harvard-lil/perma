from __future__ import absolute_import # to avoid importing local .celery instead of celery package

from functools import wraps
import json
import os
import os.path
import threading
import urlparse
from celery import shared_task, Task
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import ProxyType
import datetime
import logging
import robotparser
import time
import requests
import errno
import tempdir
from socket import error as socket_error
import internetarchive
import Queue as queue
from warcprox.controller import WarcproxController
from warcprox.warcprox import WarcProxyHandler, WarcProxy
from warcprox.warcwriter import WarcWriter, WarcWriterThread

from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.template.loader import get_template
from django.template import Context
from django.template.defaultfilters import truncatechars
from django.forms.models import model_to_dict
from django.conf import settings

from perma.models import Asset, Stat, Registrar, LinkUser, Link, Organization, CDXLine, Capture


logger = logging.getLogger(__name__)

### CONSTANTS ###

ROBOTS_TXT_TIMEOUT = 30 # seconds to wait before giving up on robots.txt
ONLOAD_EVENT_TIMEOUT = 60 # seconds to wait before giving up on the onLoad event and proceeding as though it fired
RESOURCE_LOAD_TIMEOUT = 180 # seconds to wait for at least one resource to load before giving up on capture
ELEMENT_DISCOVERY_TIMEOUT = 2 # seconds before PhantomJS gives up running a DOM request (should be instant, assuming page is loaded)
AFTER_LOAD_TIMEOUT = 30 # seconds to allow page to keep loading additional resources after onLoad event fires
VALID_FAVICON_MIME_TYPES = {'image/png', 'image/gif', 'image/jpg', 'image/jpeg', 'image/x-icon', 'image/vnd.microsoft.icon', 'image/ico'}

### HELPERS ###

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

def retry_on_error(func):
    """
        Decorator to catch any exceptions thrown by the given task and call retry().
    """
    @wraps(func)
    def with_retry(task, *args, **kwargs):
        try:
            return func(task, *args, **kwargs)
        except Exception as e:
            logger.exception("Task failed, calling retry.\nArgs: %s\nKwargs: %s\nError: %s" % (args, kwargs, e))
            task.retry(exc=e)
    return with_retry

def save_fields(instance, **kwargs):
    """
        Update and save the given fields for a model instance.
        Use update_fields so we won't step on changes to other fields made in another thread.
    """
    for key, val in kwargs.items():
        setattr(instance, key, val)
    instance.save(update_fields=kwargs.keys())

def add_thread(thread_list, func):
    new_thread = threading.Thread(target=func)
    new_thread.start()
    thread_list.append(new_thread)


### TASKS ##

class ProxyCaptureTask(Task):
    """
        After each call to proxy_capture, we check if it has failed more than max_retries times,
        and if so mark pending captures as failed permanently.
    """
    abstract = True
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if self.request.retries >= self.max_retries:
            Capture.objects.filter(link_id=(args[0] if args else kwargs['link_guid']), status='pending').update(status='failed')

@shared_task(bind=True,
             default_retry_delay=30,  # seconds
             max_retries=2,
             base=ProxyCaptureTask)
@retry_on_error
@tempdir.run_in_tempdir()
def proxy_capture(self, link_guid, user_agent=''):
    """
    start warcprox process. Warcprox is a MITM proxy server and needs to be running
    before, during and after phantomjs gets a screenshot.

    Create an image from the supplied URL, write it to disk and update our asset model with the path.
    The heavy lifting is done by PhantomJS, our headless browser.

    This whole function runs with the local dir set to a temp dir by run_in_tempdir().
    So we can use local paths for temp files, and they'll just disappear when the function exits.
    """
    # basic setup
    link = Link.objects.get(guid=link_guid)
    target_url = link.submitted_url

    # allow pending tasks to be canceled outside celery by updating capture status
    if link.primary_capture.status != "pending":
        return

    # Override user_agent for now, since PhantomJS doesn't like some user agents.
    # This user agent is the Chrome on Linux that's most like PhantomJS 1.9.8.
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.36 (KHTML, like Gecko) Chrome/13.0.766.0 Safari/534.36"

    print "%s: Fetching %s" % (link_guid, target_url)

    # suppress verbose warcprox logs
    logging.disable(logging.INFO)

    # Set up an exception we can trigger to halt capture and release all the resources involved.
    class HaltCaptureException(Exception):
        pass
    browser = warcprox_controller = warcprox_thread = None
    have_warc = False
    thread_list = []
    successful_favicon_urls = []

    try:

        # create a request handler class that counts unique requests and responses
        unique_requests = set()
        unique_responses = set()
        count_lock = threading.Lock()
        class CountingRequestHandler(WarcProxyHandler):
            def _proxy_request(self):
                with count_lock:
                    unique_requests.add(self.url)
                WarcProxyHandler._proxy_request(self)
                with count_lock:
                    unique_responses.add(self.url)

        # connect warcprox to an open port
        warcprox_port = 27500
        recorded_url_queue = queue.Queue()
        for i in xrange(500):
            try:
                proxy = WarcProxy(
                    server_address=("127.0.0.1", warcprox_port),
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

        # set up requests getter for one-off requests outside of selenium
        def proxied_get_request(url):
            return requests.get(url,
                                headers={'User-Agent': user_agent},
                                proxies={'http': 'http://' + proxy_address, 'https': 'http://' + proxy_address},
                                verify=False)

        # start warcprox in the background
        warc_writer = WarcWriter(gzip=True, port=warcprox_port)
        warc_writer_thread = WarcWriterThread(recorded_url_q=recorded_url_queue, warc_writer=warc_writer)
        warcprox_controller = WarcproxController(proxy, warc_writer_thread)
        warcprox_thread = threading.Thread(target=warcprox_controller.run_until_shutdown, name="warcprox", args=())
        warcprox_thread.start()

        print "WarcProx opened."

        # fetch page in the background
        print "Fetching url."
        browser = get_browser(user_agent, proxy_address, proxy.ca.ca_file)
        browser.set_window_size(1024, 800)
        start_time = time.time()
        page_load_thread = threading.Thread(target=browser.get, args=(target_url,))  # returns after onload
        page_load_thread.start()
        page_load_thread.join(ONLOAD_EVENT_TIMEOUT)

        # wait for the HAR log to report that at least one resource has successfully loaded
        while True:
            har_log_entries = json.loads(browser.get_log('har')[0]['message'])['log']['entries']
            if har_log_entries:
                break
            if time.time() - start_time > RESOURCE_LOAD_TIMEOUT:
                raise HaltCaptureException
            time.sleep(1)

        # use the HAR log to retrieve the URL we ended up, after any forwards,
        # and the content type.
        content_type = ''
        for header in har_log_entries[0]['response']['headers']:
            if header['name'].lower() == 'content-type':
                content_type = header['value'].lower()
                break
        content_url = har_log_entries[0]['request']['url']
        have_html = content_type and content_type.startswith('text/html')
        print "Finished fetching url."

        # get favicon urls
        # Here we fetch everything in the page that's marked as a favicon, for archival purposes.
        # But we only record a favicon as our favicon_capture_url if it passes a mimetype whitelist.
        def favicon_thread():
            favicon_urls = []
            if have_html:
                favicons = browser.find_elements_by_css_selector('link[rel="shortcut icon"],link[rel="icon"]')
                for candidate_favicon in favicons:
                    if candidate_favicon.get_attribute('href'):
                        candidate_favicon_url = urlparse.urljoin(content_url, candidate_favicon.get_attribute('href'))
                        favicon_urls.append(candidate_favicon_url)
            favicon_urls.append(urlparse.urljoin(content_url, '/favicon.ico'))
            if not favicon_urls:
                return

            for favicon_url in favicon_urls:
                print "Fetching favicon from %s ..." % favicon_url
                try:
                    favicon_response = proxied_get_request(favicon_url)
                    assert favicon_response.ok
                except (requests.ConnectionError, requests.Timeout, AssertionError) as e:
                    print "Failed:", e
                    continue

                # apply mime type whitelist
                mime_type = favicon_response.headers.get('content-type', '').split(';')[0]
                if not mime_type in VALID_FAVICON_MIME_TYPES:
                    continue

                successful_favicon_urls.append((favicon_url, mime_type))

            if not successful_favicon_urls:
                print "Couldn't get favicon"
        add_thread(thread_list, favicon_thread)

        # fetch robots.txt in the background
        def robots_txt_thread():
            print "Fetching robots.txt ..."
            robots_txt_location = urlparse.urljoin(content_url, '/robots.txt')
            try:
                robots_txt_response = proxied_get_request(robots_txt_location)
                assert robots_txt_response.ok
            except (requests.ConnectionError, requests.Timeout, AssertionError):
                print "Couldn't reach robots.txt"
                return

            # We only want to respect robots.txt if Perma is specifically asked not to archive (we're not a crawler)
            if 'Perma' in robots_txt_response.content:
                # We found Perma specifically mentioned
                rp = robotparser.RobotFileParser()
                rp.parse([line.strip() for line in robots_txt_response.content.split('\n')])
                if not rp.can_fetch('Perma', target_url):
                    save_fields(link, is_private=True, private_reason='policy')
                    print "Robots.txt fetched."
        add_thread(thread_list, robots_txt_thread)

        if have_html:
            # get page title
            print "Getting title."
            if browser.title:
                save_fields(link, submitted_title=browser.title)

            # check meta tags
            # (run this in a thread and give it long enough to find the tags, but then let other stuff proceed)
            print "Checking meta tags."
            def meta_thread():
                # get all meta tags
                meta_tags = browser.find_elements_by_tag_name('meta')
                # first look for <meta name='perma'>
                meta_tag = next((tag for tag in meta_tags if tag.get_attribute('name').lower()=='perma'), None)
                # else look for <meta name='robots'>
                if not meta_tag:
                    meta_tag = next((tag for tag in meta_tags if tag.get_attribute('name').lower() == 'robots'), None)
                # if we found a relevant meta tag, check for noarchive
                if meta_tag and 'noarchive' in meta_tag.get_attribute("content").lower():
                    save_fields(link, is_private=True, private_reason='policy')
                    print "Meta found, darchiving"
            add_thread(thread_list, meta_thread)

            # scroll to bottom of page and back up, in case that prompts anything else to load
            try:
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                browser.execute_script("window.scrollTo(0, 0);")
            except WebDriverException:
                pass

            # make sure all requests are finished
            print "Waiting for post-load requests."
            start_time = time.time()
            time.sleep(min(AFTER_LOAD_TIMEOUT, 1.5))
            while len(unique_responses) < len(unique_requests):
                print "%s/%s finished" % (len(unique_responses), len(unique_requests))
                if time.time() - start_time > AFTER_LOAD_TIMEOUT:
                    print "Waited %s seconds to finish post-load requests -- giving up." % AFTER_LOAD_TIMEOUT
                    break
                time.sleep(.5)

            # get page size to decide whether to take a screenshot
            capture_screenshot = False
            try:
                root_element = browser.find_element_by_tag_name('body')
            except NoSuchElementException:
                try:
                    root_element = browser.find_element_by_tag_name('frameset')
                except NoSuchElementException:
                    root_element = None
            if root_element:
                page_size = root_element.size
                pixel_count = page_size['width'] * page_size['height']
                capture_screenshot = pixel_count < settings.MAX_IMAGE_SIZE

            # take screenshot after all requests done
            if capture_screenshot:
                print "Taking screenshot."
                screenshot_data = browser.get_screenshot_as_png()
                link.screenshot_capture.write_warc_resource_record(screenshot_data)
                save_fields(link.screenshot_capture, status='success')
            else:
                print "Not saving screenshots! Page size is %s pixels." % pixel_count
                save_fields(link.screenshot_capture, status='failed')
        else:
            # no screenshot if not HTML
            save_fields(link.screenshot_capture, status='failed')

        have_warc = True

    except HaltCaptureException:
        pass

    except Exception as e:
        print e
        raise

    finally:
        # teardown (have to do this before save to make sure WARC is done writing):
        print "Shutting down browser and proxies."

        for thread in thread_list:
            thread.join()  # wait until threads are done (have to do this before closing phantomjs)
        if browser:
            browser.quit()  # shut down phantomjs
        if warcprox_controller:
            warcprox_controller.stop.set()  # send signal to shut down warc thread
        if warcprox_thread:
            warcprox_thread.join()  # wait until warcprox thread is done writing out warc

        # un-suppress logging
        logging.disable(logging.NOTSET)

    # save generated warc file
    if have_warc:
        print "Saving WARC."
        try:
            temp_warc_path = os.path.join(warc_writer.directory,
                                          warc_writer._f_finalname)
            with open(temp_warc_path, 'rb') as warc_file:
                link.write_warc_raw_data(warc_file)
                save_fields(link.primary_capture, status='success', content_type=content_type)

            # We only save the Capture for the favicon once the warc is stored,
            # since the data for the favicon lives in the warc.
            if successful_favicon_urls:
                Capture(
                    link=link,
                    role='favicon',
                    status='success',
                    record_type='response',
                    url=successful_favicon_urls[0][0],
                    content_type=successful_favicon_urls[0][1]
                ).save()
                print "Saved favicon at %s" % successful_favicon_urls

            print "Writing CDX lines to the DB"
            CDXLine.objects.create_all_from_link(link)

        except Exception as e:
            print "Web Archive File creation failed for %s: %s" % (target_url, e)
            save_fields(link.primary_capture, warc_capture='failed')


    print "%s capture done." % link_guid


@shared_task
def get_nightly_stats():
    """
    A periodic task (probably running nightly) to get counts of user types, disk usage.
    Write them into a DB for our stats view
    """
    
    # Five types user accounts
    total_count_regular_users = LinkUser.objects.filter(is_staff=False, organizations=None, registrar_id=None).count()
    total_count_org_members = LinkUser.objects.exclude(organizations=None).count()
    total_count_registrar_members = LinkUser.objects.exclude(registrar_id=None).count()
    total_count_registry_members = LinkUser.objects.filter(is_staff=True).count()
    
    # Registrar count
    total_count_registrars = Registrar.objects.all().count()
    
    # Journal account
    total_orgs = Organization.objects.all().count()
    
    # Two types of links
    total_count_unvested_links = Link.objects.filter(vested=False).count()
    total_count_vested_links = Link.objects.filter(vested=True).count()
    
    # Get things in the darchive
    total_count_darchive_takedown_links = Link.objects.filter(is_private=True, private_reason='takedown').count()
    total_count_darchive_robots_links = Link.objects.filter(is_private=True, private_reason='policy').count()
    
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
        org_member_count=total_count_org_members,
        registrar_member_count=total_count_registrar_members,
        registry_member_count=total_count_registry_members,
        registrar_count=total_count_registrars,
        org_count=total_orgs,
        unvested_count=total_count_unvested_links,
        darchive_takedown_count = total_count_darchive_takedown_links,
        darchive_robots_count = total_count_darchive_robots_links,
        vested_count=total_count_vested_links,
        disk_usage = new_total_disk_usage,
        )

    stat.save()

@shared_task(
    bind=True,
    default_retry_delay=10*60) # 10 minute delay between retries
def upload_to_internet_archive(self, link_guid):
    # setup
    link = Link.objects.get(guid=link_guid)

    # make sure link should be uploaded
    if not link.can_upload_to_internet_archive():
        print "Not eligible for upload."
        return

    identifier = settings.INTERNET_ARCHIVE_IDENTIFIER_PREFIX+link_guid

    # create IA item for this capture
    item = internetarchive.get_item(identifier)
    metadata = {
        'collection':settings.INTERNET_ARCHIVE_COLLECTION,
        'mediatype':'web',
        'date':link.creation_timestamp,
        'title':'%s: %s' % (link_guid, truncatechars(link.submitted_title, 50)),
        'description': 'Perma.cc archive of %s created on %s and vested on %s by %s.' % (link.submitted_url, link.creation_timestamp, link.vested_timestamp, link.organization),
        'contributor':'Perma.cc',
        'sponsor':"%s - %s" % (link.organization, link.organization.registrar),

        # custom metadata
        'submitted_url':link.submitted_url,
        'perma_url':"http://%s/%s" % (settings.HOST, link_guid),
        'external-identifier':'urn:X-perma:%s' % link_guid,
    }

    # upload
    with default_storage.open(link.warc_storage_file(), 'rb') as warc_file:
        success = item.upload(warc_file,
                              metadata=metadata,
                              access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY,
                              secret_key=settings.INTERNET_ARCHIVE_SECRET_KEY,
                              verbose=True,
                              debug=True)
    if not success:
        self.retry(exc=Exception("Internet Archive reported upload failure."))
        print "Failed."

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

        'num_org_members_added': current_stats['org_member_count'] - previous_stats['org_member_count'],
        'prev_org_members_count': previous_stats['org_member_count'],
        'current_org_members_count': current_stats['org_member_count'],

        'num_registar_members_added': current_stats['registrar_member_count'] - previous_stats['registrar_member_count'],
        'prev_registrar_members_count': previous_stats['registrar_member_count'],
        'current_registrar_members_count': current_stats['registrar_member_count'],

        'num_registry_members_added': current_stats['registry_member_count'] - previous_stats['registry_member_count'],
        'prev_registry_members_count': previous_stats['registry_member_count'],
        'current_registry_members_count': current_stats['registry_member_count'],

        'num_orgs_added': current_stats['org_count'] - previous_stats['org_count'],
        'prev_orgs_count': previous_stats['org_count'],
        'current_orgs_count': current_stats['org_count'],

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


