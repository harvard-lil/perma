from __future__ import absolute_import # to avoid importing local .celery instead of celery package

import tempfile
import traceback
from cStringIO import StringIO
from contextlib import contextmanager

from httplib import HTTPResponse
from urllib2 import URLError

import os
import os.path
import threading
import urlparse
from celery import shared_task
from pyvirtualdisplay import Display
import re
from requests.structures import CaseInsensitiveDict
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchElementException, NoSuchFrameException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import ProxyType, Proxy
from datetime import timedelta
import logging
import json
import robotparser
import time
import requests
import errno
import tempdir
from socket import error as socket_error
import internetarchive
import Queue as queue
from warcprox.controller import WarcproxController
from warcprox.warcprox import WarcProxyHandler, WarcProxy, ProxyingRecorder
from warcprox.warcwriter import WarcWriter, WarcWriterThread

from django.core.files.storage import default_storage
from django.template.defaultfilters import truncatechars
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.http import HttpRequest


from perma.models import WeekStats, MinuteStats, Registrar, LinkUser, Link, Organization, CDXLine, Capture, CaptureJob
from perma.email import sync_cm_list, send_admin_email, registrar_users_plus_stats


from perma.utils import run_task, url_in_allowed_ip_range, copy_file_data

logger = logging.getLogger(__name__)

### CONSTANTS ###

ROBOTS_TXT_TIMEOUT = 30 # seconds to wait before giving up on robots.txt
ONLOAD_EVENT_TIMEOUT = 30 # seconds to wait before giving up on the onLoad event and proceeding as though it fired
RESOURCE_LOAD_TIMEOUT = 45 # seconds to wait for at least one resource to load before giving up on capture
ELEMENT_DISCOVERY_TIMEOUT = 2 # seconds before PhantomJS gives up running a DOM request (should be instant, assuming page is loaded)
AFTER_LOAD_TIMEOUT = 30 # seconds to allow page to keep loading additional resources after onLoad event fires
VALID_FAVICON_MIME_TYPES = {'image/png', 'image/gif', 'image/jpg', 'image/jpeg', 'image/x-icon', 'image/vnd.microsoft.icon', 'image/ico'}

### HELPERS ###

# monkeypatch ProxyingRecorder to grab headers of proxied response
_orig_update_payload_digest = ProxyingRecorder._update_payload_digest
def _update_payload_digest(self, hunk):
    if self.payload_digest is None:
        if not hasattr(self, 'headers'):
            self.headers = ""
        self.headers += hunk
        self.headers = re.sub(br'(\r?\n\r?\n).*', r'\1', self.headers)  # remove any part of hunk that came after headers
    return _orig_update_payload_digest(self, hunk)
ProxyingRecorder._update_payload_digest = _update_payload_digest

def get_browser(user_agent, proxy_address, cert_path):
    """ Set up a Selenium browser with given user agent, proxy and SSL cert. """
    # PhantomJS
    if settings.CAPTURE_BROWSER == 'PhantomJS':
        desired_capabilities = dict(DesiredCapabilities.PHANTOMJS)
        desired_capabilities["phantomjs.page.settings.userAgent"] = user_agent
        browser = webdriver.PhantomJS(
            executable_path=getattr(settings, 'PHANTOMJS_BINARY', 'phantomjs'),
            desired_capabilities=desired_capabilities,
            service_args=[
                "--proxy=%s" % proxy_address,
                "--ssl-certificates-path=%s" % cert_path,
                "--ignore-ssl-errors=true",
                "--local-url-access=false",
                "--local-storage-path=.",
            ],
            service_log_path=settings.PHANTOMJS_LOG)

    # Firefox
    elif settings.CAPTURE_BROWSER == 'Firefox':
        desired_capabilities = dict(DesiredCapabilities.FIREFOX)
        proxy = Proxy({
            'proxyType': ProxyType.MANUAL,
            'httpProxy': proxy_address,
            'ftpProxy': proxy_address,
            'sslProxy': proxy_address,
        })
        proxy.add_to_capabilities(desired_capabilities)
        profile = webdriver.FirefoxProfile()
        profile.accept_untrusted_certs = True
        profile.assume_untrusted_cert_issuer = True
        browser = webdriver.Firefox(
            capabilities=desired_capabilities,
            firefox_profile=profile)

    # Chrome
    elif settings.CAPTURE_BROWSER == 'Chrome':
        # http://blog.likewise.org/2015/01/setting-up-chromedriver-and-the-selenium-webdriver-python-bindings-on-ubuntu-14-dot-04/
        download_dir = os.path.abspath('./downloads')
        os.mkdir(download_dir)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=%s' % proxy_address)
        chrome_options.add_argument('--test-type')
        chrome_options.add_experimental_option("prefs", {"profile.default_content_settings.popups": "0",
                                                         "download.default_directory": download_dir,
                                                         "download.prompt_for_download": "false"})
        desired_capabilities = chrome_options.to_capabilities()
        desired_capabilities["acceptSslCerts"] = True

        # for more detailed progress updates
        # desired_capabilities["loggingPrefs"] = {'performance': 'INFO'}
        # then:
        # performance_log = browser.get_log('performance')

        browser = webdriver.Chrome(desired_capabilities=desired_capabilities)

    else:
        assert False, "Invalid value for CAPTURE_BROWSER."

    browser.implicitly_wait(ELEMENT_DISCOVERY_TIMEOUT)
    browser.set_page_load_timeout(ROBOTS_TXT_TIMEOUT)

    return browser

