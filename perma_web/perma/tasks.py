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

import logging
logger = logging.getLogger(__name__)

### CONSTANTS ###

ROBOTS_TXT_TIMEOUT = 30 # seconds to wait before giving up on robots.txt
ONLOAD_EVENT_TIMEOUT = 30 # seconds to wait before giving up on the onLoad event and proceeding as though it fired
RESOURCE_LOAD_TIMEOUT = 45 # seconds to wait for at least one resource to load before giving up on capture
ELEMENT_DISCOVERY_TIMEOUT = 2 # seconds before PhantomJS gives up running a DOM request (should be instant, assuming page is loaded)
AFTER_LOAD_TIMEOUT = 30 # seconds to allow page to keep loading additional resources after onLoad event fires
VALID_FAVICON_MIME_TYPES = {'image/png', 'image/gif', 'image/jpg', 'image/jpeg', 'image/x-icon', 'image/vnd.microsoft.icon', 'image/ico'}

### THREAD HELPERS ###

def run_capture_component(thread_list, func, **kwargs):
    """
       Run in a new thread, unless THREADED_CAPTURES is False (for debugging)
    """
    if settings.THREADED_CAPTURES:
        add_thread(thread_list, func, **kwargs)
    else:
        func(**kwargs["kwargs"])

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

def get_url(url, thread_list, proxy_address):
    """
        Get a url, via proxied python requests.get(), in a way that is interruptable from other threads.
        Blocks calling thread. Perma assumes only run from sub-threads, and settings.THREADED_CAPTURES = True.
        Unexpected blocking may result otherwise.
    """
    request_thread = add_thread(thread_list, ProxiedRequestThread(proxy_address, url))
    request_thread.join()
    return request_thread.response, request_thread.response_exception

class ProxiedRequestThread(threading.Thread):
    """
        Run python request.get() in a thread, loading data in chunks.
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


# BROWSER HELPERS

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

def run_in_frames(link, browser, func, output_collector=None):
    # setup
    browser.implicitly_wait(0)

    if output_collector is None:
        output_collector = []
    run_in_frames_recursive(link, browser, func, output_collector)

    # reset
    browser.implicitly_wait(ELEMENT_DISCOVERY_TIMEOUT)
    browser.switch_to.default_content()

    return output_collector

def run_in_frames_recursive(link, browser, func, output_collector, frame_path=None):
    if frame_path is None:
        frame_path = []
    with browser_running(link, browser):
        output_collector += func(browser)
        for child_frame in browser.find_elements_by_tag_name('frame') + browser.find_elements_by_tag_name('iframe'):
            browser.switch_to.default_content()
            for frame in frame_path:
                browser.switch_to.frame(frame)
            try:
                browser.switch_to.frame(child_frame)
                run_in_frames_recursive(link, browser, func, output_collector, frame_path + [child_frame])
            except (ValueError, NoSuchFrameException):
                # switching to frame failed for some reason
                print "run_in_frames_recursive caught exception switching to iframe:"
                traceback.print_exc()


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

# meta tags

def meta_thread(browser=None, link=None):
    meta_tags = meta_tags_get(browser, link)
    if meta_tags:
        meta_tags_process(meta_tags, link)

def meta_tags_get(browser, link):
    """
        Retrieves meta tags. Returns a list of dicts, keys=name, content.
        Uses js instead of selenium for speed.
    """
    def get_meta():
        with browser_running(link, browser, lambda: meta_tag_analysis_failed(link)):
            return browser.execute_script("""
                var meta_tags = document.getElementsByTagName('meta');
                var tags = [];
                for (var i = 0; i < meta_tags.length; i++){
                    tags.push({"name":meta_tags[i].name, "content":meta_tags[i].content});
                }
                return tags
            """)
    return repeat_until_truthy(get_meta)

def meta_tags_process(meta_tags, link):
    """Do what we want with the meta tags we find."""

    ## Privacy Related ##
    # first look for <meta name='perma'>
    meta_tag = next((tag for tag in meta_tags if tag['name'].lower()=='perma'), None)
    # else look for <meta name='robots'>
    if not meta_tag:
        meta_tag = next((tag for tag in meta_tags if tag['name'].lower() == 'robots'), None)
    # if we found a relevant meta tag, check for noarchive
    if meta_tag and 'noarchive' in meta_tag["content"].lower():
        safe_save_fields(link, is_private=True, private_reason='policy')
        print "Meta found, darchiving"

    ## Page Description ##
    description_meta_tag = next((tag for tag in meta_tags if tag['name'].lower() == 'description'), '')
    if description_meta_tag and description_meta_tag['content']:
        safe_save_fields(link, submitted_description=description_meta_tag['content'])

def meta_tag_analysis_failed(link):
    """What to do if analysis of a link's meta tags fails"""
    if settings.PRIVATE_LINKS_ON_FAILURE:
        safe_save_fields(link, is_private=True, private_reason='failure')
    print "Meta tag retrieval failure."
    link.tags.add('meta-tag-retrieval-failure')

