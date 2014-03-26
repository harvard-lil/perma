from django.core.urlresolvers import reverse

from perma.models import *
from perma.urls import urlpatterns

from .utils import PermaTestCase


class PermissionsTestCase(PermaTestCase):

    def test_permissions(self):
        """Test who can log into restricted pages."""
        all_users = {
            'test_registry_member@example.com',
            'test_registrar_member@example.com',
            'test_vesting_member@example.com',
            'test_user@example.com',
            'test_vesting_manager@example.com'
        }
        views = [
            {
                'urls': [
                    ['user_management_manage_registrar'],
                    ['user_management_manage_single_registrar', {'kwargs':{'registrar_id': 1}}],
                    ['user_management_manage_registrar_member'],
                    ['user_management_manage_single_registrar_member', {'kwargs':{'user_id': 2}}],
                    ['user_management_manage_single_registrar_member_delete', {'kwargs':{'user_id': 2}}],
                    ['user_management_manage_single_registrar_member_reactivate', {'kwargs':{'user_id': 2}}],
                    ['user_management_manage_user'],
                    ['user_management_user_add_registrar', {'kwargs': {'user_id': 4}}],
                    ['user_management_user_add_vesting_org', {'kwargs': {'user_id': 4}}],
                    ['user_management_manage_single_user', {'kwargs':{'user_id': 4}}],
                    ['user_management_manage_single_user_delete', {'kwargs':{'user_id': 4}}],
                    ['user_management_manage_single_user_reactivate', {'kwargs':{'user_id': 4}}],
                    ['dark_archive_link', {'kwargs': {'guid': '1234'}, 'success_status': 404}],
                ],
                'allowed': {'test_registry_member@example.com'},
            },
            {
                'urls': [
                    ['user_management_manage_vesting_manager'],
                    ['user_management_manage_vesting_org'],
                    ['user_management_manage_single_vesting_org', {'kwargs':{'vesting_org_id':1}}],
                    ['user_management_manage_single_vesting_manager', {'kwargs':{'user_id': 5}}],
                    ['user_management_manage_single_vesting_manager_delete', {'kwargs':{'user_id': 5}}],
                    ['user_management_manage_single_vesting_manager_reactivate', {'kwargs':{'user_id': 5}}],
                ],
                'allowed': {'test_registry_member@example.com', 'test_registrar_member@example.com'},
            },
            {
                'urls': [
                    ['user_management_manage_vesting_member'],
                    ['user_management_manage_single_vesting_member', {'kwargs':{'user_id': 3}}],
                    ['user_management_manage_single_vesting_member_delete', {'kwargs':{'user_id': 3}}],
                    ['user_management_manage_single_vesting_member_reactivate', {'kwargs':{'user_id': 3}}],
                ],
                'allowed': {'test_registry_member@example.com', 'test_registrar_member@example.com',
                            'test_vesting_manager@example.com'}
            },
            {
                'urls': [
                    ['vested_links'],
                    ['vest_link', {'kwargs':{'guid':'1234'},'success_status':404}],
                ],
                'allowed': {'test_registry_member@example.com', 'test_registrar_member@example.com',
                            'test_vesting_manager@example.com', 'test_vesting_member@example.com'}
            },
            {
                'urls': [
                    ['user_management_manage_account'],
                    ['create_link'],
                    ['upload_link', {'success_status':400}],
                    ['created_links'],
                ],
                'allowed': {'test_user@example.com'},
                'disallowed': set(),
            },
        ]

        views_tested = set()
        for view in views:
            for url in view['urls']:
                view_name = url[0]
                opts = url[1] if len(url)>1 else {}
                views_tested.add(view_name)
                url = reverse(view_name, kwargs=opts.get('kwargs', None))
                success_status = opts.get('success_status', 200)
                success_test = opts.get('success_test', None)

                # try while logged out
                self.client.logout()
                resp = self.client.get(url)
                self.assertRedirects(resp, settings.LOGIN_URL+"?next="+url)

                # try with valid users
                for user in view['allowed']:
                    self.log_in_user(user)
                    resp = self.client.get(url)
                    if success_test:
                        success_test(resp)
                    else:
                        self.assertEqual(resp.status_code, success_status,
                                         "View %s returned status %s for user %s; expected %s." % (view_name, resp.status_code, user, success_status))

                # try with invalid users
                for user in view.get('disallowed', all_users - view['allowed']):
                    self.log_in_user(user)
                    resp = self.client.get(url)
                    self.assertRedirects(resp, settings.LOGIN_REDIRECT_URL)

        # make sure that all ^manage/ views were tested
        for urlpattern in urlpatterns:
            if urlpattern._regex.startswith(r'^manage/') and urlpattern._regex != '^manage/?$':
                self.assertTrue(urlpattern.name in views_tested,
                                "Permissions not checked for view '%s' -- add to 'views' or 'any_user_allowed'." % urlpattern.name)