def save_fields(instance, **kwargs):
    """
        Update and save the given fields for a model instance.
        Use update_fields so we won't step on changes to other fields made in another thread.
    """
    for key, val in kwargs.items():
        setattr(instance, key, val)
    instance.save(update_fields=kwargs.keys())

def add_thread(thread_list, target, **kwargs):
    if not isinstance(target, threading.Thread):
        target = threading.Thread(target=target, **kwargs)
    target.start()
    thread_list.append(target)
    return target

class ProxiedRequestThread(threading.Thread):
    """
        Run request.get() in a thread, loading data in chunks.
        Listen for self.stop to be set, allowing requests to be halted by other threads.
        While the thread is running, see `self.pending_data` for how much has been downloaded so far.
        Once the thread is done, see `self.response` and `self.response_exception` for the results.
    """
    def __init__(self, proxy_address, url, *args, **kwargs):
        self.url = url
        self.proxy_address = proxy_address
        self.pending_data = 0
        self.stop = threading.Event()
        self.response = None
        self.response_exception = None
        super(ProxiedRequestThread, self).__init__(*args, **kwargs)

    def run(self):
        try:
            self.response = requests.get(self.url,
                                         headers={'User-Agent': settings.CAPTURE_USER_AGENT},
                                         proxies={'http': 'http://' + self.proxy_address, 'https': 'http://' + self.proxy_address},
                                         verify=False,
                                         stream=True,
                                         timeout=1)
            self.response._content = bytes()
            for chunk in self.response.iter_content(8192):
                self.pending_data += len(chunk)
                self.response._content += chunk
                if self.stop.is_set():
                    return
        except requests.RequestException as e:
            self.response_exception = e
        finally:
            self.pending_data = 0

def repeat_while_exception(func, exception=Exception, timeout=10, sleep_time=.1, raise_after_timeout=True):
    end_time = time.time() + timeout
    while True:
        try:
            return func()
        except exception:
            if time.time() > end_time:
                if raise_after_timeout:
                    raise
                return
            time.sleep(sleep_time)

def parse_response(response_text):
    """
        Given an HTTP response line and headers, return a requests.Response object.
    """
    class FakeSocket():
        def __init__(self, response_str):
            self._file = StringIO(response_str)

        def makefile(self, *args, **kwargs):
            return self._file

    source = FakeSocket(response_text)
    response = HTTPResponse(source)
    response.begin()
    requests_response = requests.Response()
    requests_response.status_code = response.status

    headers = CaseInsensitiveDict(response.getheaders())
    # Reset headers['x-robots-tag'], so that we can handle the
    # possibilility that multiple x-robots directives might be included
    # https://developers.google.com/webmasters/control-crawl-index/docs/robots_meta_tag
    # e.g.
    # HTTP/1.1 200 OK
    # Date: Tue, 25 May 2010 21:42:43 GMT
    # (...)
    # X-Robots-Tag: googlebot: nofollow
    # X-Robots-Tag: otherbot: noindex, nofollow
    # (...)
    # Join with a semi-colon, not a comma, so that multiple agents can
    # be recovered. As of 12/14/16, there doesn't appear to be any spec
    # describing how to do this properly (since commas don't work).
    # Since parsed response headers aren't archived, this convenience is
    # fine. However, it's worth keeping track of the situation.
    robots_directives = []
    for directive in response.msg.getallmatchingheaders('x-robots-tag'):
        robots_directives.append(directive.split(": ", 1)[1].replace("\n", "").replace("\r", ""))
    headers['x-robots-tag'] = ";".join(robots_directives)

    requests_response.headers = headers

    return requests_response

