import unittest
from django.core.urlresolvers import reverse
from perma.models import UncaughtError
from perma.models import LinkUser

from .utils import PermaTestCase

class ErrorManagementViewsTestCase(PermaTestCase):
    def test_post_new_with_user(self):
        self.client.post(reverse('user_management_limited_login'),
            {'username':'test_user@example.com', 'password':'pass'})

        error_contents = {
            'current_url' : '/test/url/',
            'stack': 'Error: hello at Object.ErrorHandler.notify () at Object.ls.getCurrent ()',
            'custom_message': 'Uncaught exception',
            'name':'Fake error',
            'message':'This is an error test',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
        }

        response = self.client.post(reverse('error_management_post_new'), error_contents)
        self.assertEqual(response.status_code, 200)

        # testing that we're creating error on post
        latest_error = UncaughtError.objects.all()[0]
        self.assertEqual(latest_error.current_url, error_contents['current_url'])
        self.assertEqual(latest_error.name, error_contents['name'])

    def test_post_new_without_user(self):
        self.client.post(reverse('logout'))

        error_contents = {
            'current_url' : '/test/other/url/',
            'stack': 'Error: oh no! at Object.ErrorHandler.notify () at Object.ls.getCurrent ()',
            'custom_message': 'Uncaught exception',
            'name':'Another fake error',
            'message':'This is an error test',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
        }

        response = self.client.post(reverse('error_management_post_new'), error_contents)
        self.assertEqual(response.status_code, 200)
        latest_error = UncaughtError.objects.all()[0]
        self.assertEqual(latest_error.current_url, error_contents['current_url'])
        self.assertEqual(latest_error.name, error_contents['name'])
