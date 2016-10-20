# -*- coding: utf-8 -*-

from perma.templatetags.repeat import repeat

from .utils import PermaTestCase

class TemplateTagsTestCase(PermaTestCase):

    def test_repeat(self):
        self.assertEqual(repeat('', 0), '')
        self.assertEqual(repeat('hodor', 0), '')
        self.assertEqual(repeat('hodor', 1), 'hodor')
        self.assertEqual(repeat('hodor', 5), 'hodorhodorhodorhodorhodor')


