import os
from .utils import ApiResourceTestCase, TEST_ASSETS_DIR
from api.resources import LinkResource
from perma import models
from perma.models import Link, LinkUser
from django.test.utils import override_settings


class LinkValidationsTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/api_keys.json',
                'fixtures/archive.json']

    serve_files = [os.path.join(TEST_ASSETS_DIR, 'target_capture_files/test.html'),
                   os.path.join(TEST_ASSETS_DIR, 'target_capture_files/test.jpg')]

    def setUp(self):
        super(LinkValidationsTestCase, self).setUp()

        self.user = LinkUser.objects.get(email='test_vesting_member@example.com')

        self.vested_link = Link.objects.get(pk="3SLN-JHX9")
        self.unvested_link = Link.objects.get(pk="7CF8-SS4G")

        self.list_url = "{0}/{1}/".format(self.url_base, LinkResource.Meta.resource_name)

        self.vested_url = "{0}{1}/".format(self.list_url, self.vested_link.pk)
        self.unvested_url = "{0}{1}/".format(self.list_url, self.unvested_link.pk)

    def get_credentials(self, user=None):
        user = user or self.user
        return self.create_apikey(username=user.email, api_key=user.api_key.key)

    ########
    # URLs #
    ########

    @override_settings(BANNED_IP_RANGES=["0.0.0.0/8", "127.0.0.0/8"])
    def test_should_reject_invalid_ip(self):
        count = Link.objects.count()
        self.assertHttpBadRequest(
            self.api_client.post(self.list_url,
                                 format='json',
                                 data={'url': self.server_url},
                                 authentication=self.get_credentials()))

        self.assertEqual(Link.objects.count(), count)

    def test_should_reject_malformed_url(self):
        count = Link.objects.count()
        self.assertHttpBadRequest(
            self.api_client.post(self.list_url,
                                 format='json',
                                 data={'url': 'httpexamplecom'},
                                 authentication=self.get_credentials()))

        self.assertEqual(Link.objects.count(), count)

    def test_should_reject_unresolvable_domain_url(self):
        models.HEADER_CHECK_TIMEOUT = 1  # only wait 1 second before giving up
        count = Link.objects.count()
        self.assertHttpBadRequest(
            self.api_client.post(self.list_url,
                                 format='json',
                                 data={'url': 'http://this-is-not-a-functioning-url.com'},
                                 authentication=self.get_credentials()))

        self.assertEqual(Link.objects.count(), count)

    def test_should_reject_unloadable_url(self):
        count = Link.objects.count()
        self.assertHttpBadRequest(
            self.api_client.post(self.list_url,
                                 format='json',
                                 data={'url': 'http://192.0.2.1/'},
                                 authentication=self.get_credentials()))

        self.assertEqual(Link.objects.count(), count)

    @override_settings(MAX_HTTP_FETCH_SIZE=1024)
    def test_should_reject_large_url(self):
        count = Link.objects.count()
        self.assertHttpBadRequest(
            self.api_client.post(self.list_url,
                                 format='json',
                                 data={'url': self.server_url + '/test.jpg'},
                                 authentication=self.get_credentials()))

        self.assertEqual(Link.objects.count(), count)

    #########
    # Files #
    #########

    def test_should_reject_invalid_file_format(self):
        count = Link.objects.count()
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.html')) as test_file:
            self.assertHttpBadRequest(
                self.api_client.post(self.list_url,
                                     format='multipart',
                                     data={'url': self.server_url + '/test.html',
                                           'file': test_file},
                                     authentication=self.get_credentials()))

            self.assertEqual(Link.objects.count(), count)

    @override_settings(MAX_ARCHIVE_FILE_SIZE=1024)
    def test_should_reject_large_file(self):
        count = Link.objects.count()
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.jpg')) as test_file:
            self.assertHttpBadRequest(
                self.api_client.post(self.list_url,
                                     format='multipart',
                                     data={'url': self.server_url + '/test.html',
                                           'file': test_file},
                                     authentication=self.get_credentials()))

            self.assertEqual(Link.objects.count(), count)

    ###################
    # Required Fields #
    ###################

    def test_should_reject_vest_when_missing_vesting_org(self):
        old_data = self.deserialize(self.api_client.get(self.unvested_url, format='json'))
        new_data = old_data.copy()
        new_data.update({'vested': True})

        count = Link.objects.count()
        self.assertHttpBadRequest(
            self.api_client.patch(self.unvested_url,
                                  format='json',
                                  data=new_data,
                                  authentication=self.get_credentials(self.unvested_link.created_by)))

        self.assertEqual(Link.objects.count(), count)
        self.assertEqual(
            self.deserialize(self.api_client.get(self.unvested_url, format='json')),
            old_data)