def run_in_frames(browser, func, output_collector=None):
    # setup
    browser.implicitly_wait(0)
    if output_collector is None:
        output_collector = []

    run_in_frames_recursive(browser, func, output_collector)

    # reset
    browser.implicitly_wait(ELEMENT_DISCOVERY_TIMEOUT)
    browser.switch_to.default_content()

    return output_collector

def run_in_frames_recursive(browser, func, output, frame_path=None):
    if frame_path is None:
        frame_path = []
    output += func(browser)
    for child_frame in browser.find_elements_by_tag_name('frame') + browser.find_elements_by_tag_name('iframe'):
        browser.switch_to.default_content()
        for frame in frame_path:
            browser.switch_to.frame(frame)
        try:
            browser.switch_to.frame(child_frame)
            run_in_frames_recursive(browser, func, output, frame_path + [child_frame])
        except (ValueError, NoSuchFrameException):
            # switching to frame failed for some reason
            print "run_in_frames_recursive caught exception switching to iframe:"
            traceback.print_exc()

@contextmanager
def warn_on_exception(message="Exception in block:", exception_type=Exception):
    try:
        yield
    except exception_type as e:
        print message, e


### TASKS ##

@shared_task
def run_next_capture():
    """ Grab and run the next CaptureJob. This will keep calling itself until there are no jobs left. """
    capture_job = CaptureJob.get_next_job(reserve=True)
    if not capture_job:
        return  # no jobs waiting
    try:
        proxy_capture(capture_job)
    except:
        print "Exception while processing capture job %s:" % capture_job.link_id
        traceback.print_exc()
    finally:
        capture_job.link.captures.filter(status='pending').update(status='failed')
        if capture_job.status == 'pending':
            capture_job.mark_completed('failed')
    run_task(run_next_capture.s())


