from django.test.client import RequestFactory

from perma.utils import *

from .utils import PermaTestCase

class UtilsTestCase(PermaTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_client_ip(self):
        request = self.factory.get('/some/route', REMOTE_ADDR="1.2.3.4")
        self.assertEqual(get_client_ip(request), "1.2.3.4")