# robots.txt

def robots_txt_thread(link=None, target_url=None, content_url=None, thread_list=None, proxy_address=None):
    robots_txt_location = urlparse.urljoin(content_url, '/robots.txt')
    robots_txt_response, e = get_url(robots_txt_location, thread_list, proxy_address)
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

def favicon_thread(successful_favicon_urls=None, browser=None, content_url=None, thread_list=None, proxy_address=None):
    favicon_urls = favicon_get_urls(browser, content_url)
    for favicon_url in favicon_urls:
        favicon = favicon_fetch(favicon_url, thread_list, proxy_address)
        if favicon:
            successful_favicon_urls.append(favicon)
    if not successful_favicon_urls:
        print "Couldn't get any favicons"

def favicon_get_urls(browser, content_url):
    """
        Retrieves favicon urls.
        Uses js instead of selenium for speed.
    """
    urls = []
    urls = browser.execute_script("""
        var links = document.querySelectorAll('link[rel="shortcut icon"],link[rel="icon"]');
        var urls = [];
        for (var i = 0; i < links.length; i++){
            urls.push(links[i].getAttribute('href'))
        }
        return urls
    """)
    urls.append('/favicon.ico')
    return (make_absolute_urls(content_url, urls))

def favicon_fetch(url, thread_list, proxy_address):
    print "Fetching favicon from %s ..." % url
    response, e = get_url(url, thread_list, proxy_address)
    if e or not response or not response.ok:
        print "Favicon failed:", e, response
        return
    # apply mime type whitelist
    mime_type = response.headers.get('content-type', '').split(';')[0]
    if mime_type in VALID_FAVICON_MIME_TYPES:
        return (url, mime_type)

# media

def get_media_tags(browser):
    url_list = []
    base_url = browser.current_url
    print("Fetching images in srcsets")
    get_srcset_image_urls(url_list, base_url, browser)
    if settings.ENABLE_AV_CAPTURE:
        print("Fetching audio/video objects")
        get_audio_video_urls(url_list, base_url, browser)
        get_object_urls(url_list, base_url, browser)
    return url_list

def get_srcset_image_urls(url_list, base_url, browser):
    """
       Appends all urls listed in img/src srcset attributes
       to a passed in url_list.
       Uses js instead of selenium for speed.
    """
    urls = browser.execute_script("""
        var images = document.querySelectorAll('img[srcset], source[srcset]');
        var urls = [];
        for (var i = 0; i < images.length; i++){
            var srcs = images[i].getAttribute('srcset').split(',');
            for (var j = 0; j < srcs.length; j++){
                urls.push(srcs[j].trim().split(' ')[0])
            }
        }
        return urls
    """)
    url_list.extend(make_absolute_urls(base_url, urls))

