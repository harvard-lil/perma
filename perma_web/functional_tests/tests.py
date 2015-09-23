from __future__ import print_function

import socket
import StringIO
import imghdr
import requests
import sys
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException, NoSuchElementException
import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings

from perma.wsgi import application as wsgi_app
from perma.settings import SAUCE_USERNAME, SAUCE_ACCESS_KEY, USE_SAUCE

SERVER_DOMAIN = 'perma.dev'


assert socket.gethostbyname(SERVER_DOMAIN) in ('0.0.0.0', '127.0.0.1'), "Please add `127.0.0.1 " + SERVER_DOMAIN + "` to your hosts file before running this test."

# set up browsers
if not USE_SAUCE:
    browsers = ['PhantomJS']
else:
    from sauceclient import SauceClient
    assert SAUCE_USERNAME and SAUCE_ACCESS_KEY, "Please make sure that SAUCE_USERNAME and SAUCE_ACCESS_KEY are set."
    sauce = SauceClient(SAUCE_USERNAME, SAUCE_ACCESS_KEY)
    
    # options: https://saucelabs.com/platforms
    browsers = [
        {"platform": "Mac OS X 10.9",
        "browserName": "chrome",
        "version": "31"},

        {"platform": "Windows 8.1",
        "browserName": "internet explorer",
        "version": "11"},

        {"platform": "Windows 7",
        "browserName": "firefox",
        "version": "30"},

        {"platform": "Windows XP",
        "browserName": "internet explorer",
        "version": "8"},

        {"platform": "OS X 10.9",
        "browserName": "iPhone",
        "version": "7.1",
        "device-orientation": "portrait",
        "nonSyntheticWebClick": False},
    ]

## helpers
def on_platforms(platforms, use_sauce):
    if use_sauce:
        def decorator(base_class):
            module = sys.modules[base_class.__module__].__dict__
            for i, platform in enumerate(platforms):
                d = dict(base_class.__dict__)
                d['desired_capabilities'] = platform
                name = "%s_%s" % (base_class.__name__, i + 1)
                module[name] = type(name, (base_class,), d)
        return decorator

    def decorator(base_class):
        module = sys.modules[base_class.__module__].__dict__
        for i, platform in enumerate(platforms):
            d = dict(base_class.__dict__)
            d['browser'] = platform
            name = "%s_%s" % (base_class.__name__, i + 1)
            module[name] = type(name, (base_class,), d)
        pass
    return decorator


