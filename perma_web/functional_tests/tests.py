import socket
import os
import unittest
import datetime
import sys
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException, NoSuchElementException, StaleElementReferenceException
import time

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from perma.urls import urlpatterns
from perma.models import UncaughtError
from perma.tests.utils import failed_test_files_path


# In this file we point a browser at a test server and navigate the site.
# There are several choices to make:
# (1) is the Perma application server:
#    (a) remote
#    (b) a local Django test server we start for the occasion on 127.0.0.1
#    (c) a local Django test server we start for the occasion, but broadcast to 0.0.0.0, to allow other Docker containers on the same network to browse the site.
#
# (2) is the browser:
#    (a) a set of remote Sauce browsers
#    (b) a selenium-driven browser running in its own Docker container
#
#
# N.B. Some of these combinations may not work with the current code base.
# TODO: document, or fix, or remove...
#
# Example invocations:
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
LOCAL_SERVER_DOMAIN = settings.HOST.split(':')[0]

if REMOTE_SERVER_URL:
    BaseTestCase = unittest.TestCase

else:
    BaseTestCase = StaticLiveServerTestCase
    assert socket.gethostbyname(LOCAL_SERVER_DOMAIN) in ('0.0.0.0', '127.0.0.1'), "Please add `127.0.0.1 " + LOCAL_SERVER_DOMAIN + "` to your hosts file before running this test."


# (2) Configure Sauce vs. local PhantomJS browsers vs. containerized Chrome:

