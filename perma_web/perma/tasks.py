from __future__ import absolute_import # to avoid importing local .celery instead of celery package

import tempfile
import traceback
from cStringIO import StringIO
from collections import OrderedDict
from contextlib import contextmanager
from pyquery import PyQuery

from httplib import HTTPResponse
from urllib2 import URLError

import os
import os.path
import threading
import Queue as queue
import time
from datetime import timedelta
import urlparse
import re
import json
import robotparser
import errno
import tempdir
from socket import error as socket_error
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchElementException, NoSuchFrameException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import ProxyType, Proxy
from pyvirtualdisplay import Display
import warcprox
from warcprox.controller import WarcproxController
from warcprox.warcprox import WarcProxyHandler, WarcProxy, ProxyingRecorder
from warcprox.warcwriter import WarcWriter, WarcWriterThread
import requests
from requests.structures import CaseInsensitiveDict
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import internetarchive

from django.core.files.storage import default_storage
from django.template.defaultfilters import truncatechars
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.http import HttpRequest

from perma.models import WeekStats, MinuteStats, Registrar, LinkUser, Link, Organization, CDXLine, Capture, CaptureJob
from perma.email import sync_cm_list, send_admin_email, registrar_users_plus_stats
from perma.utils import run_task, url_in_allowed_ip_range, copy_file_data
from perma import site_scripts

import logging
logger = logging.getLogger(__name__)

### CONSTANTS ###

ROBOTS_TXT_TIMEOUT = 30 # seconds to wait before giving up on robots.txt
ONLOAD_EVENT_TIMEOUT = 30 # seconds to wait before giving up on the onLoad event and proceeding as though it fired
RESOURCE_LOAD_TIMEOUT = 45 # seconds to wait for at least one resource to load before giving up on capture
ELEMENT_DISCOVERY_TIMEOUT = 2 # seconds before PhantomJS gives up running a DOM request (should be instant, assuming page is loaded)
AFTER_LOAD_TIMEOUT = 30 # seconds to allow page to keep loading additional resources after onLoad event fires
VALID_FAVICON_MIME_TYPES = {'image/png', 'image/gif', 'image/jpg', 'image/jpeg', 'image/x-icon', 'image/vnd.microsoft.icon', 'image/ico'}
BROWSER_SIZE = [1024, 800]


### THREAD HELPERS ###

def add_thread(thread_list, target, **kwargs):
    if not isinstance(target, threading.Thread):
        target = threading.Thread(target=target, **kwargs)
    target.start()
    thread_list.append(target)
    return target

def safe_save_fields(instance, **kwargs):
    """
        Update and save the given fields for a model instance.
        Use update_fields so we won't step on changes to other fields made in another thread.
    """
    for key, val in kwargs.items():
        setattr(instance, key, val)
    instance.save(update_fields=kwargs.keys())

def get_url(url, thread_list, proxy_address, requested_urls):
    """
        Get a url, via proxied python requests.get(), in a way that is interruptable from other threads.
        Blocks calling thread. (Recommended: only call in sub-threads.)
    """
    request_thread = add_thread(thread_list, ProxiedRequestThread(proxy_address, url, requested_urls))
    request_thread.join()
    return request_thread.response, request_thread.response_exception

class ProxiedRequestThread(threading.Thread):
    """
        Run python request.get() in a thread, loading data in chunks.
        Listen for self.stop to be set, allowing requests to be halted by other threads.
        While the thread is running, see `self.pending_data` for how much has been downloaded so far.
        Once the thread is done, see `self.response` and `self.response_exception` for the results.
    """
    def __init__(self, proxy_address, url, requested_urls, *args, **kwargs):
        self.url = url
        self.proxy_address = proxy_address
        self.pending_data = 0
        self.stop = threading.Event()
        self.response = None
        self.response_exception = None
        self.requested_urls = requested_urls
        super(ProxiedRequestThread, self).__init__(*args, **kwargs)

    def run(self):
        try:
            self.requested_urls.add(self.url)
            self.response = requests.get(self.url,
                                         headers={'User-Agent': settings.CAPTURE_USER_AGENT},
                                         proxies={'http': 'http://' + self.proxy_address, 'https': 'http://' + self.proxy_address},
                                         verify=False,
                                         stream=True,
                                         timeout=1)
            self.response._content = bytes()
            for chunk in self.response.iter_content(chunk_size=8192):
                self.pending_data += len(chunk)
                self.response._content += chunk
                if self.stop.is_set():
                    return
        except requests.RequestException as e:
            self.response_exception = e
        finally:
            self.pending_data = 0

