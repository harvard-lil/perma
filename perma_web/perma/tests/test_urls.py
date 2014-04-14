from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from perma.urls import urlpatterns

class UrlsTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        
    def test_url_status_codes(self):
        """
        A really simple test for 500 errors. We test all views that don't
        take parameters (it's not easy to guess what params they want).
        """
        
        for urlpattern in urlpatterns:
            if '?P<' not in urlpattern.regex.pattern and urlpattern.name:
                response = self.client.get(reverse(urlpattern.name))
                self.assertNotEqual(response.status_code, 500)
                
                response = self.client.post(reverse(urlpattern.name))
                self.assertNotEqual(response.status_code, 500)