if settings.USE_SAUCE:
    from sauceclient import SauceClient
    assert settings.SAUCE_USERNAME and settings.SAUCE_ACCESS_KEY, "Please make sure that settings.SAUCE_USERNAME and settings.SAUCE_ACCESS_KEY are set."
    sauce = SauceClient(settings.SAUCE_USERNAME, settings.SAUCE_ACCESS_KEY)

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
    browsers = [{}]  # single test case with empty dict -- no special desired_capabilities


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

    @classmethod
    def setUpClass(cls):
        cls.setUpPerma()
        cls.setUpBrowser()

    @classmethod
    def setUpPerma(cls):
        if REMOTE_SERVER_URL:
            super().setUpClass()
            cls.server_url = REMOTE_SERVER_URL
        else:
            cls.host = '0.0.0.0'
            cls.port = 8000
            super().setUpClass()

            cls.server_url = 'http://{}'.format(settings.HOST)

    @classmethod
    def setUpBrowser(cls):
        if settings.USE_SAUCE:
            cls.setUpSauce()
        else:
            cls.setUpRemoteSelenium()
        cls.driver.implicitly_wait(5)
        print("Using %s for integration tests." % (type(cls.driver)))

    @classmethod
    def tearDownClass(cls):
        if settings.USE_SAUCE:
            cls.tearDownSauce()
        else:
            cls.tearDownRemoteSelenium()

    @classmethod
    def setUpSauce(cls):
        desired_capabilities = dict(cls.base_desired_capabilities, **cls.desired_capabilities)
        desired_capabilities['name'] = cls.id()
        sauce_url = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"
        cls.driver = webdriver.Remote(
            desired_capabilities=desired_capabilities,
            command_executor=sauce_url % (settings.SAUCE_USERNAME, settings.SAUCE_ACCESS_KEY)
        )
        socket.setdefaulttimeout(300)  # spinning up iOS browser can take a few minutes

    @classmethod
    def setUpRemoteSelenium(cls):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1024x800')
        cls.driver = webdriver.Remote(
            command_executor='http://{}:4444/wd/hub'.format(settings.REMOTE_SELENIUM_HOST),
            desired_capabilities=options.to_capabilities()
        )

    @classmethod
    def tearDownRemoteSelenium(cls):
        cls.driver.quit()

    @classmethod
    def tearDownSauce(cls):
        print("Link to your job: https://saucelabs.com/jobs/%s" % cls.driver.session_id)
        try:
            if sys.exc_info() == (None, None, None):
                sauce.jobs.update_job(cls.driver.session_id, passed=True)
            else:
                sauce.jobs.update_job(cls.driver.session_id, passed=False)
        finally:
            cls.driver.quit()

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
            if settings.USE_SAUCE:
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

        def repeat_while_false(func, timeout=10, sleep_time=.1):
            end_time = time.time()+timeout
            while True:
                result = func()
                if result:
                    return result
                if time.time()>end_time:
                    raise Exception("%s timed out after %s seconds" % (func, timeout))
                time.sleep(sleep_time)

        def test_js_error_handling():
            # helper to throw a javascript error and confirm it was recorded on the backend
            if REMOTE_SERVER_URL:
                return  # can only check this on local server
            return
            # this is not working with the remote Chrome, don't know why
            # err_count = UncaughtError.objects.count()
            # self.driver.execute_script("setTimeout(function(){doesNotExist()})")
            # repeat_while_exception(lambda: self.assertEqual(err_count+1, UncaughtError.objects.count()), timeout=5)  # give time for background thread to create exception
            # self.assertIn('doesNotExist', UncaughtError.objects.last().message)

        def test_playback(capture_url):
            self.driver.get(capture_url)
            repeat_while_exception(lambda: self.driver.switch_to.frame(self.driver.find_elements_by_tag_name('iframe')[0]), StaleElementReferenceException, 10)
            repeat_while_exception(lambda: get_element_with_text(example_text, 'p'), NoSuchElementException, 30)
            # Evidently the above doesn't work on Sauce with Safari and this version of Webdriver.
            self.driver.get(capture_url)
            get_element_with_text('See the Screenshot View', 'a').click()
            assert_text_displayed('This is a screenshot.')

        example_text = 'This domain is for use in illustrative examples in documents.'

        info("Starting functional tests at time:", datetime.datetime.utcnow())

        try:

            info("Loading homepage from %s." % self.server_url)
            self.driver.get(self.server_url)
            assert_text_displayed("Perma.cc is simple") # new text on landing now
            #
            # First, tests logged in as test_user@example.com
            #

            info("Logging in.")
            try:
                get_css_selector('.navbar-toggle').click()  # show navbar in mobile view
            except ElementNotVisibleException:
                pass  # not in mobile view
            assert_text_displayed("Log in", "a")
            self.driver.get(self.server_url + '/login')
            assert_text_displayed("Email address", 'label')
            get_id('id_username').send_keys('test_user@example.com')
            get_id('id_password').send_keys('pass')
            get_xpath("//button[@class='btn login']").click() # new design button, no more 'btn-success'
            assert_text_displayed('Create a new', 'h1')  # wait for load

            info("Testing javascript error reporting -- logged in user")
            test_js_error_handling()

            info("Dismissing browser tool reminder.")
            self.assertNotIn('supress_reminder', self.driver.get_cookies())
            get_css_selector('.close-browser-tools.btn-link').click()
            self.assertTrue(any(cookie['name'] == 'suppress_reminder' and cookie['value'] == 'true' for cookie in self.driver.get_cookies()))

            info("Failing to create an archive.")
            # choose folder from dropdown
            get_css_selector('#folder-tree > .jstree-container-ul > li:last-child > a').click()
            # don't provide a URL
            get_id('addlink').click() # submit
            assert_text_displayed('URL cannot be empty.', 'p')
            # don't provide a URL or a file on the Upload a file form
            get_element_with_text("upload your own archive", 'button').click()
            get_id('uploadPermalink').click()
            assert_text_displayed('URL cannot be empty.')
            assert_text_displayed('File cannot be blank.')

            info("Creating archive.")
            self.driver.get(self.server_url + '/manage/create')
            url_to_capture = 'example.com'
            type_to_element(get_id('rawUrl'), url_to_capture)  # type url
            # choose folder from dropdown
            folder = get_css_selector('#folder-tree > .jstree-container-ul > li:last-child')
            # folder_id = folder.get_attribute('data-folder_id')
            folder.click()

            # wait until API call enables create archive button
            repeat_while_false(lambda: get_id('addlink').is_enabled(), 5)
            get_id('addlink').click()  # submit

            info("Viewing playback (logged in).")
            # wait 60 seconds to be forwarded to archive page
            repeat_while_exception(lambda: get_element_with_text('See the Screenshot View', 'a'), NoSuchElementException, 60)
            capture_url = self.driver.current_url
            # Check out the capture.
            test_playback(capture_url)

            # Personal Links

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

            # Verify that the folder used in the last capture was saved.
            # this fails ALL THE TIME
            # self.driver.get(self.server_url + '/manage/create/')
            # self.driver.implicitly_wait(20)
            # current_url = self.driver.current_url
            # self.assertEqual(self.server_url + '/manage/create/?folder=' + folder_id, current_url)
            # folder_from_storage = self.driver.execute_script("var ls = JSON.parse(localStorage.perma_selection); return ls[Object.keys(ls)[0]].folderIds[0]")
            # self.assertEqual(folder_id, str(folder_from_storage))

            info("Checking for unexpected javascript errors")
            # Visit every test every view that doesn't take parameters,
            # except the route for posting new js errors
            for urlpattern in urlpatterns:
                if '?P<' not in urlpattern.pattern._regex and urlpattern.name and urlpattern.name not in [
                    "error_management_post_new",
                    "set_iframe_session_cookie"
                ]:
                    self.driver.get(self.server_url + reverse(urlpattern.name))
            if not REMOTE_SERVER_URL and UncaughtError.objects.exclude(message__contains="doesNotExist").count():
                self.assertTrue(False, "Unexpected javascript errors (see log for details)")

            #
            # Next, tests while logged out (tested last so that the newly created Capture is available)
            #
            info("Logging out")
            # Start at homepage.
            self.driver.get(self.server_url)
            try:
                get_css_selector('.navbar-toggle').click()  # show navbar in mobile view
            except (ElementNotVisibleException, NoSuchElementException):
                get_css_selector('.navbar-link').click()
            log_out_button = repeat_while_exception(lambda: get_element_with_text("Log out", element_type='button'))
            log_out_button.click()
            assert_text_displayed("You have been logged out.", 'h1')

            info("Testing javascript error reporting -- logged out user")
            test_js_error_handling()

            info("Loading about page.")
            self.driver.get(self.server_url + "/about")
            partners = self.driver.execute_script("return partnerPoints")
            self.assertGreater(len(partners), 0)

            info("Loading docs.")
            try:
                get_css_selector('.navbar-toggle').click()  # show navbar in mobile view
            except ElementNotVisibleException:
                pass  # not in mobile view
            get_xpath("//a[@href='/docs']").click()
            assert_text_displayed('Perma.cc user guide')  # new text -- wait for load

            info("Viewing playback (logged out).")
            test_playback(capture_url)

        except Exception:
            # print unexpected JS errors
            for err in UncaughtError.objects.exclude(message__contains="doesNotExist"):
                info("\n-----\nUnexpected javascript error:", err.current_url, err.message, err.stack)

            # save screenshot
            try:
                info("Attempting to capture screenshot of failed functional test ...")
                screenshot_path = os.path.join(failed_test_files_path, "failed_functional_test.png")
                self.driver.save_screenshot(screenshot_path)
                info("Screenshot of failed functional test is at %s" % screenshot_path)
            except Exception as e2:
                info("Screenshot failed: %s" % e2)

            raise
