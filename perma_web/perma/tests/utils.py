import json
from django.test import TransactionTestCase
from django.core.urlresolvers import reverse

from perma.models import Registrar, VestingOrg, LinkUser


class PermaTestCase(TransactionTestCase):
    fixtures = ['fixtures/groups.json',
                'fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/archive.json']

    def setUp(self):
        # create test registrar and vesting org
        # TODO: move these to fixtures
        registrar = Registrar(name='Test Registrar', email='registrar@test.com', website='http://testregistrar.com')
        registrar.save()
        VestingOrg(name='Test Vesting Org', registrar=registrar).save()

    def log_in_user(self, username, password='pass'):
        # TODO: check resp to see if login actually worked
        self.client.logout()
        self.client.post(reverse('user_management_limited_login'), {'username': username, 'password': password})
        self.logged_in_user = LinkUser.objects.get(email=username)

    def do_request(self,
                   view_name,
                   method='get',
                   reverse_args=[],
                   reverse_kwargs={},
                   request_args=[],
                   request_kwargs={},
                   require_status_code=200):
        """
            Given view name, get url and fetch url contents.
        """
        url = reverse(view_name, *reverse_args, **reverse_kwargs)
        resp = getattr(self.client, method.lower())(url, *request_args, **request_kwargs)
        if require_status_code:
            self.assertEqual(resp.status_code, require_status_code)
        return resp

    def get(self, view_name, *args, **kwargs):
        """
            Convenience method to call do_request with method='get'
        """
        return self.do_request(view_name, 'get', *args, **kwargs)

    def post(self, view_name, data={}, *args, **kwargs):
        """
            Convenience method to call do_request with method='post'
        """
        kwargs['request_kwargs'] = {'data': data}
        return self.do_request(view_name, 'post', *args, **kwargs)

    def post_json(self, view_name, data={}, *args, **kwargs):
        """
            Convenience method to call do_request with necessary headers for JSON requests.
        """
        kwargs['request_kwargs'] = {'data': json.dumps(data),
                                    'content_type': 'application/x-www-form-urlencoded',
                                    'HTTP_X_REQUESTED_WITH':'XMLHttpRequest'}
        return self.do_request(view_name, 'post', *args, **kwargs)


    def submit_form(self, view_name, data={}, *args, **kwargs):
        """
            Post to a view.
            success_url = url form should forward to after success
            success_query = query that should return one object if form worked
        """
        success_url = kwargs.pop('success_url', None)
        success_query = kwargs.pop('success_query', None)
        form_key = kwargs.pop('form_key', 'form')           # name of form object in RequestContext returned with response
        error_keys = set(kwargs.pop('error_keys', []))      # keys that must appear in form error list

        kwargs['require_status_code'] = None
        resp = self.post(view_name, data, *args, **kwargs)

        def form_errors():
            try:
                return resp.context[form_key]._errors
            except:
                return {}

        if success_url:
            self.assertEqual(resp.status_code, 302,
                             "Form failed to forward to success url. Status: %s. Content: %s. Errors: %s." % (resp.status_code, resp.content, form_errors()))
            self.assertTrue(resp['Location'].endswith(success_url), "Form failed to forward to %s. Instead forwarded to: %s." % (success_url, resp['Location']))

        if success_query:
            self.assertEqual(success_query.count(), 1)

        if error_keys:
            self.assertTrue(error_keys <= set(form_errors().keys()), "Couldn't find expected error keys. Expected: %s. Found: %s" % (error_keys, form_errors()))

        return resp
