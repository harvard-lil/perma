from __future__ import print_function

import socket
import os
import subprocess
import unittest
import re
import datetime
import sys
from urlparse import urlparse
import requests

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException, NoSuchElementException
import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from perma.wsgi import application as wsgi_app
from perma.settings import SAUCE_USERNAME, SAUCE_ACCESS_KEY, USE_SAUCE, TIMEGATE_WARC_ROUTE, WARC_ROUTE


# In this file we point a browser at a test server and navigate the site.
# There are two separate choices to make:
# (1) is the server remote, or a local Django test server we start for the occasion?
# (2) is the browser a local PhantomJS browser, or a set of remote Sauce browsers?
#
# Examples:
#
# Local browser, local server:
# $ fab test:functional_tests
#
# Remote Sauce browsers, local server:
# $ fab dev.sauce_tunnel &  # (keep this open in the background for all tests)
# $ fab dev.test_sauce
#
# Remote Sauce browsers, remote server:
# $ fab dev.test_sauce:https://perma.cc


# (1) Configure remote vs. local server:

REMOTE_SERVER_URL = os.environ.get('SERVER_URL')
LOCAL_SERVER_DOMAIN = 'perma.dev'
build_name = datetime.datetime.now().isoformat().split('.')[0]

if REMOTE_SERVER_URL:
    BaseTestCase = unittest.TestCase
    build_name += '-' + REMOTE_SERVER_URL  # pretty label for remote jobs: datetime-target_url

else:
    BaseTestCase = StaticLiveServerTestCase
    assert socket.gethostbyname(LOCAL_SERVER_DOMAIN) in ('0.0.0.0', '127.0.0.1'), "Please add `127.0.0.1 " + LOCAL_SERVER_DOMAIN + "` to your hosts file before running this test."
    build_name += subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()  # pretty label for local jobs: datetime-git_branch


# (2) Configure Sauce vs. local PhantomJS browsers:

if USE_SAUCE:
    from sauceclient import SauceClient
    assert SAUCE_USERNAME and SAUCE_ACCESS_KEY, "Please make sure that SAUCE_USERNAME and SAUCE_ACCESS_KEY are set."
    sauce = SauceClient(SAUCE_USERNAME, SAUCE_ACCESS_KEY)

    # options: https://saucelabs.com/platforms
    browsers = [
        # Chrome
        {"platform": "Mac OS X 10.10",
        "browserName": "chrome",
        "version": "45"},

        {"platform": "Windows 7",
         "browserName": "chrome",
         "version": "45"},

        # Safari
        {"platform": "OS X 10.10",
         "browserName": "safari",
         "version": "8.0"},

        # IE
        {"platform": "Windows 8.1",
        "browserName": "internet explorer",
        "version": "11"},

        {"platform": "Windows 7",
         "browserName": "internet explorer",
         "version": "9.0"},

        # Firefox
        {"platform": "Windows 7",
        "browserName": "firefox",
        "version": "40"},

        # iOS
        {"platform": "OS X 10.10",
        "browserName": "iPhone",
        "version": "8.4",
        "deviceOrientation": "portrait",
        "deviceName": "iPhone 6",},
    ]

else:
    browsers = [{}]  # single PhantomJS test case with empty dict -- no special desired_capabilities


## helpers

def on_platforms(platforms):
    """
        Generate a version of the test case class for each platform.
        via: https://github.com/Victory/django-travis-saucelabs/blob/master/mysite/saucetests/tests.py
    """
    def decorator(base_class):
        module = sys.modules[base_class.__module__].__dict__
        for i, platform in enumerate(platforms):
            d = dict(base_class.__dict__, desired_capabilities=platform)
            name = "%s_%s" % (base_class.__name__, i + 1)
            module[name] = type(name, (base_class,), d)
    return decorator


## the actual tests!