class HaltCaptureException(Exception):
    """
        An exception we can trigger to halt capture and release
        all involved resources.
    """
    pass


# WARCPROX HELPERS

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

# monkeypatch WarcProxy so request threads are daemons, and don't stop
# the parent python process from quitting normally
_orig_threading_mixin = warcprox.warcprox.socketserver.ThreadingMixIn
_orig_threading_mixin.daemon_threads = True


# BROWSER HELPERS

def start_virtual_display():
    display = Display(visible=0, size=BROWSER_SIZE)
    display.start()
    return display

def get_browser(user_agent, proxy_address, cert_path):
    """ Set up a Selenium browser with given user agent, proxy and SSL cert. """

    display = None
    print "Using browser: %s" % settings.CAPTURE_BROWSER

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
                "--local-storage-path=."
            ],
            service_log_path=settings.PHANTOMJS_LOG)

    # Firefox
    elif settings.CAPTURE_BROWSER == 'Firefox':
        display = start_virtual_display()

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
        display = start_virtual_display()

        # http://blog.likewise.org/2015/01/setting-up-chromedriver-and-the-selenium-webdriver-python-bindings-on-ubuntu-14-dot-04/
        download_dir = os.path.abspath('./downloads')
        os.mkdir(download_dir)
        chrome_options = webdriver.ChromeOptions()

        # To use Chrome beta channel, if installed:
        # chrome_options.binary_location = '/usr/bin/google-chrome-beta'

        chrome_options.add_argument('--proxy-server=%s' % proxy_address)
        chrome_options.add_argument('--test-type')  # needed?
        # chrome_options.add_argument('--headless')  # not selenium compatible yet, keep using start_virtual_display for now
        chrome_options.add_argument('--disable-gpu')  # needed?
        chrome_options.add_argument('--hide-scrollbars')  # not currently working -- see workaround in get_screenshot
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

    return browser, display

def browser_still_running(browser):
    return browser.service.process.poll() is None

def scroll_browser(browser):
    """scroll to bottom of page"""
    # TODO: This doesn't scroll horizontally or scroll frames
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

def get_page_source(browser):
    """
        Get page source.
        Use JS rather than browser.page_source so we get the parsed, properly formatted DOM instead of raw user HTML.
    """
    return browser.execute_script("return document.documentElement.outerHTML")

def parse_page_source(source):
    """
        Return page source as a parsed PyQuery object for querying.

        PyQuery here works the same as `$(source)` in jQuery. So for example you can do `parsed_source(selector)`
        with the returned value to get a list of LXML elements matching the selector.
    """
    return PyQuery(source, parser='html')

def get_dom_tree(browser):
    with browser_running(browser):
        return parse_page_source(get_page_source(browser))

def get_all_dom_trees(browser):
    with browser_running(browser):
        return run_in_frames(browser, lambda browser: [[browser.current_url, get_dom_tree(browser)]])

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

