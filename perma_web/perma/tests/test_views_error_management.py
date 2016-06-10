from django.core.urlresolvers import reverse

from .utils import PermaTestCase

class ErrorManagementViewsTestCase(PermaTestCase):
    def test_post_new_with_user(self):
        error_contents = {
            'context': {
                'userAgent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0",
                'url': 'http://perma.dev:8000/static/js/global.setup.js',
            },
            'errors': [
                {'backtrace': [
                    {
                        'column': 5,
                        'file': 'http://perma.dev:8000/static/js/global.setup.js',
                        'function': '',
                        'line': 11
                    }, {
                        'column': 28285,
                        'file': 'http://perma.dev:8000/static/vendors/jquery/jquery.js',
                        'function': 'b.event.dispatch',
                        'line': 3
                    }, {
                        'column': 25025,
                        'file': 'http://perma.dev:8000/static/vendors/jquery/jquery.js',
                        'function': 'b.event.add/v.handle',
                        'line': 3
                    }],
                    'message': 'TypeError: document.thisdoesnotexist is not a function',
                    'type': 'TypeError'
                }
            ],
        }



        response = self.client.post(reverse('error_management_post_new'), error_contents)
        self.assertEqual(response.status_code, 200)

        # testing that we're creating error on post
        # latest_error = UncaughtError.objects.all()[0]
        # self.assertEqual(latest_error.current_url, error_contents['current_url'])

    def test_post_new_without_user(self):
        self.client.post(reverse('logout'))

        error_contents = {
            'context': {
                'userAgent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0",
                'url': 'http://perma.dev:8000/static/js/global.setup.js',
            },
            'errors': [
                {'backtrace': [
                    {
                        'column': 5,
                        'file': 'http://perma.dev:8000/static/js/global.setup.js',
                        'function': '',
                        'line': 11
                    }, {
                        'column': 28285,
                        'file': 'http://perma.dev:8000/static/vendors/jquery/jquery.js',
                        'function': 'b.event.dispatch',
                        'line': 3
                    }, {
                        'column': 25025,
                        'file': 'http://perma.dev:8000/static/vendors/jquery/jquery.js',
                        'function': 'b.event.add/v.handle',
                        'line': 3
                    }],
                    'message': 'TypeError: document.thisdoesnotexist is not a function',
                    'type': 'TypeError'
                }
            ],
        }
        response = self.client.post(reverse('error_management_post_new'), error_contents)
        self.assertEqual(response.status_code, 200)
        # latest_error = UncaughtError.objects.all()[0]
        # self.assertEqual(latest_error.current_url, error_contents['current_url'])