@tempdir.run_in_tempdir()
def proxy_capture(capture_job):
    """
    Start warcprox process. Warcprox is a MITM proxy server and needs to be running
    before, during and after the headless browser.

    Start a headless browser to capture the supplied URL. Also take a screenshot if the URL is an HTML file.

    This whole function runs with the local dir set to a temp dir by run_in_tempdir().
    So we can use local paths for temp files, and they'll just disappear when the function exits.
    """

    # basic setup
    link = capture_job.link
    target_url = link.safe_url

    if link.user_deleted or link.primary_capture.status != "pending":
        capture_job.mark_completed('deleted')
        return

    capture_job.attempt += 1
    capture_job.save()

    # Helper function to update capture_job's progress
    def display_progress(step_count, step_description):
        save_fields(capture_job, step_count=step_count, step_description=step_description)
        print "%s step %s: %s" % (link.guid, step_count, step_description)

    print "%s: Fetching %s" % (link.guid, target_url)
    progress = 0
    display_progress(progress, "Starting capture")

    # suppress verbose warcprox logs
    logging.disable(logging.INFO)

    # Set up an exception we can trigger to halt capture and release all the resources involved.
    class HaltCaptureException(Exception):
        pass

    browser = warcprox_controller = warcprox_thread = display = have_html = None
    have_warc = False
    thread_list = []
    successful_favicon_urls = []

    try:

        # create a request handler class that counts requests and responses
        proxied_requests = []
        proxied_responses = []
        proxied_pairs = []
        count_lock = threading.Lock()
        class CountingRequestHandler(WarcProxyHandler):
            def _proxy_request(self):

                # make sure we don't capture anything in a banned IP range
                if not url_in_allowed_ip_range(self.url):
                    return

                with count_lock:
                    proxied_pair = [self.url, None]
                    proxied_requests.append(proxied_pair[0])
                    proxied_pairs.append(proxied_pair)
                response = WarcProxyHandler._proxy_request(self)
                with count_lock:
                    proxied_responses.append(response)
                    proxied_pair[1] = response

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
            raise Exception("WarcProx couldn't find an open port.")
        proxy_address = "127.0.0.1:%s" % warcprox_port

        # start warcprox in the background
        warc_writer = WarcWriter(gzip=True, port=warcprox_port)
        warc_writer_thread = WarcWriterThread(recorded_url_q=recorded_url_queue, warc_writer=warc_writer)
        warcprox_controller = WarcproxController(proxy, warc_writer_thread)
        warcprox_thread = threading.Thread(target=warcprox_controller.run_until_shutdown, name="warcprox", args=())
        warcprox_thread.start()

        print "WarcProx opened."

        # Helper function to get a url, via proxied requests.get(), in a way that is interruptable from other threads.
        # This should only be run from sub-threads.
        def get_url(url):
            request_thread = add_thread(thread_list, ProxiedRequestThread(proxy_address, url))
            request_thread.join()
            return request_thread.response, request_thread.response_exception

        # start virtual display
        if settings.CAPTURE_BROWSER != "PhantomJS":
            display = Display(visible=0, size=(1024, 800))
            display.start()

        # fetch page in the background
        progress += 1
        display_progress(progress, "Fetching target URL")
        browser = get_browser(settings.CAPTURE_USER_AGENT, proxy_address, proxy.ca.ca_file)
        browser.set_window_size(1024, 800)

        start_time = time.time()
        page_load_thread = threading.Thread(target=browser.get, args=(target_url,))  # returns after onload
        page_load_thread.start()
        page_load_thread.join(ONLOAD_EVENT_TIMEOUT)

        # wait until warcprox records a response that isn't a forward
        have_response = False
        while not have_response:
            if proxied_responses:
                for request, response in proxied_pairs:
                    if response is None:
                        # Response hasn't finished yet -- we might get here because subsequent
                        # responses have finished, but we have to go in order to find the correct content_type,
                        # so let's wait for this one.
                        break
                    if response.url.endswith('/favicon.ico') and response.url != target_url:
                        continue
                    if not hasattr(response, 'parsed_response'):
                        response.parsed_response = parse_response(response.response_recorder.headers)
                    if response.parsed_response.is_redirect or response.parsed_response.status_code == 206:  # partial content
                        continue

                    content_url = response.url
                    content_type = response.parsed_response.headers.get('content-type')
                    robots_directives = response.parsed_response.headers.get('x-robots-tag')
                    have_html = content_type and content_type.startswith('text/html')
                    have_response = True
                    break

            if have_response:
                have_warc = True  # at this point we have something that's worth showing to the user
                break

            wait_time = time.time() - start_time
            if wait_time > RESOURCE_LOAD_TIMEOUT:
                raise HaltCaptureException

            progress = int(progress) + wait_time/RESOURCE_LOAD_TIMEOUT
            display_progress(progress, "Fetching target URL")

            time.sleep(1)

        print "Finished fetching url."

        # check for x-robots-tag directives
        progress = int(progress) + 1
        display_progress(progress, "Checking x-robots-tag directives.")
        if robots_directives:
            darchive = False
            for directive in robots_directives.split(";"):
                parsed = directive.lower().split(":")
                # respect tags that target all crawlers (no user-agent specified)
                if len(parsed) == 1:
                    if "noarchive" in parsed:
                        darchive = True
                # look for perma user-agent
                elif len(parsed) == 2:
                    if parsed[0] == "perma" and "noarchive" in parsed[1]:
                        darchive = True
                # if the directive is poorly formed, do our best
                else:
                    if "perma" in directive and "noarchive" in directive:
                        darchive = True

            if darchive:
                save_fields(link, is_private=True, private_reason='policy')
                print "x-robots-tag found, darchiving"

        # get favicon urls
        # Here we fetch everything in the page that's marked as a favicon, for archival purposes.
        # But we only record a favicon as our favicon_capture_url if it passes a mimetype whitelist.
        def favicon_thread():
            favicon_urls = []
            if have_html:
                favicons = repeat_while_exception(lambda: browser.find_elements_by_css_selector('link[rel="shortcut icon"],link[rel="icon"]'),
                                                  timeout=10)
                for candidate_favicon in favicons:
                    if candidate_favicon.get_attribute('href'):
                        candidate_favicon_url = urlparse.urljoin(content_url, candidate_favicon.get_attribute('href'))
                        favicon_urls.append(candidate_favicon_url)
            favicon_urls.append(urlparse.urljoin(content_url, '/favicon.ico'))
            if not favicon_urls:
                return

            for favicon_url in favicon_urls:
                print "Fetching favicon from %s ..." % favicon_url
                favicon_response, e = get_url(favicon_url)
                if e or not favicon_response or not favicon_response.ok:
                    print "Favicon failed:", e, favicon_response
                    continue

                # apply mime type whitelist
                mime_type = favicon_response.headers.get('content-type', '').split(';')[0]
                if mime_type not in VALID_FAVICON_MIME_TYPES:
                    continue

                successful_favicon_urls.append((favicon_url, mime_type))

            if not successful_favicon_urls:
                print "Couldn't get favicon"
        add_thread(thread_list, favicon_thread)

        # fetch robots.txt in the background
        def robots_txt_thread():
            print "Fetching robots.txt ..."
            robots_txt_location = urlparse.urljoin(content_url, '/robots.txt')
            robots_txt_response, e = get_url(robots_txt_location)
            if e or not robots_txt_response or not robots_txt_response.ok:
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
            progress = int(progress) + 1
            display_progress(progress, "Getting page title")
            def get_title():
                if browser.title:
                    save_fields(link, submitted_title=browser.title)
                else:
                    title_element = browser.find_element_by_tag_name("title")
                    save_fields(link, submitted_title=title_element.get_attribute("text"))
            repeat_while_exception(get_title, timeout=10, raise_after_timeout=False)

            # check meta tags
            print "Checking meta tags."
            def meta_thread():
                # get all meta tags
                meta_tags = repeat_while_exception(lambda: browser.find_elements_by_tag_name('meta'),
                                                   timeout=10)
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

            # scroll to bottom of page, in case that prompts anything else to load
            # TODO: This doesn't scroll horizontally or scroll frames
            progress += .5
            display_progress(progress, "Checking for scroll-loaded assets")
            def scroll_browser():
                try:
                    scroll_delay = browser.execute_script("""
                        // Scroll down the page in a series of jumps the size of the window height.
                        // The actual scrolling is done in a setTimeout with a 50ms delay so the browser has
                        // time to render at each position.
                        var delay=50,
                            height=document.body.scrollHeight,
                            jump=window.innerHeight,
                            scrollTo=function(scrollY){ window.scrollTo(0, scrollY) },
                            i=1;
                        for(;i*jump<height;i++){
                            setTimeout(scrollTo, i*delay, i*jump);
                        }

                        // Scroll back to top before taking screenshot.
                        setTimeout(scrollTo, i*delay, 0);

                        // Return how long all this scrolling will take.
                        return (i*delay)/1000;
                    """)

                    # In python, wait for javascript background scrolling to finish.
                    time.sleep(min(scroll_delay,1))
                except (WebDriverException, URLError):
                    # Don't panic if we can't scroll -- we've already captured something useful anyway.
                    # WebDriverException: the page can't execute JS for some reason.
                    # URLError: the headless browser has gone away for some reason.
                    pass
            repeat_while_exception(scroll_browser)

            # load media
            progress = int(progress) + 1
            display_progress(progress, "Fetching media")
            with warn_on_exception("Error fetching media"):
                # running in each frame ...
                def get_media_tags(browser):
                    url_set = []
                    base_url = browser.current_url

                    def make_absolute_urls(urls):
                        '''collect resource urls, converted to absolute urls relative to current browser frame'''
                        return [urlparse.urljoin(base_url, url) for url in urls if url]

                    # get all images in srcsets
                    print("Fetching images in srcsets")
                    for img in browser.find_elements_by_css_selector('img[srcset], source[srcset]'):
                        urls = [src.strip().split(' ')[0] for src in img.get_attribute('srcset').split(',')]
                        url_set.extend(make_absolute_urls(urls))

                    # fetch each audio/video/object/embed element
                    if settings.ENABLE_AV_CAPTURE:
                        print("Fetching audio/video objects")
                        media_tags = sum((browser.find_elements_by_tag_name(tag_name) for tag_name in ('video', 'audio', 'object', 'embed')), [])
                        for tag in media_tags:
                            # for each tag, extract all resource urls
                            if tag.tag_name == 'object':
                                # for <object>, get the data and archive attributes, prepended with codebase attribute if it exists,
                                # as well as any <param name="movie" value="url"> elements
                                codebase_url = tag.get_attribute('codebase') or base_url
                                urls = [
                                    urlparse.urljoin(codebase_url, url) for url in
                                    [tag.get_attribute('data')] +
                                    (tag.get_attribute('archive') or '').split()
                                ]+[
                                    param.get_attribute('value') for param in tag.find_elements_by_css_selector('param[name="movie"]')
                                ]
                            else:
                                # for <audio>, <video>, and <embed>, get src attribute and any <source src="url"> elements
                                urls = [tag.get_attribute('src')] + [source.get_attribute('src') for source in tag.find_elements_by_tag_name('source')]

                            url_set.extend(make_absolute_urls(urls))

                    return url_set

                media_urls = run_in_frames(browser, get_media_tags)

                # grab all media urls that aren't already being grabbed
                for media_url in set(media_urls) - set(proxied_requests):
                    add_thread(thread_list, ProxiedRequestThread(proxy_address, media_url))

        # Wait AFTER_LOAD_TIMEOUT seconds for any requests to finish that are started within the next .5 seconds.
        progress = int(progress) + 1
        display_progress(progress, "Waiting for post-load requests")
        time.sleep(.5)
        unfinished_proxied_pairs = [pair for pair in proxied_pairs if not pair[1]]
        start_time = time.time()
        while unfinished_proxied_pairs:

            print "Waiting for %s pending requests" % len(unfinished_proxied_pairs)

            # give up after AFTER_LOAD_TIMEOUT seconds
            wait_time = time.time() - start_time
            if wait_time > AFTER_LOAD_TIMEOUT:
                print "Waited %s seconds to finish post-load requests -- giving up." % AFTER_LOAD_TIMEOUT
                break

            # Give up if downloaded size exceeds MAX_ARCHIVE_FILE_SIZE.
            # Amount captured so far is the sum of the bytes recorded by warcprox,
            # and the bytes pending in our background threads.
            capture_size = sum(getattr(thread, 'pending_data', 0) for thread in thread_list) + \
                           sum(proxied_response.response_recorder.len for proxied_response in proxied_responses)
            if capture_size > settings.MAX_ARCHIVE_FILE_SIZE:
                print "Halting for size"
                break

            # Show progress to user
            progress = int(progress) + wait_time/AFTER_LOAD_TIMEOUT
            display_progress(progress, "Waiting for post-load requests")

            # Sleep and update our list
            time.sleep(.5)
            unfinished_proxied_pairs = [pair for pair in unfinished_proxied_pairs if not pair[1]]

        if have_html:
            # get page size to decide whether to take a screenshot
            capture_screenshot = False
            pixel_count = 0
            try:
                root_element = browser.find_element_by_tag_name('body')
            except (NoSuchElementException, URLError):
                try:
                    root_element = browser.find_element_by_tag_name('frameset')
                except (NoSuchElementException, URLError):
                    # If we can't find the root element, we just won't capture a screenshot.
                    # NoSuchElementException: HTML structure is weird somehow.
                    # URLError: the headless browser has gone away for some reason.
                    root_element = None
            if root_element:
                page_size = root_element.size
                pixel_count = page_size['width'] * page_size['height']
                capture_screenshot = pixel_count < settings.MAX_IMAGE_SIZE

            # take screenshot after all requests done
            if capture_screenshot:
                progress += 1
                display_progress(progress, "Taking screenshot")
                screenshot_data = browser.get_screenshot_as_png()
                link.screenshot_capture.write_warc_resource_record(screenshot_data)
                save_fields(link.screenshot_capture, status='success')
            else:
                print "Not saving screenshots! %s" % ("Page size is %s pixels." % pixel_count if pixel_count else "")
                save_fields(link.screenshot_capture, status='failed')
        else:
            # no screenshot if not HTML
            save_fields(link.screenshot_capture, status='failed')

    except HaltCaptureException:
        pass

    finally:
        # teardown (have to do this before save to make sure WARC is done writing):
        print "Shutting down browser and proxies."

        for thread in thread_list:
            # wait until threads are done (have to do this before closing phantomjs)
            if hasattr(thread, 'stop'):
                thread.stop.set()
            thread.join()
        if browser:
            browser.quit()  # shut down phantomjs
        if display:
            display.stop()  # shut down virtual display
        if warcprox_controller:
            warcprox_controller.stop.set()  # send signal to shut down warc thread
        if warcprox_thread:
            warcprox_thread.join()  # wait until warcprox thread is done writing out warc

        # un-suppress logging
        logging.disable(logging.NOTSET)

    # save generated warc file
    if have_warc:
        progress += 1
        display_progress(progress, "Saving web archive file")

        temp_warc_path = os.path.join(warc_writer.directory,
                                      warc_writer._f_finalname)
        with open(temp_warc_path, 'rb') as warc_file:
            link.write_warc_raw_data(warc_file)

        print "Writing CDX lines to the DB"
        CDXLine.objects.create_all_from_link(link)

        save_fields(
            link.primary_capture,
            status='success',
            content_type=content_type,
        )
        save_fields(
            link,
            warc_size=default_storage.size(link.warc_storage_file())
        )
        capture_job.mark_completed()

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

        print "%s capture succeeded." % link.guid


