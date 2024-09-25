from django.urls import reverse
from django.test.utils import override_settings

from perma.urls import urlpatterns

import pytest


@override_settings(SECURE_SSL_REDIRECT=False)
@pytest.mark.django_db
def test_permissions(client, admin_user, registrar_user, org_user, link_user_factory, sponsored_user, pending_registrar):
    """Test who can log into restricted pages."""

    regular_user = link_user_factory()

    # Nickname for convenience
    org_user_org = org_user.organizations.first()
    registrar_user_registrar = registrar_user.registrar
    sponsored_user_registrar = sponsored_user.sponsorships.first().registrar

    # Retrieve the registrar user who supports the sponsored user
    sponsored_user_registrar_user = sponsored_user_registrar.users.first()
    assert sponsored_user_registrar_user

    # Create the registrar user who supports the org user
    assert not org_user_org.registrar.users.first()
    org_user_org.registrar.users.add(link_user_factory())
    org_user_registrar_user = org_user_org.registrar.users.first()
    assert org_user_registrar_user

    all_users = {
        admin_user,
        registrar_user,
        org_user_registrar_user,
        sponsored_user_registrar_user,
        org_user,
        sponsored_user,
        regular_user
    }

    views = [
        {
            'urls': [
                ['user_management_stats'],
                ['user_management_manage_admin_user'],
                ['user_management_admin_user_add_user'],
                ['user_management_manage_single_admin_user_delete', {'kwargs':{'user_id': admin_user.id}}],
                ['user_management_manage_single_admin_user_remove', {'kwargs':{'user_id': admin_user.id}}],
                ['user_management_manage_registrar'],
                ['user_management_manage_single_registrar_user', {'kwargs':{'user_id': registrar_user.id}}],
                ['user_management_manage_single_registrar_user_delete', {'kwargs':{'user_id': registrar_user.id}}],
                ['user_management_manage_single_registrar_user_reactivate', {'kwargs':{'user_id': registrar_user.id}}],
                ['user_management_approve_pending_registrar', {'kwargs':{'registrar_id': pending_registrar.id}}],
                ['user_management_manage_user'],
                ['user_management_user_add_user'],
                ['user_management_manage_single_user', {'kwargs':{'user_id': regular_user.id}}],
                ['user_management_manage_single_user_delete', {'kwargs':{'user_id': regular_user.id}}],
                ['user_management_manage_single_organization_user_delete', {'kwargs':{'user_id': org_user.id}}],
                ['user_management_manage_single_organization_user_reactivate', {'kwargs':{'user_id': org_user.id}}],
                ['user_management_manage_single_user_reactivate', {'kwargs':{'user_id': regular_user.id}}],
                ['user_management_manage_single_sponsored_user_delete', {'kwargs':{'user_id': sponsored_user.id}}],
                ['user_management_manage_single_sponsored_user_reactivate', {'kwargs':{'user_id': sponsored_user.id}}]
            ],
            'allowed': {admin_user},
        },
        {
            'urls': [
                ['user_management_manage_registrar_user'],
                ['user_management_registrar_user_add_user'],
                ['user_management_manage_sponsored_user'],
                ['user_management_manage_sponsored_user_export_user_list'],
                ['user_management_sponsored_user_add_user']
            ],
            'allowed': {admin_user, registrar_user, org_user_registrar_user, sponsored_user_registrar_user},
        },
        {
            'urls': [
                ['user_management_manage_single_registrar', {'kwargs':{'registrar_id': registrar_user_registrar.id}}],
            ],
            'allowed': {admin_user, registrar_user},
        },
        {
            'urls': [
                ['user_management_manage_single_sponsored_user', {'kwargs':{'user_id': sponsored_user.id}}],
                ['user_management_manage_single_sponsored_user_remove', {'kwargs':{'user_id': sponsored_user.id, 'registrar_id': sponsored_user_registrar.id}}],
                ['user_management_manage_single_sponsored_user_readd', {'kwargs':{'user_id': sponsored_user.id, 'registrar_id': sponsored_user_registrar.id}}],
                ['user_management_manage_single_sponsored_user_links', {'kwargs':{'user_id': sponsored_user.id, 'registrar_id': sponsored_user_registrar.id}}]
            ],
            'allowed': {admin_user, sponsored_user_registrar_user},
        },
        {
            'urls': [
                ['user_management_manage_organization_user'],
                ['user_management_manage_organization'],
                ['user_management_organization_user_add_user'],
            ],
            'allowed': {admin_user, registrar_user, org_user_registrar_user, sponsored_user_registrar_user, org_user},
        },
        {
            'urls': [
                ['user_management_manage_single_organization_user', {'kwargs':{'user_id': org_user.id}}],
                ['user_management_manage_single_organization', {'kwargs':{'org_id': org_user_org.id}}],
                ['user_management_manage_single_organization_export_user_list', {'kwargs': {'org_id': org_user_org.id}}],
                ['user_management_manage_single_organization_delete', {'kwargs':{'org_id': org_user_org.id}}],
                ['user_management_manage_single_organization_user_remove', {'kwargs':{'user_id': org_user.id},
                 'success_status': 302}],
            ],
            'allowed': {admin_user, org_user_registrar_user, org_user},
        },
        {
            'urls': [
                ['user_management_manage_single_registrar_user_remove', {'kwargs':{'user_id': registrar_user.id}}],
            ],
            'allowed': {registrar_user}
        },

        {
            'urls': [
                ['user_management_organization_user_leave_organization', {'kwargs':{'org_id': org_user_org.id}}],
            ],
            'allowed': {org_user}
        },

        {
            'urls': [
                ['user_management_settings_profile'],
                ['user_management_settings_password'],
                ['user_management_settings_tools'],
                ['create_link'],
                ['user_delete_link', {'kwargs':{'guid':'1234-1234'},'success_status':404}],
            ],
            'allowed': {regular_user, sponsored_user},
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
            client.logout()
            resp = client.get(url)

            assert resp.status_code == 302
            assert resp['Location'] == f"{reverse('user_management_limited_login')}?next={url}"

            # try with valid users
            for user in view['allowed']:
                client.force_login(user)
                resp = client.get(url, secure=True)
                if success_test:
                    success_test(resp)
                else:
                    assert resp.status_code == success_status, \
                        "View %s returned status %s for user %s; expected %s." % (view_name, resp.status_code, user, success_status)

            # try with invalid users
            for user in view.get('disallowed', all_users - view['allowed']):
                client.force_login(user)
                resp = client.get(url)
                assert resp.status_code == 403, \
                    "View %s returned status %s for user %s; expected %s." % (view_name, resp.status_code, user, 403)

    # make sure that all ^manage/ views were tested
    for urlpattern in urlpatterns:

        # Things that are no longer needed and have become redirects or other special cases
        excluded_names = ['create_link_with_org',
                          'link_browser',
                          'user_management_resend_activation']

        if urlpattern.pattern._regex.startswith(r'^manage/') and urlpattern.pattern._regex != '^manage/?$' and urlpattern.name not in excluded_names:
            assert urlpattern.name in views_tested, \
                "Permissions not checked for view '%s' -- add to 'views' or 'any_user_allowed'." % urlpattern.name
