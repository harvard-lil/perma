from .utils import ApiResourceTestCase
from api.resources import LinkResource
from perma.models import Link, LinkUser


class LinkAuthorizationTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/archive.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(LinkAuthorizationTestCase, self).setUp()

        self.registry_member = LinkUser.objects.get(pk=1)
        self.registrar_member = LinkUser.objects.get(pk=2)
        self.vesting_member = LinkUser.objects.get(pk=3)
        self.regular_user = LinkUser.objects.get(pk=4)
        self.vesting_manager = LinkUser.objects.get(pk=5)

        self.vested_link = Link.objects.get(pk="3SLN-JHX9")
        self.unvested_link = Link.objects.get(pk="7CF8-SS4G")

        self.list_url = "{0}/{1}/".format(self.url_base, LinkResource.Meta.resource_name)

        self.vested_url = "{0}{1}/".format(self.list_url, self.vested_link.pk)
        self.unvested_url = "{0}{1}/".format(self.list_url, self.unvested_link.pk)

    def get_credentials(self, user):
        return self.create_apikey(username=user.email, api_key=user.api_key.key)

    ############
    # Updating #
    ############

    def patch_link(self, user, new_vals):
        old_data = self.deserialize(self.api_client.get(self.vested_url, format='json'))
        new_data = old_data.copy()
        new_data.update(new_vals)

        count = Link.objects.count()
        self.assertHttpAccepted(
            self.api_client.patch(self.vested_url,
                                  format='json',
                                  data=new_data,
                                  authentication=self.get_credentials(user)))

        # Make sure the count hasn't changed & we did an update.
        self.assertEqual(Link.objects.count(), count)

        fresh_data = self.deserialize(self.api_client.get(self.vested_url, format='json'))
        for attr in new_vals.keys():
            self.assertNotEqual(fresh_data[attr], old_data[attr])
            self.assertEqual(fresh_data[attr], new_data[attr])

        return fresh_data

    def reject_patch_link(self, user, new_vals):
        old_data = self.deserialize(self.api_client.get(self.vested_url, format='json'))
        new_data = old_data.copy()
        new_data.update(new_vals)

        count = Link.objects.count()
        self.assertHttpUnauthorized(
            self.api_client.patch(self.vested_url,
                                  format='json',
                                  data=new_data,
                                  authentication=self.get_credentials(user)))

        self.assertEqual(Link.objects.count(), count)
        self.assertEqual(
            self.deserialize(self.api_client.get(self.vested_url, format='json')),
            old_data)

    def test_should_allow_link_owner_to_patch_notes_and_title(self):
        self.patch_link(self.vested_link.created_by,
                        {'notes': 'These are new notes',
                         'title': 'This is a new title'})

    def test_should_allow_member_of_links_vesting_org_to_patch_notes_and_title(self):
        self.patch_link(self.vested_link.vesting_org.users.first(),
                        {'notes': 'These are new notes',
                         'title': 'This is a new title'})

    def test_should_allow_member_of_links_vesting_registrar_to_patch_notes_and_title(self):
        registrar = self.vested_link.vesting_org.registrar
        self.patch_link(LinkUser.objects.filter(registrar=registrar.pk).first(),
                        {'notes': 'These are new notes',
                         'title': 'This is a new title'})

    def test_should_reject_patch_from_user_lacking_owner_and_folder_access(self):
        self.reject_patch_link(self.vesting_manager,
                               {'notes': 'These are new notes',
                                'title': 'This is a new title'})

    def test_should_allow_link_owner_to_dark_archive(self):
        user = self.vested_link.created_by
        data = self.patch_link(user, {'dark_archived': True})
        self.assertEqual(data['dark_archived_by']['id'], user.id)

    def test_should_allow_member_of_links_vesting_org_to_dark_archive(self):
        user = self.vested_link.vesting_org.users.first()
        data = self.patch_link(user, {'dark_archived': True})
        self.assertEqual(data['dark_archived_by']['id'], user.id)

    def test_should_allow_member_of_links_vesting_registrar_to_dark_archive(self):
        user = LinkUser.objects.filter(registrar=self.vested_link.vesting_org.registrar.pk).first()
        data = self.patch_link(user, {'dark_archived': True})
        self.assertEqual(data['dark_archived_by']['id'], user.id)

    def test_should_reject_dark_archive_from_user_lacking_owner_and_folder_access(self):
        self.reject_patch_link(self.vesting_manager, {'dark_archived': True})

    #############
    # Deleteing #
    #############

    def test_should_allow_owner_to_delete_link(self):
        count = Link.objects.count()
        self.assertHttpAccepted(
            self.api_client.delete(self.unvested_url,
                                   format='json',
                                   authentication=self.get_credentials(self.unvested_link.created_by)))

        self.assertEqual(Link.objects.count(), count-1)

        self.assertHttpNotFound(
            self.api_client.get(self.unvested_url,
                                format='json'))

    def test_should_reject_delete_for_vested_link(self):
        self.assertHttpUnauthorized(
            self.api_client.delete(self.vested_url,
                                   format='json',
                                   authentication=self.get_credentials(self.vested_link.created_by)))

        self.assertHttpOK(
            self.api_client.get(self.vested_url,
                                format='json'))

    def test_should_reject_delete_from_users_who_dont_own_link(self):
        self.assertHttpUnauthorized(
            self.api_client.delete(self.vested_url,
                                   format='json',
                                   authentication=self.get_credentials(self.vesting_member)))

        self.assertHttpUnauthorized(
            self.api_client.delete(self.vested_url,
                                   format='json',
                                   authentication=self.get_credentials(self.registrar_member)))

        self.assertHttpUnauthorized(
            self.api_client.delete(self.vested_url,
                                   format='json',
                                   authentication=self.get_credentials(self.vesting_manager)))

        self.assertHttpOK(
            self.api_client.get(self.vested_url,
                                format='json'))