def get_audio_video_urls(url_list, base_url, browser):
    """
       Appends urls from 'video', 'audio', 'embed' tags
       to a passed in url_list.

       Get src attribute and any <source src="url"> elements.
       Uses js instead of selenium for speed.
    """
    urls = browser.execute_script("""
        var media_tags = document.querySelectorAll('video, audio, embed');
        var urls = [];
        for (var i = 0; i < media_tags.length; i++){
            urls.push(media_tags[i].getAttribute('src'))
            var srcs = media_tags[i].getElementsByTagName('source');
            for (var j = 0; j < srcs.length; j++){
                urls.push(srcs[j].getAttribute('src'))
            }
        }
        return urls
    """)
    url_list.extend(make_absolute_urls(base_url, urls))

def get_object_urls(url_list, base_url, browser):
    '''
        Appends urls from 'object' tags to a passed in url_list.

        Get the data and archive attributes, prepended with codebase attribute if it exists,
        as well as any <param name="movie" value="url"> elements
    '''
    url_pairs = browser.execute_script("""
        var base_url = "%s";
        var url_pairs = [];
        var object_tags = document.querySelectorAll('object');
        for (var i = 0; i < object_tags.length; i++){
            var tag = object_tags[i];
            var codebase_url = tag.getAttribute('codebase') || base_url;

            // data attribute
            url_pairs.push([codebase_url, tag.getAttribute('data')]);

            // archive attribute can be a space-separated list
            var archive = (tag.getAttribute('archive') || '').split(' ');
            for (var j = 0; j < archive.length; j++){
                url_pairs.push([codebase_url, archive[j]]);
            }

            // params
            var params = tag.querySelectorAll('param[name="movie"]')
            for (var j = 0; j < params.length; j++){
                url_pairs.push([codebase_url, params[j].getAttribute('value')]);
            }
        }
        return url_pairs
    """ % (base_url,))
    urls = [urlparse.urljoin(url[0], url[1]) for url in url_pairs if url[1]]
    url_list.extend(make_absolute_urls(base_url, urls))

# page title

def get_title(link, browser):
    if browser.title:
        safe_save_fields(link, submitted_title=browser.title)
    else:
        title_element = browser.find_element_by_tag_name("title")
        safe_save_fields(link, submitted_title=title_element.get_attribute("text"))

# screenshot

def get_screenshot(link, browser):
    pixels = get_page_pixel_count(browser)
    if page_pixels_in_allowed_range(pixels):
        screenshot_data = browser.get_screenshot_as_png()
        link.screenshot_capture.write_warc_resource_record(screenshot_data)
        safe_save_fields(link.screenshot_capture, status='success')
    else:
        print "Not taking screenshot! %s" % ("Page size is %s pixels." % pixels if pixels else "(none)")
        safe_save_fields(link.screenshot_capture, status='failed')

def get_page_pixel_count(browser):
    try:
        root_element = browser.find_element_by_tag_name('body')
    except (NoSuchElementException, URLError):
        try:
            root_element = browser.find_element_by_tag_name('frameset')
        except (NoSuchElementException, URLError):
            # NoSuchElementException: HTML structure is weird somehow.
            # URLError: the headless browser has gone away for some reason.
            root_element = None
    if root_element:
        page_size = root_element.size
        return page_size['width'] * page_size['height']

def page_pixels_in_allowed_range(pixel_count):
    return pixel_count and pixel_count < settings.MAX_IMAGE_SIZE

### CAPTURE COMPLETION

def teardown(thread_list, browser, display, warcprox_controller, warcprox_thread):
    print("Shutting down browser and proxies.")
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