@shared_task()
def update_stats():
    """
    run once per minute by celerybeat. logs our minute-by-minute activity,
    and also rolls our weekly stats (perma.models.WeekStats)
    """

    # On the first minute of the new week, roll our weekly stats entry
    now = timezone.now()
    if now.weekday() == 6 and now.hour == 0 and now.minute == 0:
        week_to_close = WeekStats.objects.latest('start_date')
        week_to_close.end_date = now
        week_to_close.save()
        new_week = WeekStats(start_date=now)
        new_week.save()


    # We only need to keep a day of data for our visualization.
    # TODO: this is 1560 minutes is 26 hours, that likely doesn't
    # cover everyone outside of the east coast. Our vis should
    # be timezone aware. Fix this.
    if MinuteStats.objects.all().count() == 1560:
        MinuteStats.objects.all()[0].delete()


    # Add our new minute measurements
    a_minute_ago = now - timedelta(seconds=60)

    links_sum = Link.objects.filter(creation_timestamp__gt=a_minute_ago).count()
    users_sum = LinkUser.objects.filter(date_joined__gt=a_minute_ago).count()
    organizations_sum = Organization.objects.filter(date_created__gt=a_minute_ago).count()
    registrars_sum = Registrar.objects.approved().filter(date_created__gt=a_minute_ago).count()

    new_minute_stat = MinuteStats(links_sum=links_sum, users_sum=users_sum,
        organizations_sum=organizations_sum, registrars_sum=registrars_sum)
    new_minute_stat.save()


    # Add our minute activity to our current weekly sum
    if links_sum or users_sum or organizations_sum or registrars_sum:
        current_week = WeekStats.objects.latest('start_date')
        current_week.end_date = now
        current_week.links_sum += links_sum
        current_week.users_sum += users_sum
        current_week.organizations_sum += organizations_sum
        current_week.registrars_sum += registrars_sum
        current_week.save()


