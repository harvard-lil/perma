from django.core.urlresolvers import reverse

from perma.models import *
from perma.urls import urlpatterns

from .utils import PermaTestCase


class PermissionsTestCase(PermaTestCase):

    def test_permissions(self):
        """Test who can log into restricted pages."""
        all_users = {
            'test_admin_user@example.com',
            'test_registrar_user@example.com',
            'test_org_user@example.com',
            'test_user@example.com'
        }
        views = [
            {
                'urls': [
                    ['user_management_stats'],
                    ['user_management_manage_admin_user'],
                    ['user_management_admin_user_add_user'],
                    ['user_management_manage_single_admin_user_delete', {'kwargs':{'user_id': 1}}],
                    ['user_management_manage_single_admin_user_remove', {'kwargs':{'user_id': 1}}],
                    ['user_management_manage_registrar'],
                    ['user_management_manage_single_registrar_user', {'kwargs':{'user_id': 2}}],
                    ['user_management_manage_single_registrar_user_delete', {'kwargs':{'user_id': 2}}],
                    ['user_management_manage_single_registrar_user_reactivate', {'kwargs':{'user_id': 2}}],
                    ['user_management_approve_pending_registrar', {'kwargs':{'registrar_id': 2}}],
                    ['user_management_manage_user'],
                    ['user_management_user_add_user'],
                    ['user_management_manage_single_user', {'kwargs':{'user_id': 4}}],
                    ['user_management_manage_single_user_delete', {'kwargs':{'user_id': 4}}],
                    ['user_management_manage_single_organization_user_delete', {'kwargs':{'user_id': 3}}],
                    ['user_management_manage_single_organization_user_reactivate', {'kwargs':{'user_id': 3}}],
                    ['user_management_manage_single_user_reactivate', {'kwargs':{'user_id': 4}}],
                    ['error_management_get_all'],
                    ['error_management_resolve', {'success_status': 404}],
                ],
                'allowed': {'test_admin_user@example.com'},
            },
            {
                'urls': [
                    ['user_management_manage_registrar_user'],
                    ['user_management_registrar_user_add_user'],
                    ['user_management_manage_single_registrar', {'kwargs':{'registrar_id': 1}}],
                ],
                'allowed': {'test_admin_user@example.com', 'test_registrar_user@example.com'},
            },
            {
                'urls': [
                    ['user_management_manage_single_organization_user', {'kwargs':{'user_id': 3}}],
                    ['user_management_manage_organization_user'],
                    ['user_management_manage_organization'],
                    ['user_management_manage_single_organization', {'kwargs':{'org_id':1}}],
                    ['user_management_manage_single_organization_delete', {'kwargs':{'org_id':1}}],
                    ['user_management_organization_user_add_user'],
                    ['user_management_manage_single_organization_user_remove', {'kwargs':{'user_id': 3},
                     'success_status': 302}],
                ],
                'allowed': {'test_admin_user@example.com', 'test_registrar_user@example.com',
                        'test_org_user@example.com'},
            },
            {
                'urls': [
                    ['user_management_manage_single_registrar_user_remove', {'kwargs':{'user_id': 2}}],
                ],
                'allowed': {'test_registrar_user@example.com'}
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
                    ['user_delete_link', {'kwargs':{'guid':'1234-1234'},'success_status':404}],
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
                    self.assertEqual(resp.status_code, 403,
                                         "View %s returned status %s for user %s; expected %s." % (view_name, resp.status_code, user, success_status))
                    # self.assertRedirects(resp, settings.LOGIN_URL+"?next="+url, target_status_code=302,
                    #                      msg_prefix="Error while confirming that %s can't view %s: " % (user, view_name))

        # make sure that all ^manage/ views were tested
        for urlpattern in urlpatterns:

            # Things that are no longer needed and have become redirects or other special cases
            excluded_names = ['create_link_with_org',
                              'link_browser',
                              'user_management_resend_activation']

            if urlpattern._regex.startswith(r'^manage/') and urlpattern._regex != '^manage/?$' and urlpattern.name not in excluded_names:
                self.assertTrue(urlpattern.name in views_tested,
                                "Permissions not checked for view '%s' -- add to 'views' or 'any_user_allowed'." % urlpattern.name)
