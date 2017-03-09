from django.test import override_settings
from django.test.client import RequestFactory

from perma.utils import *

from .utils import PermaTestCase

class UtilsTestCase(PermaTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(LIMIT_TO_TRUSTED_PROXY=True,
                   TRUSTED_PROXIES = ["10.0.2.2"],
                   TRUSTED_PROXY_HEADER = 'REMOTE_ADDR')
    def test_get_client_ip_wrong_proxy(self):
        request = self.factory.get('/some/route', REMOTE_ADDR="127.0.0.1")
        with self.assertRaises(PermissionDenied):
            get_client_ip(request)

    @override_settings(LIMIT_TO_TRUSTED_PROXY=True,
                   TRUSTED_PROXIES = ["10.0.2.2"],
                   TRUSTED_PROXY_HEADER = 'REMOTE_ADDR')
    def test_get_client_ip_right_proxy(self):
        request = self.factory.get('/some/route', REMOTE_ADDR="10.0.2.2")
        self.assertEqual(get_client_ip(request), "10.0.2.2")

    @override_settings(LIMIT_TO_TRUSTED_PROXY=True,
                   TRUSTED_PROXIES = ["10.0.2.2"],
                   TRUSTED_PROXY_HEADER = 'REMOTE_ADDR')
    def test_get_client_ip_wrong_header(self):
        request = self.factory.get('/some/route', HTTP_X_FORWARDED_FOR="10.0.2.2")
        with self.assertRaises(PermissionDenied):
            get_client_ip(request)

    @override_settings(LIMIT_TO_TRUSTED_PROXY=False,
                   TRUSTED_PROXIES = ["10.0.2.2"],
                   TRUSTED_PROXY_HEADER = 'REMOTE_ADDR')
    def test_get_client_ip_no_checking_remote_only(self):
        request = self.factory.get('/some/route', REMOTE_ADDR="127.0.0.1")
        self.assertEqual(get_client_ip(request), "127.0.0.1")

    @override_settings(LIMIT_TO_TRUSTED_PROXY=False,
                   TRUSTED_PROXIES = ["10.0.2.2"],
                   TRUSTED_PROXY_HEADER = 'REMOTE_ADDR')
    def test_get_client_ip_no_checking_xforwarded_only(self):
        request = self.factory.get('/some/route', HTTP_X_FORWARDED_FOR="127.0.0.1")
        self.assertEqual(get_client_ip(request), "127.0.0.1")

    @override_settings(LIMIT_TO_TRUSTED_PROXY=False,
                   TRUSTED_PROXIES = ["10.0.2.2"],
                   TRUSTED_PROXY_HEADER = 'REMOTE_ADDR')
    def test_get_client_ip_no_checking_xforwarded_prefered(self):
        request = self.factory.get('/some/route', HTTP_X_FORWARDED_FOR="10.0.2.2", REMOTE_ADDR="127.0.0.1")
        self.assertEqual(get_client_ip(request), "10.0.2.2")

