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
            'test_org_user@example.com',
            'test_user@example.com'
        }
        views = [
            {
                'urls': [
                    ['user_management_manage_registry_user'],
                    ['user_management_registry_user_add_user'],
                    ['user_management_manage_single_registry_user_delete', {'kwargs':{'user_id': 1}}],
                    ['user_management_manage_single_registry_user_remove', {'kwargs':{'user_id': 1}}],
                    ['user_management_manage_registrar'],
                    ['user_management_manage_single_registrar', {'kwargs':{'registrar_id': 1}}],
                    ['user_management_manage_single_registrar_user', {'kwargs':{'user_id': 2}}],
                    ['user_management_manage_single_registrar_user_delete', {'kwargs':{'user_id': 2}}],
                    ['user_management_manage_single_registrar_user_reactivate', {'kwargs':{'user_id': 2}}],
                    ['user_management_approve_pending_registrar', {'kwargs':{'registrar_id': 2}}],
                    ['user_management_manage_user'],
                    ['user_management_user_add_registrar', {'kwargs': {'user_id': 4}}],
                    ['user_management_manage_single_user', {'kwargs':{'user_id': 4}}],
                    ['user_management_manage_single_user_delete', {'kwargs':{'user_id': 4}}],
                    ['user_management_manage_single_organization_user_delete', {'kwargs':{'user_id': 3}}],
                    ['user_management_manage_single_organization_user_reactivate', {'kwargs':{'user_id': 3}}],
                    ['user_management_manage_single_user_reactivate', {'kwargs':{'user_id': 4}}],
                ],
                'allowed': {'test_registry_member@example.com'},
            },
            {
                'urls': [
                    ['user_management_manage_registrar_user'],
                    ['user_management_registrar_user_add_user'],
                ],
                'allowed': {'test_registry_member@example.com', 'test_registrar_member@example.com'},
            },
            {
                'urls': [
                    ['user_management_manage_single_organization_user', {'kwargs':{'user_id': 3}}],
                    ['user_management_manage_organization_user'],
                    ['vest_link', {'kwargs': {'guid': '1234'}, 'success_status': 404}],
                    ['user_management_manage_organization'],
                    ['user_management_manage_single_organization', {'kwargs':{'org_id':1}}],
                    ['user_management_organization_user_add_user'],
                    ['user_management_manage_single_organization_user_remove', {'kwargs':{'user_id': 3},
                     'success_status': 302}],
                ],
                'allowed': {'test_registry_member@example.com', 'test_registrar_member@example.com',
                        'test_org_user@example.com'},
            },
            {
                'urls': [
                    ['user_management_manage_single_registrar_user_remove', {'kwargs':{'user_id': 2}}],
                ],
                'allowed': {'test_registrar_member@example.com'}
            },

            {
                'urls': [
                    ['user_management_organization_user_leave_organization', {'kwargs':{'org_id': 1}}],
                ],
                'allowed': {'test_org_user@example.com'}
            },

            {
                'urls': [
                    ['user_management_settings_profile'],
                    ['user_management_settings_password'],
                    ['user_management_settings_tools'],
                    ['create_link'],
                    ['link_browser'],
                    ['folder_contents', {'kwargs': {'folder_id': '12345'}, 'success_status': 404}],
                    ['user_delete_link', {'kwargs':{'guid':'1234'},'success_status':404}],
                    ['dark_archive_link', {'kwargs': {'guid': '1234'}, 'success_status': 404}],
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
                    self.assertRedirects(resp, settings.LOGIN_URL+"?next="+url,
                                         msg_prefix="Error while confirming that %s can't view %s: " % (user, view_name))

        # make sure that all ^manage/ views were tested
        for urlpattern in urlpatterns:
            if urlpattern._regex.startswith(r'^manage/') and urlpattern._regex != '^manage/?$':
                self.assertTrue(urlpattern.name in views_tested,
                                "Permissions not checked for view '%s' -- add to 'views' or 'any_user_allowed'." % urlpattern.name)
