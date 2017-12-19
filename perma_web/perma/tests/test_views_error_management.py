from perma.models import UncaughtError
from .utils import PermaTestCase

class ErrorManagementViewsTestCase(PermaTestCase):
    error_contents = {
        'context': {
            'userAgent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0",
            'url': 'http://perma.test:8000/static/js/global.setup.js',
        },
        'errors': [
            {'backtrace': [
                {
                    'column': 5,
                    'file': 'http://perma.test:8000/static/js/global.setup.js',
                    'function': '',
                    'line': 11
                }, {
                    'column': 28285,
                    'file': 'http://perma.test:8000/static/vendors/jquery/jquery.js',
                    'function': 'b.event.dispatch',
                    'line': 3
                }, {
                    'column': 25025,
                    'file': 'http://perma.test:8000/static/vendors/jquery/jquery.js',
                    'function': 'b.event.add/v.handle',
                    'line': 3
                }],
                'message': 'TypeError: document.thisdoesnotexist is not a function',
                'type': 'TypeError'
            }
        ],
    }

    def test_post_new_with_user(self):
        user_email = 'test_user@example.com'
        response = self.post_json('error_management_post_new', self.error_contents, user=user_email)
        self.assertEqual(response.status_code, 200)

        # check created error
        latest_error = UncaughtError.objects.last()
        self.assertEqual(latest_error.current_url, self.error_contents['context']['url'])
        self.assertEqual(latest_error.user.email, user_email)

    def test_post_new_without_user(self):
        response = self.post_json('error_management_post_new', self.error_contents)
        self.assertEqual(response.status_code, 200)

        # check created error
        latest_error = UncaughtError.objects.last()
        self.assertEqual(latest_error.current_url, self.error_contents['context']['url'])

    def test_invalid_post(self):
        # if a post is sent without a valid json error report for some reason, just record user and referer
        user_email = 'test_user@example.com'
        referer_url = 'http://example.com'
        response = self.post_json('error_management_post_new', 'invalid json', user=user_email,
                                  request_kwargs={'HTTP_REFERER':referer_url})
        self.assertEqual(response.status_code, 200)

        # check created error
        latest_error = UncaughtError.objects.last()
        self.assertEqual(latest_error.current_url, referer_url)
        self.assertEqual(latest_error.user.email, user_email)

    def test_can_resolve_errors(self):
        admin_email = 'test_admin_user@example.com'

        # create error
        self.post_json('error_management_post_new', self.error_contents)
        latest_error = UncaughtError.objects.last()

        # resolve error
        response = self.post('error_management_resolve', {'error_id': latest_error.id}, user=admin_email)
        self.assertEqual(response.status_code, 200)

        # check error is resolved
        latest_error.refresh_from_db()
        self.assertTrue(latest_error.resolved)
        self.assertEqual(admin_email, latest_error.resolved_by_user.email)
