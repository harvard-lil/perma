from django.test import Client
from perma.tests.utils import PermaTestCase


class LockssTestCase(PermaTestCase):

    def setUp(self):
        c = Client(REMOTE_ADDR='203.0.113.3')
        self.client = c

    def test_daemon_settings(self):
        response = self.client.get('/lockss/daemon_settings.txt')
        self.assertEqual(response.status_code, 200)

    def test_titledb_and_search(self):
        response = self.client.get('/lockss/titledb.xml')
        self.assertEqual(response.status_code, 200)
        for ym in [ym[0:7] for ym in response.content.split('Perma.cc Captures For ')][1:]:
            (year, month) = ym.split('-')
            response = self.client.get('/lockss/search/?creation_year={0}&creation_month={1}'.format(year, month))
            self.assertEqual(response.status_code, 200)

    def test_permission(self):
        response = self.client.get('/lockss/permission/')
        self.assertEqual(response.status_code, 200)

    def test_fetch(self):
        response = self.client.get('/lockss/fetch/3S/LN/JH/3SLN-JHX9.warc.gz')
        self.assertEqual(response.status_code, 200)