def run_in_frames_recursive(browser, func, output_collector, frame_path=None):
    DEPTH_LIMIT = 3  # deepest frame level we'll visit
    FRAME_LIMIT = 20  # max total frames we'll visit
    if frame_path is None:
        frame_path = []

    with browser_running(browser):
        # slow to run, so only uncomment logging if needed for debugging:
        # import hashlib
        # print frame_path, browser.find_elements_by_tag_name('html')[0]._id, hashlib.sha256(browser.page_source.encode('utf8')).hexdigest(), browser.execute_script("return window.location.href")

        # skip about:blank, about:srcdoc, and any other non-http frames
        current_url = browser.current_url
        if not (current_url.startswith('http:') or current_url.startswith('https:')):
            return

        # run func in current frame
        output_collector += func(browser)

        # stop looking for subframes if we hit depth limit
        if len(frame_path) > DEPTH_LIMIT:
            return

        # run in subframes of current frame
        for i in range(FRAME_LIMIT):

            # stop looking for subframes if we hit total frames limit
            if len(output_collector) > FRAME_LIMIT:
                return

            # call self recursively in child frame i
            try:
                browser.switch_to.frame(i)
                run_in_frames_recursive(browser, func, output_collector, frame_path + [i])
            except NoSuchFrameException:
                # we've run out of subframes
                break
            except ValueError:
                # switching to frame failed for some reason (does this still apply?)
                print "run_in_frames_recursive caught exception switching to iframe:"
                traceback.print_exc()

            # return to current frame
            browser.switch_to.default_content()
            try:
                for frame in frame_path:
                    browser.switch_to.frame(frame)
            except NoSuchFrameException:
                # frame hierarchy changed; frame_path is invalid
                print "frame hierarchy changed while running run_in_frames_recursive"
                break


### UTILS ###

def repeat_while_exception(func, arglist=[], exception=Exception, timeout=10, sleep_time=.1, raise_after_timeout=True):
    """
       Keep running a function until it completes without raising an exception,
       or until "timeout" is reached.

       Useful when retrieving page elements via Selenium.
    """
    end_time = time.time() + timeout
    while True:
        try:
            return func(*arglist)
        except SoftTimeLimitExceeded:
            raise
        except exception:
            if time.time() > end_time:
                if raise_after_timeout:
                    raise
                return
            time.sleep(sleep_time)

def repeat_until_truthy(func, arglist=[], timeout=10, sleep_time=.1):
    """
        Keep running a function until it returns a truthy value, or until
        "timeout" is reached. No exception handling.

        Useful when retrieving page elements via javascript run by Selenium.
    """
    end_time = time.time() + timeout
    result = None
    while not result:
        if time.time() > end_time:
            break
        result = func(*arglist)
        time.sleep(sleep_time)
    return result

def sleep_unless_seconds_passed(seconds, start_time):
    delta = time.time() - start_time
    if delta < seconds:
        wait = seconds - delta
        print("Sleeping for {}s".format(wait))
        time.sleep(wait)


# CAPTURE HELPERS

def inc_progress(capture_job, inc, description):
    capture_job.inc_progress(inc, description)
    print "%s step %s: %s" % (capture_job.link.guid, capture_job.step_count, capture_job.step_description)

def capture_current_size(thread_list, recorded):
    """
        Amount captured so far is the sum of the bytes recorded by warcprox,
        and the bytes pending in our background threads.
    """
    return recorded + sum(getattr(thread, 'pending_data', 0) for thread in thread_list)

def make_absolute_urls(base_url, urls):
    """collect resource urls, converted to absolute urls relative to current browser frame"""
    return [urlparse.urljoin(base_url, url) for url in urls if url]

def parse_response(response_text):
    """
        Given an HTTP response line and headers, as a string,
        return a requests.Response object.
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


### CAPTURE COMPONENTS ###

# on load

# By domain, code to run after the target_url's page onload event.
post_load_function_lookup = {
    "^https?://www.forbes.com/forbes/welcome": site_scripts.forbes_post_load
}
def get_post_load_function(browser):
    current_url = browser.current_url
    for regex, post_load_function in post_load_function_lookup.items():
        if re.search(regex, current_url.lower()):
            return post_load_function
    return None

# x-robots headers

def xrobots_blacklists_perma(robots_directives):
    darchive = False
    if robots_directives:
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
    return darchive

# page metadata

def get_metadata(page_metadata, dom_tree):
    """
        Retrieve html page metadata.
    """
    page_metadata.update({
        'meta_tags': get_meta_tags(dom_tree),
        'title': get_title(dom_tree)
    })

def get_meta_tags(dom_tree):
    """
        Retrieves meta tags as a dict (e.g. {"robots": "noarchive"}).

        The keys of the dict are the "name" attributes of the meta tags (if
        any) and the values are the corresponding "content" attributes.
        Later-encountered tags overwrite earlier-encountered tags, if a
        "name" attribute is duplicated in the html. Tags without name
        attributes are thrown away (their "content" attribute is mapped
        to the key "", the empty string).
    """
    return {tag.attrib['name'].lower(): tag.attrib.get('content', '')
            for tag in dom_tree('meta')
            if tag.attrib.get('name')}

def get_title(dom_tree):
    return dom_tree('head > title').text()

def meta_tag_analysis_failed(link):
    """What to do if analysis of a link's meta tags fails"""
    if settings.PRIVATE_LINKS_ON_FAILURE:
        safe_save_fields(link, is_private=True, private_reason='failure')
    print "Meta tag retrieval failure."
    link.tags.add('meta-tag-retrieval-failure')

