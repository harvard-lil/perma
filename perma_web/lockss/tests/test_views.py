from django.test import Client
from perma.tests.utils import PermaTestCase


class LockssTestCase(PermaTestCase):

    def setUp(self):
        self.clients = []
        for (ip, status_code) in [('203.0.113.3', 200), ('203.0.113.4', 403)]:
            self.clients.append((Client(REMOTE_ADDR=ip), status_code))

    def test_daemon_settings(self):
        for (client, status_code) in self.clients:
            response = client.get('/lockss/daemon_settings.txt')
            self.assertEqual(response.status_code, status_code)

    def test_titledb_and_search(self):
        response = self.clients[0][0].get('/lockss/titledb.xml')
        self.assertEqual(response.status_code, self.clients[0][1])
        for ym in [ym[0:7] for ym in str(response.content, 'utf-8').split('Perma.cc Captures For ')][1:]:
            (year, month) = ym.split('-')
            for (client, status_code) in self.clients:
                response = client.get('/lockss/search/?creation_year={0}&creation_month={1}'.format(year, month))
                self.assertEqual(response.status_code, status_code)
        response = self.clients[1][0].get('/lockss/titledb.xml')
        self.assertEqual(response.status_code, self.clients[1][1])

    def test_permission(self):
        for (client, status_code) in self.clients:
            response = client.get('/lockss/permission/')
            self.assertEqual(response.status_code, status_code)

    def test_fetch(self):
        for (client, status_code) in self.clients:
            response = client.get('/lockss/fetch/3S/LN/JH/3SLN-JHX9.warc.gz')
            self.assertEqual(response.status_code, status_code)
