import requests
from importlib import reload

from django.test import LiveServerTestCase

import perma.settings
import perma.wsgi


class WsgiTestCase(LiveServerTestCase):

    def setUp(self):
        # Set custom settings and reload wsgi app.
        # We have to override settings in this weird way -- by monkeypatching perma.settings and reloading wsgi.py --
        # because wsgi.py is designed to run before django is loaded.
        self.orig_TRUSTED_PROXIES = perma.settings.TRUSTED_PROXIES
        perma.settings.TRUSTED_PROXIES = [["1.2.0.0/16", "3.4.0.0/16"],["127.0.0.1"]]
        reload(perma.wsgi)

        # use full wsgi app in test server
        self.server_thread.httpd.set_app(self.server_thread.static_handler(perma.wsgi.application))

    def tearDown(self):
        # Make sure we leave everything like we found it.
        perma.settings.TRUSTED_PROXIES = self.orig_TRUSTED_PROXIES
        reload(perma.wsgi)

    def test_get_client_ip_no_proxy(self):
        # No X-Forwarded-For header:
        response = requests.get(self.live_server_url)
        self.assertEqual(response.status_code, 400)

    def test_get_client_ip_short_proxy(self):
        # Incomplete proxy chain:
        response = requests.get(self.live_server_url, headers={
            'X-Forwarded-For': '1.1.1.1'  #<client IP>
        })
        self.assertEqual(response.status_code, 400)

    def test_get_client_ip_wrong_proxy(self):
        # Complete proxy chain, but proxy is wrong:
        response = requests.get(self.live_server_url, headers={
            'X-Forwarded-For': '1.1.1.1,8.8.8.8'  #<client IP>,<wrong IP>
        })
        self.assertEqual(response.status_code, 400)

    def test_get_client_ip_right_proxy(self):
        # Valid proxy chain:
        response = requests.get(self.live_server_url+'/tests/client_ip', headers={
            'X-Forwarded-For': '1.1.1.1,1.2.3.4'  #<client IP>,<right IP>
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, '1.1.1.1')