# robots.txt

def robots_txt_thread(link, target_url, content_url, thread_list, proxy_address, requested_urls):
    robots_txt_location = urlparse.urljoin(content_url, '/robots.txt')
    robots_txt_response, e = get_url(robots_txt_location, thread_list, proxy_address, requested_urls)
    if e or not robots_txt_response or not robots_txt_response.ok:
        print "Couldn't reach robots.txt"
        return
    print "Robots.txt fetched."

    # We only want to respect robots.txt if Perma is specifically asked not to archive (we're not a crawler)
    if 'Perma' in robots_txt_response.content:
        # We found Perma specifically mentioned
        rp = robotparser.RobotFileParser()
        rp.parse([line.strip() for line in robots_txt_response.content.split('\n')])
        if not rp.can_fetch('Perma', target_url):
            safe_save_fields(link, is_private=True, private_reason='policy')
            print "Robots.txt disallows Perma."

# favicons

def favicon_thread(successful_favicon_urls, dom_tree, content_url, thread_list, proxy_address, requested_urls):
    favicon_urls = favicon_get_urls(dom_tree, content_url)
    for favicon_url in favicon_urls:
        favicon = favicon_fetch(favicon_url, thread_list, proxy_address, requested_urls)
        if favicon:
            successful_favicon_urls.append(favicon)
    if not successful_favicon_urls:
        print "Couldn't get any favicons"

def favicon_get_urls(dom_tree, content_url):
    """
        Retrieve favicon URLs from DOM.
    """
    urls = []  # order here matters so that we prefer meta tag favicon over /favicon.ico
    for el in dom_tree('link'):
        if el.attrib.get('rel', '').lower() in ("shortcut icon", "icon"):
            href = el.attrib.get('href')
            if href:
                urls.append(href)
    urls.append('/favicon.ico')
    urls = make_absolute_urls(content_url, urls)
    urls = list(OrderedDict((url, True) for url in urls).keys())  # remove duplicates without changing list order
    return urls

def favicon_fetch(url, thread_list, proxy_address, requested_urls):
    print "Fetching favicon from %s ..." % url
    response, e = get_url(url, thread_list, proxy_address, requested_urls)
    if e or not response or not response.ok:
        print "Favicon failed:", e, response
        return
    # apply mime type whitelist
    mime_type = response.headers.get('content-type', '').split(';')[0]
    if mime_type in VALID_FAVICON_MIME_TYPES:
        return (url, mime_type)

# media

def get_media_tags(dom_trees):
    urls = set()
    for base_url, dom_tree in dom_trees:
        print("Fetching images in srcsets")
        new_urls = get_srcset_image_urls(dom_tree)
        if settings.ENABLE_AV_CAPTURE:
            print("Fetching audio/video objects")
            new_urls += get_audio_video_urls(dom_tree)
            new_urls += get_object_urls(dom_tree)
        urls |= set(make_absolute_urls(base_url, new_urls))
    return urls

def get_srcset_image_urls(dom_tree):
    """
       Return all urls listed in img/src srcset attributes.
    """
    urls = []
    for el in dom_tree('img[srcset], source[srcset]'):
        for src in el.attrib.get('srcset', '').split(','):
            src = src.strip().split()[0]
            if src:
                urls.append(src)
    return urls

