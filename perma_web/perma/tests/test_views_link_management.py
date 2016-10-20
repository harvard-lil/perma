# -*- coding: utf-8 -*-
from .utils import PermaTestCase

from bs4 import BeautifulSoup
from perma.views.link_management import Link

from mock import patch

# TODO: the template for displaying links/folders should probably be tested
# more thoroughly, since it includes a fair bit of logic

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
        self.assertIn("browser-tools-message", response)

    def test_no_reminder_when_refered_from_bookmarklet(self):
        response = self.get('create_link',
                             user = 'test_user@example.com',
                             request_kwargs={'data':{'url':'some-url-here'}}).content
        self.assertNotIn("browser-tools-message", response)

    def test_no_reminder_when_suppression_cookie_present(self):
        self.client.cookies.load({'suppress_reminder': 'true'})
        response = self.get('create_link',
                             user = 'test_user@example.com')
        self.assertNotIn("browser-tools-message", response)

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

    ### folder_contents function ###

    def test_folder(self):
        # with current fixures, expect 5
        response = self.get('folder_contents',
                             reverse_kwargs={'args':['25']},
                             user = 'test_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        links = soup.select('a.perma')
        self.assertEqual(len(links), 5)

    def test_folder_sort(self):
        # default sort = -creation_timestamp
        response = self.get('folder_contents',
                             reverse_kwargs={'args':['25']},
                             user = 'test_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        links = soup.select('a.perma')
        self.assertGreater(len(links), 1)
        first, last = links[0], links[-1]
        # get with reverse order
        response = self.get('folder_contents',
                             reverse_kwargs={'args':['25']},
                             request_kwargs={'data':{'sort':'creation_timestamp'}},
                             user = 'test_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        links = soup.select('a.perma')
        self.assertEqual(first, links[-1])
        self.assertEqual(last, links[0])
        # get with bogus sort, and it's the same as default
        response = self.get('folder_contents',
                             reverse_kwargs={'args':['25']},
                             request_kwargs={'data':{'sort':'bogus_sort'}},
                             user = 'test_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        links = soup.select('a.perma')
        self.assertEqual(first, links[0])
        self.assertEqual(last, links[-1])

    def test_folder_with_deleted(self):
        # with current fixtures, expect 6 in 30 (7th, deleted should not display)
        response = self.get('folder_contents',
                             reverse_kwargs={'args':['30']},
                             user = 'test_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        links = soup.select('a.perma')
        self.assertEqual(len(links), 6)

    def test_folder_with_revoked_access(self):
        # though Regular User (test_user@example.com) once
        # _created a link in 35, can't see it now
        self.get('folder_contents',
                  reverse_kwargs={'args':['35']},
                  user = 'test_user@example.com',
                  require_status_code = 404)

        # but an org user can
        response = self.get('folder_contents',
                             reverse_kwargs={'args':['35']},
                             user = 'test_org_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        links = soup.select('a.perma')
        self.assertEqual(len(links), 1)
        self.assertIn("Created by:</strong> Regular User", response)