@shared_task(bind=True)
def delete_from_internet_archive(self, link_guid):
    if not settings.UPLOAD_TO_INTERNET_ARCHIVE:
        return

    identifier = settings.INTERNET_ARCHIVE_IDENTIFIER_PREFIX + link_guid
    link = Link.objects.get(guid=link_guid)
    item = internetarchive.get_item(identifier)

    if not item.exists:
        return False
    for f in item.files:
        file = item.get_file(f["name"])
        file.delete(
            verbose=True,
            cascade_delete=True,
            access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY,
            secret_key=settings.INTERNET_ARCHIVE_SECRET_KEY,
        )

    metadata = {
        "description":"",
        "contributor":"",
        "sponsor":"",
        "submitted_url":"",
        "perma_url":"",
        "title":"Removed",
        "external-identifier":"",
        "imagecount":"",
    }

    item.modify_metadata(
            metadata,
            access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY,
            secret_key=settings.INTERNET_ARCHIVE_SECRET_KEY,
        )

    link.internet_archive_upload_status = 'deleted'
    link.save()

@shared_task()
def upload_all_to_internet_archive():
    """
        Links to upload:
        - links that have not started to upload
        - links that have failed to upload but not failed permanently (those should not exist, but doesn't hurt to look)
        - links that have previously been deleted from internet archive (is_private=True) but have since been made public
        - only links that are older than 24 hours
    """
    links = Link.objects.filter((Q(internet_archive_upload_status='not_started') |
                                Q(internet_archive_upload_status='failed') |
                                Q(internet_archive_upload_status='deleted', is_private=False)) &
                                Q(creation_timestamp__lte=timezone.now()-timedelta(days=1)))

    for link in links:
        if link.can_upload_to_internet_archive():
            run_task(upload_to_internet_archive.s(link_guid=link.guid))


