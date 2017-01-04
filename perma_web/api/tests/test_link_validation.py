# -*- coding: utf-8 -*-

import os
from .utils import TEST_ASSETS_DIR, ApiResourceTransactionTestCase
from api.resources import LinkResource
from perma.models import Link, LinkUser
from django.test.utils import override_settings


class LinkValidationTestCase(ApiResourceTransactionTestCase):

    resource = LinkResource
    rejected_status_code = 400  # Bad Request

    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/api_keys.json',
                'fixtures/archive.json']

    serve_files = ['target_capture_files/test.html',
                   'target_capture_files/test.jpg']

    def setUp(self):
        super(LinkValidationTestCase, self).setUp()

        self.admin_user = LinkUser.objects.get(pk=1)
        self.org_user = LinkUser.objects.get(pk=3)

        self.link = Link.objects.get(pk="3SLN-JHX9")
        self.unrelated_link = Link.objects.get(pk="7CF8-SS4G")

        self.list_url = "{0}/{1}/".format(self.url_base, LinkResource.Meta.resource_name)

        self.unrelated_url = "{0}{1}/".format(self.list_url, self.unrelated_link.pk)

    ########
    # URLs #
    ########
    def test_should_fail_gracefully_if_passed_long_unicode(self):
        '''
            See https://github.com/harvard-lil/perma/issues/1841
        '''
        u = u"This is a block of text that contains 64 or more characters, including one or more unicode characters like ☃"
        self.rejected_post(self.list_url,
                           user=self.org_user,
                           data={'url': u})

    @override_settings(BANNED_IP_RANGES=["0.0.0.0/8", "127.0.0.0/8"])
    def test_should_reject_invalid_ip(self):
        self.rejected_post(self.list_url,
                           user=self.org_user,
                           data={'url': self.server_url})

    def test_should_reject_malformed_url(self):
        self.rejected_post(self.list_url,
                           user=self.org_user,
                           data={'url': 'httpexamplecom'})

    def test_should_reject_unresolvable_domain_url(self):
        with self.header_timeout(0.25):  # only wait 1/4 second before giving up
            self.rejected_post(self.list_url,
                               user=self.org_user,
                               data={'url': 'http://this-is-not-a-functioning-url.com'})

    def test_should_reject_unloadable_url(self):
        self.rejected_post(self.list_url,
                           user=self.org_user,
                           # http://stackoverflow.com/a/10456069/313561
                           data={'url': 'http://0.42.42.42/'})

    @override_settings(MAX_ARCHIVE_FILE_SIZE=1024)
    def test_should_reject_large_url(self):
        self.rejected_post(self.list_url,
                           user=self.org_user,
                           data={'url': self.server_url + '/test.jpg'})

    #########
    # Files #
    #########

    def test_should_reject_invalid_file_format(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.html')) as test_file:
            self.rejected_post(self.list_url,
                               format='multipart',
                               user=self.org_user,
                               data={'url': self.server_url + '/test.html',
                                     'file': test_file})

    @override_settings(MAX_ARCHIVE_FILE_SIZE=1024)
    def test_should_reject_large_file(self):
        with open(os.path.join(TEST_ASSETS_DIR, 'target_capture_files', 'test.jpg')) as test_file:
            self.rejected_post(self.list_url,
                               format='multipart',
                               user=self.org_user,
                               data={'url': self.server_url + '/test.html',
                                     'file': test_file})
