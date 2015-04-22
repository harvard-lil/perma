from __future__ import print_function

import socket
import StringIO
import imghdr
import os
import requests
import sys
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException, NoSuchElementException
import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from perma.wsgi import application as wsgi_app
from perma.settings import SAUCE_USERNAME, SAUCE_ACCESS_KEY

SERVER_DOMAIN = 'perma.dev'
RUN_LOCAL = os.environ.get('RUN_TESTS_LOCAL') == 'True'


assert socket.gethostbyname(SERVER_DOMAIN) in ('0.0.0.0', '127.0.0.1'), "Please add `127.0.0.1 " + SERVER_DOMAIN + "` to your hosts file before running this test."

# set up browsers
if RUN_LOCAL:
    browsers = ['Firefox']
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
def on_platforms(platforms, local):
    if local:
        def decorator(base_class):
            module = sys.modules[base_class.__module__].__dict__
            for i, platform in enumerate(platforms):
                d = dict(base_class.__dict__)
                d['browser'] = platform
                name = "%s_%s" % (base_class.__name__, i + 1)
                module[name] = type(name, (base_class,), d)
            pass
        return decorator

    def decorator(base_class):
        module = sys.modules[base_class.__module__].__dict__
        for i, platform in enumerate(platforms):
            d = dict(base_class.__dict__)
            d['desired_capabilities'] = platform
            name = "%s_%s" % (base_class.__name__, i + 1)
            module[name] = type(name, (base_class,), d)
    return decorator


# via: https://github.com/Victory/django-travis-saucelabs/blob/master/mysite/saucetests/tests.py
@on_platforms(browsers, RUN_LOCAL)
class FunctionalTest(StaticLiveServerTestCase):
    fixtures = ['fixtures/sites.json',
                'fixtures/users.json',
                'fixtures/folders.json']

    def setUp(self):
        # By default, the test server only mounts the django app,
        # which will leave out the warc app, so mount them both here
        self.server_thread.httpd.set_app(self.server_thread.static_handler(wsgi_app))
        self.server_thread.host = SERVER_DOMAIN

        if RUN_LOCAL:
            self.setUpLocal()
        else:
            self.setUpSauce()

    def tearDown(self):
        if RUN_LOCAL:
            self.tearDownLocal()
        else:
            self.tearDownSauce()

    def setUpSauce(self):
        self.desired_capabilities['name'] = self.id()

        sauce_url = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"
        self.driver = webdriver.Remote(
            desired_capabilities=self.desired_capabilities,
            command_executor=sauce_url % (SAUCE_USERNAME, SAUCE_ACCESS_KEY)
        )
        self.driver.implicitly_wait(5)

    def setUpLocal(self):
        self.driver = getattr(webdriver, self.browser)()
        self.driver.implicitly_wait(3)

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
            self.driver.find_element_by_link_text(link_text).click()

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

        def info(*args):
            if RUN_LOCAL:
                infoLocal(*args)
            else:
                infoSauce(*args)

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


        info("Loading homepage from %s." % self.live_server_url)
        self.driver.get(self.live_server_url)
        assert is_displayed(get_element_with_text("Websites Change"))

        info("Checking Perma In Action section.")
        get_xpath("//a[@data-img='MSC_1']").click()
        assert is_displayed(get_id('example-title'))
        get_xpath("//div[@id='example-image-wrapper']/img").click() # click on random element to trigger Sauce screenshot

        info("Loading docs.")
        get_xpath("//a[@href='/docs']").click()
        assert is_displayed(get_element_with_text('Overview', 'h2')) # wait for load

        info("Logging in.")
        click_link("Log in")
        assert "Email address" in get_xpath('//body').text
        get_id('id_username').send_keys('test_registrar_member@example.com')
        get_id('id_password').send_keys('pass')
        get_xpath("//button[@class='btn-success login']").click()
        assert is_displayed(get_element_with_text('Create a Perma archive', 'h3')) # wait for load

        info("Creating archive.")
        url_input = get_id('rawUrl') # type url
        url_input.click()
        url_input.send_keys("example.com")
        get_id('addlink').click() # submit
        thumbnail = repeat_while_exception(lambda: get_css_selector(".library-thumbnail img"), NoSuchElementException, timeout=15)
        thumbnail_data = requests.get(thumbnail.get_attribute('src'))
        thumbnail_fh = StringIO.StringIO(thumbnail_data.content)
        assert imghdr.what(thumbnail_fh) == 'png'
        # TODO: We could check the size of the generated png or the contents,
        # but note that the contents change between PhantomJS versions and OSes, so we'd need a fuzzy match

        info("Viewing playback.")
        archive_url = get_xpath("//a[@class='perma-url']").get_attribute('href') # get url from green button
        self.driver.get(archive_url)
        assert is_displayed(get_element_with_text('Live page view', 'a'))
        archive_view_link = get_id('warc_cap_container_complete')
        repeat_while_exception(lambda: archive_view_link.click(), ElementNotVisibleException) # wait for archiving to finish
        warc_url = self.driver.find_elements_by_tag_name("iframe")[0].get_attribute('src')
        self.driver.get(warc_url)
        assert is_displayed(get_element_with_text('This domain is established to be used for illustrative examples', 'p'))