@shared_task(bind=True)
def upload_to_internet_archive(self, link_guid):
    try:
        link = Link.objects.get(guid=link_guid)

        if link.internet_archive_upload_status == 'failed_permanently':
            return

    except:
        print "Link %s does not exist" % link_guid
        return

    if not settings.UPLOAD_TO_INTERNET_ARCHIVE:
        return

    if not link.can_upload_to_internet_archive():
        print "Not eligible for upload."
        return

    metadata = {
        "collection":settings.INTERNET_ARCHIVE_COLLECTION,
        "title":'%s: %s' % (link_guid, truncatechars(link.submitted_title, 50)),
        "mediatype":'web',
        "description":'Perma.cc archive of %s created on %s.' % (link.submitted_url, link.creation_timestamp,),
        "contributor":'Perma.cc',
        "submitted_url":link.submitted_url,
        "perma_url":"http://%s/%s" % (settings.HOST, link_guid),
        "external-identifier":'urn:X-perma:%s' % link_guid,
    }

    identifier = settings.INTERNET_ARCHIVE_IDENTIFIER_PREFIX + link_guid
    try:
        if default_storage.exists(link.warc_storage_file()):
            item = internetarchive.get_item(identifier)

            # if item already exists (but has been removed),
            # ia won't update its metadata in upload function
            if item.exists and item.metadata['title'] == 'Removed':
                item.modify_metadata(metadata,
                    access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY,
                    secret_key=settings.INTERNET_ARCHIVE_SECRET_KEY,
                )

            warc_name = os.path.basename(link.warc_storage_file())

            # copy warc to local disk storage for upload
            temp_warc_file = tempfile.TemporaryFile()
            copy_file_data(default_storage.open(link.warc_storage_file()), temp_warc_file)
            temp_warc_file.seek(0)

            success = internetarchive.upload(
                            identifier,
                            {warc_name:temp_warc_file},
                            metadata=metadata,
                            access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY,
                            secret_key=settings.INTERNET_ARCHIVE_SECRET_KEY,
                            retries=10,
                            retries_sleep=60,
                            verbose=True,
                        )

            if success:
                link.internet_archive_upload_status = 'completed'
                link.save()

            else:
                link.internet_archive_upload_status = 'failed'
                self.retry(exc=Exception("Internet Archive reported upload failure."))

            return
        else:
            link.internet_archive_upload_status = 'failed_permanently'
            link.save()

    except requests.ConnectionError as e:
        logger.exception("Upload to Internet Archive task failed because of a connection error. \nLink GUID: %s\nError: %s" % (link.pk, e))
        return

@shared_task()
def cm_sync():
    '''
       Sync our current list of registrar users plus some associated metadata
       to Campaign Monitor.

       Run daily at 3am by celerybeat
    '''

    reports = sync_cm_list(settings.CAMPAIGN_MONITOR_REGISTRAR_LIST,
                           registrar_users_plus_stats(destination='cm'))
    if reports["import"]["duplicates_in_import_list"]:
        logger.error("Duplicate reigstrar users sent to Campaign Monitor. Check sync logic.")
    send_admin_email("Registrar Users Synced to Campaign Monitor",
                      settings.DEFAULT_FROM_EMAIL,
                      HttpRequest(),
                      'email/admin/sync_to_cm.txt',
                      {"reports": reports})
    return json.dumps(reports)