# via: https://github.com/Victory/django-travis-saucelabs/blob/master/mysite/saucetests/tests.py
@on_platforms(browsers, USE_SAUCE)
class FunctionalTest(StaticLiveServerTestCase):
    fixtures = ['fixtures/sites.json',
                'fixtures/users.json',
                'fixtures/folders.json']

    base_desired_capabilities = {
        'loggingPrefs': {'browser': 'ALL'}
    }

    def setUp(self):
        # By default, the test server only mounts the django app,
        # which will leave out the warc app, so mount them both here
        self.server_thread.httpd.set_app(self.server_thread.static_handler(wsgi_app))
        self.server_thread.host = SERVER_DOMAIN

        if USE_SAUCE:
            self.setUpSauce()
        else:
            self.setUpLocal()

    def tearDown(self):
        if USE_SAUCE:
            self.tearDownSauce()
        else:
            self.tearDownLocal()

    def setUpSauce(self):
        desired_capabilities = dict(self.base_desired_capabilities, **self.base_desired_capabilities)
        desired_capabilities['name'] = self.id()

        sauce_url = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"
        self.driver = webdriver.Remote(
            desired_capabilities=desired_capabilities,
            command_executor=sauce_url % (SAUCE_USERNAME, SAUCE_ACCESS_KEY)
        )
        self.driver.implicitly_wait(5)
        socket.setdefaulttimeout(10)

    def setUpLocal(self):
        self.driver = getattr(webdriver, self.browser)(
            desired_capabilities=self.base_desired_capabilities,
        )
        self.driver.implicitly_wait(3)
        socket.setdefaulttimeout(10)
        self.driver.set_window_size(1024, 800)

    def tearDownLocal(self):
        self.driver.quit()

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

        def fix_host(url, host=settings.HOST):
            return url.replace('http://' + host, self.live_server_url)

        info("Loading homepage from %s." % self.live_server_url)
        self.driver.get(self.live_server_url)
        assert_text_displayed("Perma.cc prevents link rot.") # new text on landing now

        info("Checking Perma In Action section.")
        get_xpath("//a[@data-img='MSC_1']").click()
        self.assertTrue(is_displayed(get_id('example-title')))
        get_xpath("//div[@id='example-image-wrapper']/img").click()  # click on random element to trigger Sauce screenshot

        info("Loading docs.")
        get_xpath("//a[@href='/docs']").click()
        assert_text_displayed('Introducing Perma.cc', 'h2')  # new text -- wait for load

        info("Logging in.")
        try:
            get_css_selector('.navbar-toggle').click()  # show navbar in mobile view
        except ElementNotVisibleException:
            pass  # not in mobile view
        repeat_while_exception(lambda: click_link("Log in"))
        self.assertTrue("Email address" in get_xpath('//body').text)
        get_id('id_username').send_keys('test_registrar_member@example.com')
        get_id('id_password').send_keys('pass')
        get_xpath("//button[@class='btn btn-success login']").click() # new design button
        assert_text_displayed('Create a new Perma Link', 'h1')  # wait for load

        info("Creating archive.")
        url_to_capture = 'example.com'
        type_to_element(get_id('rawUrl'), url_to_capture)  # type url
        get_id('addlink').click() # submit
        thumbnail = repeat_while_exception(lambda: get_css_selector(".library-thumbnail img"), NoSuchElementException, timeout=60)
        # thumbnail_data = requests.get(thumbnail.get_attribute('src'))
        # thumbnail_fh = StringIO.StringIO(thumbnail_data.content)
        # self.assertEqual(imghdr.what(thumbnail_fh), 'png')
        # TODO: We could check the size of the generated png or the contents,
        # but note that the contents change between PhantomJS versions and OSes, so we'd need a fuzzy match

        info("Viewing playback.")
        display_archive_url = get_xpath("//a[@id='perma-success-url']").get_attribute('href')  # get url from green button
        archive_url = fix_host(display_archive_url)
        self.driver.get(archive_url)
        assert_text_displayed('See the Screenshot View', 'a')
        # archive_view_link = get_id('warc_cap_container_complete')
        # repeat_while_exception(lambda: archive_view_link.click(), ElementNotVisibleException) # wait for archiving to finish
        warc_url = fix_host(self.driver.find_elements_by_tag_name("iframe")[0].get_attribute('src'), settings.WARC_HOST)
        self.driver.get(warc_url)
        assert_text_displayed('This domain is established to be used for illustrative examples', 'p')

        # My Links

        # show links
        self.driver.get(self.live_server_url + '/manage/links')
        # create folder
        get_css_selector('.new-folder').click()
        # find link
        assert_text_displayed(display_archive_url)
        # show details
        get_css_selector('.link-expand').click()
        # for some reason these are throwing 500 errors on PATCH:
        # # change title
        # type_to_element(get_css_selector('input.link-title'), 'test')
        # repeat_while_exception(get_xpath("//span[contains(@class,'title-save-status') and contains(text(),'saved.')]"), NoSuchElementException)
        # # change notes
        # type_to_element(get_css_selector('input.link-notes'), 'test')
        # repeat_while_exception(get_xpath("//span[contains(@class,'notes-save-status') and contains(text(),'saved.')]"), NoSuchElementException)

        # Timemap

        info("Checking timemap.")
        self.driver.get(self.live_server_url + '/warc/pywb/*/' + url_to_capture)
        self.assertTrue(is_displayed(get_element_with_text('1', 'b')))  # the number of captures
        assert_text_displayed('http://' + url_to_capture, 'b')

        # Displays playback by timestamp
        get_xpath("//a[contains(@href, '%s')]" % url_to_capture).click()
        assert_text_displayed('This domain is established to be used for illustrative examples', 'p')
        playback_url = self.driver.current_url

