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

        response = self.client.get(reverse('single_link_header', kwargs={'guid': 'JJ99--JJJJ'}))
        self.assertRedirects(response,
            reverse('single_link_header', kwargs={'guid': 'JJ99-JJJJ'}), status_code=301,
            target_status_code=404)

        # Insane IDs should redirect if they have non-hyphens
        response = self.client.get(reverse('single_link_header', kwargs={'guid': '988-JJJJ=JJJJ'}))
        self.assertRedirects(response,
            reverse('single_link_header', kwargs={'guid': '988-JJJJ-JJJJ'}), status_code=301,
            target_status_code=404)

        # This identifier is legit. We shouldn't get redirected, just 404.
        response = self.client.get(reverse('single_link_header', kwargs={'guid': 'JJ99-JJJJ'}))
        self.assertEqual(response.status_code, 404)

        # Test the original ID style. We shouldn't get a rediect.
        response = self.client.get(reverse('single_link_header', kwargs={'guid': '0J6pkzDeQwT'}))
        self.assertEqual(response.status_code, 404)


    def test_contact(self):
        # Does our contact form behave reasonably?

        # The form should be fine will all fields
        self.submit_form('contact', data={
                            'email': 'example@example.com',
                            'message': 'Just some message here'},
                       success_url=reverse('contact_thanks'))

        # We should fail if we don't get an email
        response = self.client.post(reverse('contact'), data={
                            'email': '',
                            'message': 'some message here'})
        self.assertEqual(response.request['PATH_INFO'], reverse('contact'))

        # We need at least a message. We should get the contact page back
        # instead of the thanks page.
        response = self.client.post(reverse('contact'), data={
                            'email': '',
                            'message': ''})
        self.assertEqual(response.request['PATH_INFO'], reverse('contact'))