def get_audio_video_urls(dom_tree):
    """
       Return urls listed in video/audio/embed/source tag src attributes.
    """
    urls = []
    for el in dom_tree('video, audio, embed, source'):
        src = el.attrib.get('src', '').strip()
        if src:
            urls.append(src)
    return urls

def get_object_urls(dom_tree):
    """
        Return urls in object tag data/archive attributes, as well as object -> param[name="movie"] tag value attributes.
        Urls will be relative to the object tag codebase attribute if it exists.
    """
    urls = []
    for el in dom_tree('object'):
        codebase_url = el.attrib.get('codebase')
        el_urls = [el.attrib.get('data', '')] + \
                  el.attrib.get('archive', '').split() + \
                  [param.attrib.get('value', '') for param in PyQuery(el)('param[name="movie"]')]
        for url in el_urls:
            url = url.strip()
            if url:
                if codebase_url:
                    url = urlparse.urljoin(codebase_url, url)
                urls.append(url)
    return urls

# screenshot

def get_screenshot(link, browser):
    page_size = get_page_size(browser)
    if page_pixels_in_allowed_range(page_size):

        if settings.CAPTURE_BROWSER == 'Chrome':
            # workaround for failure of --hide-scrollbars flag in Chrome:
            browser.execute_script("""
                ['body', 'html', 'frameset'].forEach(function(elType){
                    try {
                        document.getElementsByTagName(elType)[0].style.overflow = 'hidden';
                    } catch(e) {}
                });
            """)

            # set window size to page size in Chrome, so we get a full-page screenshot:
            browser.set_window_size(max(page_size['width'], BROWSER_SIZE[0]), max(page_size['height'], BROWSER_SIZE[1]))

        screenshot_data = browser.get_screenshot_as_png()
        link.screenshot_capture.write_warc_resource_record(screenshot_data)
        safe_save_fields(link.screenshot_capture, status='success')
    else:
        print "Not taking screenshot! %s" % ("Page size is %s." % (page_size,))
        safe_save_fields(link.screenshot_capture, status='failed')

def get_page_size(browser):
    try:
        root_element = browser.find_element_by_tag_name('html')
    except (NoSuchElementException, URLError):
        try:
            root_element = browser.find_element_by_tag_name('frameset')
        except (NoSuchElementException, URLError):
            # NoSuchElementException: HTML structure is weird somehow.
            # URLError: the headless browser has gone away for some reason.
            root_element = None
    if root_element:
        return root_element.size

def page_pixels_in_allowed_range(page_size):
    return page_size and page_size['width'] * page_size['height'] < settings.MAX_IMAGE_SIZE

### CAPTURE COMPLETION

def teardown(link, thread_list, browser, display, warcprox_controller, warcprox_thread):
    print("Shutting down browser and proxies.")
    for thread in thread_list:
        # wait until threads are done (have to do this before closing phantomjs)
        if hasattr(thread, 'stop'):
            thread.stop.set()
        thread.join()
    if browser:
        if not browser_still_running(browser):
            link.tags.add('browser-crashed')
        browser.quit()  # shut down phantomjs
    if display:
        display.stop()  # shut down virtual display
    if warcprox_controller:
        warcprox_controller.stop.set()  # send signal to shut down warc thread
    if warcprox_thread:
        warcprox_thread.join()  # wait until warcprox thread is done writing out warc

def process_metadata(metadata, link):
    ## Privacy Related ##
    meta_tag = metadata['meta_tags'].get('perma')
    if not meta_tag:
        meta_tag = metadata['meta_tags'].get('robots')
    if meta_tag and 'noarchive' in meta_tag.lower():
        safe_save_fields(link, is_private=True, private_reason='policy')
        print "Meta found, darchiving"

    ## Page Description ##
    description_meta_tag = metadata['meta_tags'].get('description')
    if description_meta_tag:
        safe_save_fields(link, submitted_description=description_meta_tag)

    ## Page Title
    safe_save_fields(link, submitted_title=metadata['title'])

