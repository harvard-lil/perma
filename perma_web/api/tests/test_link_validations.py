import os
from .utils import ApiResourceTestCase, TEST_ASSETS_DIR
from api.resources import LinkResource
from perma.models import Link, LinkUser
from django.test.utils import override_settings


class LinkValidationsTestCase(ApiResourceTestCase):

    resource = LinkResource
    assertHttpRejected = ApiResourceTestCase.assertHttpBadRequest

    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/groups.json',
                'fixtures/api_keys.json',
                'fixtures/archive.json']

    serve_files = [os.path.join(TEST_ASSETS_DIR, 'target_capture_files/test.html'),
                   os.path.join(TEST_ASSETS_DIR, 'target_capture_files/test.jpg')]

    def setUp(self):
        super(LinkValidationsTestCase, self).setUp()

        self.registry_member = LinkUser.objects.get(pk=1)
        self.vesting_member = LinkUser.objects.get(pk=3)

        self.vested_link = Link.objects.get(pk="3SLN-JHX9")
        self.unvested_link = Link.objects.get(pk="7CF8-SS4G")

        self.list_url = "{0}/{1}/".format(self.url_base, LinkResource.Meta.resource_name)

        self.vested_url = "{0}{1}/".format(self.list_url, self.vested_link.pk)
        self.unvested_url = "{0}{1}/".format(self.list_url, self.unvested_link.pk)

    ########
    # URLs #
    ########

    @override_settings(BANNED_IP_RANGES=["0.0.0.0/8", "127.0.0.0/8"])
    def test_should_reject_invalid_ip(self):
        self.rejected_post(self.list_url,
                           user=self.vesting_member,
                           data={'url': self.server_url})

    def test_should_reject_malformed_url(self):
        self.rejected_post(self.list_url,
                           user=self.vesting_member,
                           data={'url': 'httpexamplecom'})

    def test_should_reject_unresolvable_domain_url(self):
        with self.header_timeout(0.25):  # only wait 1/4 second before giving up
            self.rejected_post(self.list_url,
                               user=self.vesting_member,
                               data={'url': 'http://this-is-not-a-functioning-url.com'})

    def test_should_reject_unloadable_url(self):
        self.rejected_post(self.list_url,
                           user=self.vesting_member,
                           # http://stackoverflow.com/a/10456069/313561
                           data={'url': 'http://0.42.42.42/'})

    @override_settings(MAX_HTTP_FETCH_SIZE=1024)
    def test_should_reject_large_url(self):
        self.rejected_post(self.list_url,
                           user=self.vesting_member,
                           data={'url': self.server_url + '/test.jpg'})

    #########
    # Files #
    #########

    def test_should_reject_invalid_file_format(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.html')) as test_file:
            self.rejected_post(self.list_url,
                               format='multipart',
                               user=self.vesting_member,
                               data={'url': self.server_url + '/test.html',
                                     'file': test_file})

    @override_settings(MAX_ARCHIVE_FILE_SIZE=1024)
    def test_should_reject_large_file(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.jpg')) as test_file:
            self.rejected_post(self.list_url,
                               format='multipart',
                               user=self.vesting_member,
                               data={'url': self.server_url + '/test.html',
                                     'file': test_file})

    ###################
    # Required Fields #
    ###################

    def test_should_reject_vest_when_vesting_org_not_found(self):
        self.rejected_patch(self.unvested_url,
                            user=self.vesting_member,
                            data={'vested': True,
                                  'vesting_org': 999,
                                  'folder': 27})

    def test_should_reject_vest_when_missing_folder(self):
        self.rejected_patch(self.unvested_url,
                            user=self.unvested_link.created_by,
                            data={'vested': True,
                                  'vesting_org': 1})

    def test_should_reject_vest_when_folder_doesnt_belong_to_vesting_org(self):
        self.rejected_patch(self.unvested_url,
                            user=self.unvested_link.created_by,
                            data={'vested': True,
                                  'vesting_org': 1,
                                  'folder': 28})
