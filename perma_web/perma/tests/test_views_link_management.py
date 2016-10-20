# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core import mail
from django.conf import settings

from .utils import PermaTestCase

from random import random
from bs4 import BeautifulSoup


class LinkManagementViewsTestCase(PermaTestCase):

    ### /manage/create ###

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