def save_primary(warc_writer, link, content_type):
    temp_warc_path = os.path.join(warc_writer.directory,
                                  warc_writer._f_finalname)
    with open(temp_warc_path, 'rb') as warc_file:
        link.write_warc_raw_data(warc_file)

    print("Writing CDX lines to the DB")
    CDXLine.objects.create_all_from_link(link)

    safe_save_fields(
        link.primary_capture,
        status='success',
        content_type=content_type,
    )
    safe_save_fields(
        link,
        warc_size=default_storage.size(link.warc_storage_file())
    )

def save_favicons(link, successful_favicon_urls):
    if successful_favicon_urls:
        Capture(
            link=link,
            role='favicon',
            status='success',
            record_type='response',
            url=successful_favicon_urls[0][0],
            content_type=successful_favicon_urls[0][1]
        ).save()
        print "Saved favicons %s" % successful_favicon_urls

### CONTEXT MANAGERS

@contextmanager
def warn_on_exception(message="Exception in block:", exception_type=Exception):
    try:
        yield
    except exception_type as e:
        print message, e

@contextmanager
def browser_running(browser, onfailure=None):
    if browser_still_running(browser):
        yield
    else:
        print("Browser crashed")
        if onfailure:
            onfailure()
        raise HaltCaptureException


### TASKS ##

