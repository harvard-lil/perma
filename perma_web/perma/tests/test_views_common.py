from perma.urls import urlpatterns

from .utils import PermaTestCase
from django.core.urlresolvers import reverse

class CommonViewsTestCase(PermaTestCase):

    def test_public_views(self):
        # test static template views
        for urlpattern in urlpatterns:
            if urlpattern.callback.func_name == 'DirectTemplateView':
                resp = self.get(urlpattern.name)

    def test_single_link_guid(self):
        # We try to help the user by translating separation chars into hyphens
        # For example, JJJJ--JJJJ gets redirected to JJJJ-JJJJ

        response = self.client.get(reverse('single_linky', kwargs={'guid': 'JJ99--JJJJ'}))
        self.assertRedirects(response,
            reverse('single_linky', kwargs={'guid': 'JJJJ-JJJJ'}), status_code=301,
            target_status_code=404)

        # Insane IDs should redirect if they have non-hyphens
        response = self.client.get(reverse('single_linky', kwargs={'guid': '988-JJJJ=JJJJ'}))
        self.assertRedirects(response,
            reverse('single_linky', kwargs={'guid': '988-JJJJ-JJJJ'}), status_code=301,
            target_status_code=404)

        # This identifier is legit. We shouldn't get redirected, just 404.
        response = self.client.get(reverse('single_linky', kwargs={'guid': 'JJ99-JJJJ'}))
        self.assertEqual(response.status_code, 404)

        # Test the original ID style. We shouldn't get a rediect.
        response = self.client.get(reverse('single_linky', kwargs={'guid': '0J6pkzDeQwT'}))
        self.assertEqual(response.status_code, 404)