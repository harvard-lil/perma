import unittest
from django.core.urlresolvers import reverse
from django.utils import timezone
from perma.models import UncaughtError
from django.test import Client
# from .utils import PermaTestCase


class ErrorManagementViewsTestCase(unittest.TestCase):
    def test_post_new(self):
        c = Client()
        error_obj = {
            'current_url' : '/test/url/',
            'stack': 'Error: hello at Object.ErrorHandler.notify () at Object.ls.getCurrent ()',
            'custom_message': 'Uncaught exception',
            'name':'Fake error',
            'message':'This is an error test',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
        }

        response = c.post('/errors/new', error_obj)
        self.assertEqual(response.status_code, 200)

        # testing that we're creating error on post
        latest_error = UncaughtError.objects.all()[0]
        self.assertEqual(latest_error.current_url, error_obj['current_url'])
        self.assertEqual(latest_error.name, error_obj['name'])