@shared_task
@tempdir.run_in_tempdir()
def run_next_capture():
    """
        Grab and run the next CaptureJob. This will keep calling itself until there are no jobs left.
    """
    capture_job = CaptureJob.get_next_job(reserve=True)
    if not capture_job:
        return  # no jobs waiting
    try:
        # Start warcprox process. Warcprox is a MITM proxy server and needs to be running
        # before, during and after the headless browser.
        #
        # Start a headless browser to capture the supplied URL. Also take a screenshot if the URL is an HTML file.
        #
        # This whole function runs with the local dir set to a temp dir by run_in_tempdir().
        # So we can use local paths for temp files, and they'll just disappear when the function exits.

        # basic setup
        start_time = time.time()
        link = capture_job.link
        target_url = link.safe_url
        browser = warcprox_controller = warcprox_thread = display = None
        have_content = have_warc = have_html = False
        thread_list = []
        page_metadata = {}
        successful_favicon_urls = []
        requested_urls = set()  # all URLs we have requested -- used to avoid duplicate requests

        # Get started, unless the user has deleted the capture in the meantime
        inc_progress(capture_job, 0, "Starting capture")
        if link.user_deleted or link.primary_capture.status != "pending":
            capture_job.mark_completed('deleted')
            return
        capture_job.attempt += 1
        capture_job.save()

        # BEGIN WARCPROX SETUP

        # Create a request handler class that tracks requests and responses
        # via in-scope, shared mutable containers. (Define inside capture function
        # so the containers are initialized empty for every new capture.)
        proxied_responses = {
          "any": False,
          "size": 0,
          "limit_reached": False
        }
        proxied_pairs = []
        tracker_lock = threading.Lock()
        class TrackingRequestHandler(WarcProxyHandler):
            def _proxy_request(self):

                # make sure we don't capture anything in a banned IP range
                if not url_in_allowed_ip_range(self.url):
                    return

                # skip request if downloaded size exceeds MAX_ARCHIVE_FILE_SIZE.
                if proxied_responses["limit_reached"]:
                    return
                elif capture_current_size(thread_list, proxied_responses["size"]) > settings.MAX_ARCHIVE_FILE_SIZE:
                    proxied_responses["limit_reached"] = True
                    print("size limit reached")
                    return

                with tracker_lock:
                    proxied_pair = [self.url, None]
                    requested_urls.add(proxied_pair[0])
                    proxied_pairs.append(proxied_pair)
                try:
                    response = WarcProxyHandler._proxy_request(self)
                except Exception as e:
                    # If warcprox can't handle a request/response for some reason,
                    # remove the proxied pair so that it doesn't keep trying and
                    # the capture process can proceed
                    proxied_pairs.remove(proxied_pair)
                    print("WarcProx exception: %s parsing response from %s" % (e.__class__.__name__, proxied_pair[0]))
                    return  # swallow exception
                with tracker_lock:
                    proxied_responses["any"] = True
                    proxied_responses["size"] += response.response_recorder.len
                    proxied_pair[1] = response

        # suppress verbose warcprox logs
        logging.disable(logging.INFO)

        # connect warcprox to an open port
        warcprox_port = 27500
        recorded_url_queue = queue.Queue()
        for i in xrange(500):
            try:
                proxy = WarcProxy(
                    server_address=("127.0.0.1", warcprox_port),
                    recorded_url_q=recorded_url_queue,
                    req_handler_class=TrackingRequestHandler
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
        # END WARCPROX SETUP

        browser, display = get_browser(settings.CAPTURE_USER_AGENT, proxy_address, proxy.ca.ca_file)
        browser.set_window_size(*BROWSER_SIZE)

        # fetch page in the background
        inc_progress(capture_job, 1, "Fetching target URL")
        page_load_thread = threading.Thread(target=browser.get, args=(target_url,))  # returns after onload
        page_load_thread.start()

        # before proceeding further, wait until warcprox records a response that isn't a forward
        with browser_running(browser):
            while not have_content:
                if proxied_responses["any"]:
                    for request, response in proxied_pairs:
                        if response is None:
                            # wait for the first response to finish, so we have the best chance
                            # at successfully identifying the content-type of the target_url
                            # (in unusual circumstances, can be incorrect)
                            break
                        if response.url.endswith('/favicon.ico') and response.url != target_url:
                            continue
                        if not hasattr(response, 'parsed_response'):
                            response.parsed_response = parse_response(response.response_recorder.headers)
                        if response.parsed_response.is_redirect or response.parsed_response.status_code == 206:  # partial content
                            continue

                        have_content = True
                        content_url = response.url
                        content_type = response.parsed_response.headers.get('content-type')
                        robots_directives = response.parsed_response.headers.get('x-robots-tag')
                        have_html = content_type and content_type.startswith('text/html')
                        break

                if have_content:
                    # at this point we have something that's worth showing to the user
                    have_warc = True
                    break

                wait_time = time.time() - start_time
                if wait_time > RESOURCE_LOAD_TIMEOUT:
                    raise HaltCaptureException

                inc_progress(capture_job, wait_time/RESOURCE_LOAD_TIMEOUT, "Fetching target URL")
                time.sleep(1)

        print "Fetching robots.txt ..."
        add_thread(thread_list, robots_txt_thread, args=(
            link,
            target_url,
            content_url,
            thread_list,
            proxy_address,
            requested_urls
        ))

        inc_progress(capture_job, 1, "Checking x-robots-tag directives.")
        if xrobots_blacklists_perma(robots_directives):
            safe_save_fields(link, is_private=True, private_reason='policy')
            print "x-robots-tag found, darchiving"

        if have_html:

            # Get a copy of the page's metadata immediately, without
            # waiting for the page's onload event (which can take a
            # long time, and might even crash the browser)
            print("Retrieving DOM (pre-onload)")
            dom_tree = get_dom_tree(browser)
            get_metadata(page_metadata, dom_tree)

            # get favicon urls (saved as favicon_capture_url later)
            with browser_running(browser):
                print "Fetching favicons ..."
                add_thread(thread_list, favicon_thread, args=(
                    successful_favicon_urls,
                    dom_tree,
                    content_url,
                    thread_list,
                    proxy_address,
                    requested_urls
                ))

            print("Waiting for onload event before proceeding.")
            page_load_thread.join(max(0, ONLOAD_EVENT_TIMEOUT - (time.time() - start_time)))
            if page_load_thread.is_alive():
                print("Onload timed out")
            with browser_running(browser):
                post_load_function = get_post_load_function(browser)
                if post_load_function:
                    print("Running domain's post-load function")
                    post_load_function(browser)

            # Get a fresh copy of the page's metadata, if possible.
            print("Retrieving DOM (post-onload)")
            dom_tree = get_dom_tree(browser)
            get_metadata(page_metadata, dom_tree)

            with browser_running(browser):
                inc_progress(capture_job, 0.5, "Checking for scroll-loaded assets")
                repeat_while_exception(scroll_browser, arglist=[browser], raise_after_timeout=False)


            inc_progress(capture_job, 1, "Fetching media")
            with warn_on_exception("Error fetching media"):
                dom_trees = get_all_dom_trees(browser)
                get_metadata(page_metadata, dom_trees[0][1])
                media_urls = get_media_tags(dom_trees)
                # grab all media urls that aren't already being grabbed,
                # each in its own background thread
                for media_url in media_urls - requested_urls:
                    add_thread(thread_list, ProxiedRequestThread(proxy_address, media_url, requested_urls))

        # Wait AFTER_LOAD_TIMEOUT seconds for any requests to finish that are started within the next .5 seconds.
        inc_progress(capture_job, 1, "Waiting for post-load requests")
        time.sleep(.5)
        unfinished_proxied_pairs = [pair for pair in proxied_pairs if not pair[1]]
        load_time = time.time()
        with browser_running(browser):
            while unfinished_proxied_pairs and browser_still_running(browser):

                print "Waiting for %s pending requests" % len(unfinished_proxied_pairs)
                # give up after AFTER_LOAD_TIMEOUT seconds
                wait_time = time.time() - load_time
                if wait_time > AFTER_LOAD_TIMEOUT:
                    print "Waited %s seconds to finish post-load requests -- giving up." % AFTER_LOAD_TIMEOUT
                    break

                # Show progress to user
                inc_progress(capture_job, wait_time/AFTER_LOAD_TIMEOUT, "Waiting for post-load requests")

                # Sleep and update our list
                time.sleep(.5)
                unfinished_proxied_pairs = [pair for pair in unfinished_proxied_pairs if not pair[1]]

        # screenshot capture of html pages (not pdf, etc.)
        # (after all requests have loaded for best quality)
        if have_html and browser_still_running(browser):
            inc_progress(capture_job, 1, "Taking screenshot")
            get_screenshot(link, browser)
        else:
            safe_save_fields(link.screenshot_capture, status='failed')

    except HaltCaptureException:
        print("HaltCaptureException thrown")
    except SoftTimeLimitExceeded:
        link.tags.add('timeout-failure')
    except:
        print "Exception while processing capture job %s:" % capture_job.link_id
        traceback.print_exc()
    finally:
        try:
            teardown(link, thread_list, browser, display, warcprox_controller, warcprox_thread)

            # un-suppress logging
            logging.disable(logging.NOTSET)

            # save page metadata
            if have_html:
                if page_metadata:
                    process_metadata(page_metadata, link)
                else:
                    meta_tag_analysis_failed(link)

            # save generated warc file
            if have_warc:
                inc_progress(capture_job, 1, "Saving web archive file")
                save_primary(warc_writer, link, content_type)
                capture_job.mark_completed()

            # We only save the Capture for the favicon once the warc is stored,
            # since the data for the favicon lives in the warc.
            save_favicons(link, successful_favicon_urls)

            print "%s capture succeeded." % link.guid

        except:
            print "Exception while processing capture job %s:" % capture_job.link_id
            traceback.print_exc()
        finally:
            link.captures.filter(status='pending').update(status='failed')
            if capture_job.status == 'in_progress':
                capture_job.mark_completed('failed')
    run_task(run_next_capture.s())


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
    # find all links created 48-24 hours ago
    # include timezone
    start_date = timezone.now() - timedelta(days=2)
    end_date   = timezone.now() - timedelta(days=1)

    links = Link.objects.filter(Q(internet_archive_upload_status='not_started') | Q(internet_archive_upload_status='failed'), creation_timestamp__range=(start_date, end_date))
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

    except SoftTimeLimitExceeded as e:
        logger.exception("Upload to Internet Archive task failed because soft time limit was exceeded. \nLink GUID: %s\nError: %s" % (link.pk, e))
        return

@shared_task()
def cm_sync():
    """
       Sync our current list of registrar users plus some associated metadata
       to Campaign Monitor.

       Run daily at 3am by celerybeat
    """

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
