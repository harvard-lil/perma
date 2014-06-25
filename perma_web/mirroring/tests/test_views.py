from perma.tests.utils import PermaTestCase
from django.core.urlresolvers import reverse

class ServiceViewsTestCase(PermaTestCase):

    def test_link_assets(self):
        """Make sure we get a 404 for a non-existent archive"""

        response = self.client.post(reverse('mirroring:link_assets', kwargs={'guid': '9999-JCDL',}))
        self.assertEqual(response.status_code, 404)