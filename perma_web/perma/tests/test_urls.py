from django.urls import reverse

from perma.urls import urlpatterns
from .utils import PermaTestCase

class UrlsTestCase(PermaTestCase):

    def test_url_status_codes(self):
        """
        A really simple test for 500 errors. We test all views that don't
        take parameters (it's not easy to guess what params they want).
        """
        exclude = {
            'archive_error': 'because it returns 500 by default'
        }

        for urlpattern in urlpatterns:
            if '?P<' not in urlpattern.pattern._regex \
                     and urlpattern.name \
                     and urlpattern.name not in exclude:
                response = self.client.get(reverse(urlpattern.name))
                self.assertNotEqual(response.status_code, 500)

                response = self.client.post(reverse(urlpattern.name))
                self.assertNotEqual(response.status_code, 500)
