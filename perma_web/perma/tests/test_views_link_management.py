# -*- coding: utf-8 -*-
from mock import patch

from .utils import PermaTestCase

from perma.views.link_management import Link


class LinkManagementViewsTestCase(PermaTestCase):

    ### create_link function ###

    def test_display_after_delete_real_link(self):
        response = self.get('create_link',
                             user= 'test_user@example.com',
                             request_kwargs={'data':{'deleted':'ABCD-0003'}})
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Deleted - Wikipedia")

    def test_display_after_delete_fake_link(self):
        response = self.get('create_link',
                             user = 'test_user@example.com',
                             request_kwargs={'data':{'deleted':'ZZZZ-ZZZZ'}})
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)

    def test_reminder(self):
        response = self.get('create_link',
                             user = 'test_user@example.com').content
        self.assertIn(b"browser-tools-message", response)

    def test_no_reminder_when_refered_from_bookmarklet(self):
        response = self.get('create_link',
                             user = 'test_user@example.com',
                             request_kwargs={'data':{'url':'some-url-here'}}).content
        self.assertNotIn(b"browser-tools-message", response)

    def test_no_reminder_when_suppression_cookie_present(self):
        self.client.cookies.load({'suppress_reminder': 'true'})
        response = self.get('create_link',
                             user = 'test_user@example.com')
        self.assertNotIn(b"browser-tools-message", response)

    ### user_delete_link function ###

    def test_confirm_delete_unpermitted_link(self):
        self.get('user_delete_link',
                  reverse_kwargs={'args':['7CF8-SS4G']},
                  user = 'test_user@example.com',
                  require_status_code = 404)

    def test_confirm_delete_nonexistent_link(self):
        self.get('user_delete_link',
                  reverse_kwargs={'args':['ZZZZ-ZZZZ']},
                  user = 'test_user@example.com',
                  require_status_code = 404)

    # only brand new links can be deleted (they aren't "archive eligible"),
    # so we have to mock Link.is_archive_eligible to always return false
    @patch.object(Link, 'is_archive_eligible', lambda x: False)
    def test_confirm_delete_permitted_link(self):
        self.get('user_delete_link',
                  reverse_kwargs={'args':['JJ3S-2Q5N']},
                  user = 'test_user@example.com')






