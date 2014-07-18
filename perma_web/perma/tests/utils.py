from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from perma.models import Registrar, VestingOrg


@override_settings(RUN_TASKS_ASYNC=False)
class PermaTestCase(TestCase):
    fixtures = ['fixtures/groups.json','fixtures/users.json',
                'fixtures/archive.json']

    def setUp(self):
        # create test registrar and vesting org
        # TODO: move these to fixtures
        registrar = Registrar(name='Test Registrar', email='registrar@test.com', website='http://testregistrar.com')
        registrar.save()
        VestingOrg(name='Test Vesting Org', registrar=registrar).save()

        # set default request domain -- needed for mirroring
        self.client.defaults['SERVER_NAME'] = 'perma.dev'

    def log_in_user(self, username, password='pass'):
        # TODO: check resp to see if login actually worked
        self.client.logout()
        return self.client.post(reverse('user_management_limited_login'), {'username': username, 'password': password})

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
        kwargs['request_kwargs'] = {'data':data}
        return self.do_request(view_name, 'post', *args, **kwargs)

    def post_form(self, view_name, data={}, *args, **kwargs):
        """
            Post to a view.
            success_url = url form should forward to after success
            success_query = query that should return one object if form worked
        """
        success_url = kwargs.pop('success_url', None)
        success_query = kwargs.pop('success_query', None)
        kwargs['require_status_code'] = None
        resp = self.post(view_name, data, *args, **kwargs)

        if success_url:
            def form_errors(resp):
                try:
                    return resp.context[1]['form']._errors
                except:
                    return '?'
            self.assertEqual(resp.status_code, 302,
                             "Form failed to forward to success url. Form errors: %s" % form_errors(resp))
            self.assertEqual(resp['Location'], "http://testserver"+success_url)

        if success_query:
            self.assertEqual(success_query.count(), 1)

    def use_main_server(self):
        """
            For mirroring, send requests through main server (e.g. dashboard.perma.dev)
        """
        self.client.defaults['SERVER_NAME'] = settings.MIRROR_USERS_SUBDOMAIN+'.perma.dev'

    def use_mirror_server(self):
        """
            For mirroring, send requests through mirror server (e.g. perma.dev)
        """
        self.client.defaults['SERVER_NAME'] = 'perma.dev'