@on_platforms(browsers)
class FunctionalTest(BaseTestCase):
    fixtures = ['fixtures/sites.json',
                'fixtures/users.json',
                'fixtures/folders.json']

    base_desired_capabilities = {
        'loggingPrefs': {'browser': 'ALL'}
    }

    virtual_display = None

    def setUp(self):
        if REMOTE_SERVER_URL:
            self.server_url = REMOTE_SERVER_URL
        else:
            # By default, the test server only mounts the django app,
            # which will leave out the warc app, so mount them both here
            self.server_thread.httpd.set_app(self.server_thread.static_handler(wsgi_app))
            self.server_thread.host = LOCAL_SERVER_DOMAIN

            self.server_url = self.live_server_url

        if USE_SAUCE:
            self.setUpSauce()
        else:
            self.setUpLocal()

        self.driver.implicitly_wait(5)

    def tearDown(self):
        if USE_SAUCE:
            self.tearDownSauce()
        else:
            self.tearDownLocal()

    def setUpSauce(self):
        desired_capabilities = dict(self.base_desired_capabilities, **self.desired_capabilities)
        desired_capabilities['name'] = self.id()
        desired_capabilities['build'] = build_name

        sauce_url = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"
        self.driver = webdriver.Remote(
            desired_capabilities=desired_capabilities,
            command_executor=sauce_url % (SAUCE_USERNAME, SAUCE_ACCESS_KEY)
        )
        socket.setdefaulttimeout(300)  # spinning up iOS browser can take a few minutes

    def setUpLocal(self):
        try:
            # use Firefox if available on local system
            self.virtual_display = Display(visible=0, size=(1024, 800))
            self.virtual_display.start()
            self.driver = webdriver.Firefox(capabilities=self.base_desired_capabilities)
        except RuntimeError:
            self.driver = webdriver.PhantomJS(desired_capabilities=self.base_desired_capabilities)
        print("Using %s for integration tests." % (type(self.driver)))
        socket.setdefaulttimeout(30)
        self.driver.set_window_size(1024, 800)

    def tearDownLocal(self):
        self.driver.quit()
        if self.virtual_display:
            self.virtual_display.stop()

    def tearDownSauce(self):
        print("Link to your job: https://saucelabs.com/jobs/%s" % self.driver.session_id)
        try:
            if sys.exc_info() == (None, None, None):
                sauce.jobs.update_job(self.driver.session_id, passed=True)
            else:
                sauce.jobs.update_job(self.driver.session_id, passed=False)
        finally:
            self.driver.quit()

    def test_all(self):

        # helpers
        def click_link(link_text):
            get_element_with_text(link_text, 'a').click()

        def get_xpath(xpath):
            return self.driver.find_element_by_xpath(xpath)

        def get_css_selector(selector):
            return self.driver.find_element_by_css_selector(selector)

        def get_id(id):
            return self.driver.find_element_by_id(id)

        def get_element_with_text(text, element_type='*'):
            return get_xpath("//%s[contains(text(),'%s')]" % (element_type, text))

        def is_displayed(element, repeat=True):
            """ Check if element is displayed, by default retrying for 10 seconds if false. """
            if repeat:
                def repeater():
                    assert element.is_displayed()
                    return True
                try:
                    repeat_while_exception(repeater, AssertionError)
                except AssertionError:
                    return False
            return element.is_displayed()

        def assert_text_displayed(text, element_type='*'):
            self.assertTrue(is_displayed(get_element_with_text(text, element_type)))

        def type_to_element(element, text):
            element.click()
            element.send_keys(text)

        def info(*args):
            if USE_SAUCE:
                infoSauce(*args)
            else:
                infoLocal(*args)

        def infoSauce(*args):
            print("%s %s %s:" % (
                self.desired_capabilities['platform'],
                self.desired_capabilities['browserName'],
                self.desired_capabilities['version'],
            ), *args)

        def infoLocal(*args):
            print(*args)

        def repeat_while_exception(func, exception=Exception, timeout=10, sleep_time=.1):
            end_time = time.time()+timeout
            while True:
                try:
                    return func()
                except exception:
                    if time.time()>end_time:
                        raise
                    time.sleep(sleep_time)

        def fix_host(url):
            if REMOTE_SERVER_URL:
                return url
            o = urlparse(url)
            o = o._replace(scheme='http',
                           netloc="{0}:{1}".format(self.server_thread.host,
                                                   self.server_thread.port))
            return o.geturl()

        info("Starting functional tests at time:", datetime.datetime.utcnow())
        
        info("Loading homepage from %s." % self.server_url)
        self.driver.get(self.server_url)
        assert_text_displayed("Perma.cc is simple") # new text on landing now

        ##### cut this since it no longer exists

        # info("Checking Perma In Action section.")
        #try:
        #    get_xpath("//a[@data-img='MSC_1']").click()
        #    self.assertTrue(is_displayed(get_id('example-title')))
        #    get_xpath("//div[@id='example-image-wrapper']/img").click()  # click on random element to trigger Sauce screenshot
        #except ElementNotVisibleException:
        #    pass  # this section is hidden for mobile browsers, so just skip this test

        info("Loading docs.")
        try:
            get_css_selector('.navbar-toggle').click()  # show navbar in mobile view
        except ElementNotVisibleException:
            pass  # not in mobile view
        get_xpath("//a[@href='/docs']").click()
        assert_text_displayed('Perma.cc user guide')  # new text -- wait for load

        info("Logging in.")
        try:
            get_css_selector('.navbar-toggle').click()  # show navbar in mobile view
        except ElementNotVisibleException:
            pass  # not in mobile view
        repeat_while_exception(lambda: click_link("Log in"))
        assert_text_displayed("Email address", 'label')
        get_id('id_username').send_keys('test_user@example.com')
        get_id('id_password').send_keys('pass')
        get_xpath("//button[@class='btn login']").click() # new design button, no more 'btn-success'
        assert_text_displayed('Create a new', 'h1')  # wait for load

        info("Creating archive.")
        url_to_capture = 'example.com'
        type_to_element(get_id('rawUrl'), url_to_capture)  # type url
        # choose folder from dropdown
        get_css_selector('#folder-tree > .jstree-container-ul > li:last-child > a').click()

        get_id('addlink').click() # submit

        info("Viewing playback.")
        # wait 60 seconds to be forwarded to archive page
        repeat_while_exception(lambda: get_element_with_text('See the Screenshot View', 'a'), NoSuchElementException, 60)
        # Get the guid of the created archive
        # display_guid = fix_host(self.driver.current_url)[-9:]
        # Grab the WARC url for later.
        warc_url = fix_host(self.driver.find_elements_by_tag_name("iframe")[0].get_attribute('src'))
        # Check out the screeshot.
        get_element_with_text('See the Screenshot View', 'a').click()
        assert_text_displayed('This is a screenshot.')
        # Load the WARC URL separately, because Safari driver doesn't let us inspect it as an iframe
        self.driver.get(warc_url)
        assert_text_displayed('This domain is established to be used for illustrative examples', 'p')

        # My Links

        # show links
        self.driver.get(self.server_url + '/manage/create')
        # create folder
        get_css_selector('.new-folder').click()
        # find link
        # assert_text_displayed(display_guid)
        # show details
        # get_css_selector('.item-row').click()
        # for some reason these are throwing 500 errors on PATCH:
        # # change title
        # type_to_element(get_css_selector('input.link-title'), 'test')
        # repeat_while_exception(get_xpath("//span[contains(@class,'title-save-status') and contains(text(),'saved.')]"), NoSuchElementException)
        # # change notes
        # type_to_element(get_css_selector('input.link-notes'), 'test')
        # repeat_while_exception(get_xpath("//span[contains(@class,'notes-save-status') and contains(text(),'saved.')]"), NoSuchElementException)

        # Redirect from org-specific url to general /create url
        self.driver.get(self.server_url + '/manage/create/27')
        current_url = self.driver.current_url
        self.assertEquals(self.server_url + '/manage/create/', current_url)

        # Timemap

        info("Checking timemap.")
        self.driver.get(self.server_url + '/warc/pywb/*/' + url_to_capture)
        self.assertIsNotNone(re.search(r'<b>[1-9]\d*</b> captures?', self.driver.page_source))  # Make sure that `<b>foo</b> captures` shows a positive number of captures
        assert_text_displayed('http://' + url_to_capture, 'b')

        # Displays playback by timestamp
        get_xpath("//a[contains(@href, '%s')]" % url_to_capture).click()
        assert_text_displayed('This domain is established to be used for illustrative examples', 'p')

        info("Checking timegate")
        self.driver.get(self.server_url + TIMEGATE_WARC_ROUTE  + "/" + url_to_capture)

        assert_text_displayed('This domain is established to be used for illustrative examples', 'p')

        # timegate redirects to a memento (timestamped) url
        str_to_match = "%s%s/\d+/http://%s" % (self.server_url, WARC_ROUTE, url_to_capture)
        reg = re.compile(str_to_match)
        self.assertIsNotNone(reg.search(self.driver.current_url))
        # checking that we don't see /warc/timegate in url because of redirect
        reg = re.compile(TIMEGATE_WARC_ROUTE)
        self.assertFalse(reg.match(self.driver.current_url))


        # taking advantage of running server to check headers
        response = requests.get(self.server_url + TIMEGATE_WARC_ROUTE + '/' + url_to_capture)

        # response is memento response that's a redirect from the timegate url
        link_headers = response.headers['Link'].split(', ')
        for header in link_headers:
            if 'rel="timemap"' in header:
                reg = re.compile('%s/timemap/*/' % WARC_ROUTE)
                self.assertIsNotNone(reg.search(header))

            if 'rel="memento"' in header:
                reg = re.compile('%s%s/\d+/http://%s' % (self.server_url, WARC_ROUTE, url_to_capture))
                self.assertIsNotNone(reg.search(header))