def save_primary(inc_progress, warc_writer, link, content_type):
    inc_progress(1, "Saving web archive file")
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
def browser_running(link, browser, onfailure=None):
    if browser_still_running(browser):
        yield
    else:
        print("Browser crashed")
        link.tags.add('browser-crashed')
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
        link = capture_job.link
        target_url = link.safe_url
        browser = warcprox_controller = warcprox_thread = display = None
        have_content = have_warc = have_html = False
        thread_list = []
        successful_favicon_urls = []

        def inc_progress(step_count, step_description):
            """
                Update capture_job's progress

                (defined inside capture function so that
                step is initialized at 0 for each capture job)
            """
            if not hasattr(inc_progress, 'step'):
                inc_progress.step = 0
            inc_progress.step = int(inc_progress.step) + step_count
            safe_save_fields(capture_job, step_count=inc_progress.step, step_description=step_description)
            print "%s step %s: %s" % (link.guid, inc_progress.step, step_description)

        # By domain, code to run after the target_url's page onload event.
        # (Wrap in a lambda function to delay execution.)
        special_domains = {
            # Wait for splash page to auto redirect
            "www.forbes.com": lambda: sleep_unless_seconds_passed(24, start_time),
            "forbes.com": lambda: sleep_unless_seconds_passed(24, start_time)
        }
        post_load_function = special_domains.get(link.url_details.netloc)

        # Get started, unless the user has deleted the capture in the meantime
        inc_progress(0, "Starting capture")
        if link.user_deleted or link.primary_capture.status != "pending":
            capture_job.mark_completed('deleted')
            return
        capture_job.attempt += 1
        capture_job.save()

        try:
            # BEGIN WARCPROX SETUP

            # Create a request handler class that tracks requests and responses
            # via in-scope, shared mutable containers. (Define inside capture function
            # so the containers are initialized empty for every new capture.)
            proxied_requests = []
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
                    if proxied_responses["limit_reached"] or \
                       capture_current_size(thread_list, proxied_responses["size"]) > settings.MAX_ARCHIVE_FILE_SIZE:
                        proxied_responses["limit_reached"] = True
                        return

                    with tracker_lock:
                        proxied_pair = [self.url, None]
                        proxied_requests.append(proxied_pair[0])
                        proxied_pairs.append(proxied_pair)
                    try:
                        response = WarcProxyHandler._proxy_request(self)
                    except:
                        # If warcprox can't handle a request/response for some reason,
                        # remove the proxied pair so that it doesn't keep trying and
                        # the capture process can proceed
                        proxied_requests.remove(proxied_pair[0])
                        proxied_pairs.remove(proxied_pair)
                        raise
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

            # start virtual display
            if settings.CAPTURE_BROWSER != "PhantomJS":
                display = Display(visible=0, size=(1024, 800))
                display.start()

            browser = get_browser(settings.CAPTURE_USER_AGENT, proxy_address, proxy.ca.ca_file)
            browser.set_window_size(1024, 800)

            # fetch page in the background
            inc_progress(1, "Fetching target URL")
            start_time = time.time()
            page_load_thread = threading.Thread(target=browser.get, args=(target_url,))  # returns after onload
            page_load_thread.start()

            # before proceeding further, wait until warcprox records a response that isn't a forward
            with browser_running(link, browser):
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

                    inc_progress(wait_time/RESOURCE_LOAD_TIMEOUT, "Fetching target URL")
                    time.sleep(1)

            print "Fetching robots.txt ..."
            run_capture_component(thread_list, robots_txt_thread, kwargs={
                "link": link,
                "target_url": target_url,
                "content_url": content_url,
                "thread_list": thread_list,
                "proxy_address": proxy_address
            })

            inc_progress(1, "Checking x-robots-tag directives.")
            if xrobots_blacklists_perma(robots_directives):
                safe_save_fields(link, is_private=True, private_reason='policy')
                print "x-robots-tag found, darchiving"

            if have_html:
                # DO EVERYTHING THAT'S SAFE TO DO BEFORE "ONLOAD" IS FIRED
                # (which can take a long time, and might even crash the browser)

                # check meta tags
                with browser_running(link, browser, onfailure=lambda: meta_tag_analysis_failed(link)):
                    print "Checking meta tags."
                    run_capture_component(thread_list, meta_thread, kwargs={
                        "browser": browser,
                        "link": link
                    })

                # get favicon urls (saved as favicon_capture_url later)
                with browser_running(link, browser):
                    print "Fetching favicons ..."
                    run_capture_component(thread_list, favicon_thread, kwargs={
                        "successful_favicon_urls": successful_favicon_urls,
                        "browser": browser,
                        "content_url": content_url,
                        "thread_list": thread_list,
                        "proxy_address": proxy_address
                    })

                # WAIT FOR "ONLOAD" FOR EVERYTHING ELSE
                print("Waiting for onload event before proceding.")
                page_load_thread.join(ONLOAD_EVENT_TIMEOUT)
                if page_load_thread.isAlive():
                    print("Onload timed out")
                if post_load_function:
                    print("Running domain's post-load function")
                    post_load_function()

                print("Finished fetching URL.")

                with browser_running(link, browser):
                    inc_progress(1, "Getting page title")
                    repeat_while_exception(get_title, arglist=[link, browser], raise_after_timeout=False)

                with browser_running(link, browser):
                    inc_progress(0.5, "Checking for scroll-loaded assets")
                    repeat_while_exception(scroll_browser, arglist=[browser], raise_after_timeout=False)

                with browser_running(link, browser):
                    inc_progress(1, "Fetching media")
                    with warn_on_exception("Error fetching media"):
                        media_urls = run_in_frames(link, browser, get_media_tags)
                        # grab all media urls that aren't already being grabbed,
                        # each in its own background thread
                        for media_url in set(media_urls) - set(proxied_requests):
                            add_thread(thread_list, ProxiedRequestThread(proxy_address, media_url))

            # Wait AFTER_LOAD_TIMEOUT seconds for any requests to finish that are started within the next .5 seconds.
            inc_progress(1, "Waiting for post-load requests")
            time.sleep(.5)
            unfinished_proxied_pairs = [pair for pair in proxied_pairs if not pair[1]]
            load_time = time.time()
            with browser_running(link, browser):
                while unfinished_proxied_pairs and browser_still_running(browser):

                    print "Waiting for %s pending requests" % len(unfinished_proxied_pairs)
                    # give up after AFTER_LOAD_TIMEOUT seconds
                    wait_time = time.time() - load_time
                    if wait_time > AFTER_LOAD_TIMEOUT:
                        print "Waited %s seconds to finish post-load requests -- giving up." % AFTER_LOAD_TIMEOUT
                        break

                    # Show progress to user
                    inc_progress(wait_time/AFTER_LOAD_TIMEOUT, "Waiting for post-load requests")

                    # Sleep and update our list
                    time.sleep(.5)
                    unfinished_proxied_pairs = [pair for pair in unfinished_proxied_pairs if not pair[1]]

            # screenshot capture of html pages (not pdf, etc.)
            # (after all requests have loaded for best quality)
            if have_html and browser_still_running(browser):
                inc_progress(1, "Taking screenshot")
                get_screenshot(link, browser)
            else:
                safe_save_fields(link.screenshot_capture, status='failed')

        except HaltCaptureException:
            print("HaltCaptureException thrown")
    except SoftTimeLimitExceeded:
        capture_job.link.tags.add('timeout-failure')
    except:
        print "Exception while processing capture job %s:" % capture_job.link_id
        traceback.print_exc()
    finally:
        try:
            teardown(thread_list, browser, display, warcprox_controller, warcprox_thread)

            # un-suppress logging
            logging.disable(logging.NOTSET)

            # save generated warc file
            if have_warc:
                save_primary(inc_progress, warc_writer, link, content_type)
                capture_job.mark_completed()

            # We only save the Capture for the favicon once the warc is stored,
            # since the data for the favicon lives in the warc.
            save_favicons(link, successful_favicon_urls)

            print "%s capture succeeded." % link.guid

        except:
            print "Exception while processing capture job %s:" % capture_job.link_id
            traceback.print_exc()
        finally:
            capture_job.link.captures.filter(status='pending').update(status='failed')
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
