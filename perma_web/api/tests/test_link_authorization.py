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

        self.link = Link.objects.get(pk="3SLN-JHX9")

        self.list_url = "{0}/{1}/".format(self.url_base, LinkResource.Meta.resource_name)
        self.detail_url = "{0}{1}/".format(self.list_url, self.link.pk)

    def get_credentials(self, user):
        return self.create_apikey(username=user.email, api_key=user.api_key.key)

    def patch_link(self, user, new_vals):
        old_data = self.deserialize(self.api_client.get(self.detail_url, format='json'))
        new_data = old_data.copy()
        new_data.update(new_vals)

        count = Link.objects.count()
        self.assertHttpAccepted(
            self.api_client.patch(self.detail_url,
                                  format='json',
                                  data=new_data,
                                  authentication=self.get_credentials(user)))

        # Make sure the count hasn't changed & we did an update.
        self.assertEqual(Link.objects.count(), count)

        fresh_data = self.deserialize(self.api_client.get(self.detail_url, format='json'))
        self.assertNotEqual(fresh_data, old_data)
        self.assertEqual(fresh_data, new_data)

    def test_should_allow_link_owner_to_patch_notes_and_title(self):
        self.patch_link(self.regular_user,
                        {'notes': 'These are new notes',
                         'title': 'This is a new title'})

    def test_should_allow_member_of_links_vesting_org_to_patch_notes_and_title(self):
        self.patch_link(self.vesting_member,
                        {'notes': 'These are new notes',
                         'title': 'This is a new title'})

    def test_should_allow_member_of_links_vesting_registrar_to_patch_notes_and_title(self):
        self.patch_link(self.registrar_member,
                        {'notes': 'These are new notes',
                         'title': 'This is a new title'})

    def test_should_reject_patch_from_user_lacking_owner_or_folder_access(self):
        old_data = self.deserialize(self.api_client.get(self.detail_url, format='json'))
        new_data = old_data.copy()
        new_data.update({'notes': 'These are new notes',
                         'title': 'This is a new title'})

        count = Link.objects.count()
        self.assertHttpUnauthorized(
            self.api_client.patch(self.detail_url,
                                  format='json',
                                  data=new_data,
                                  authentication=self.get_credentials(self.vesting_manager)))

        self.assertEqual(Link.objects.count(), count)
        self.assertEqual(
            self.deserialize(self.api_client.get(self.detail_url, format='json')),
            old_data)

    def test_should_allow_owner_to_delete_link(self):
        count = Link.objects.count()
        self.assertHttpAccepted(
            self.api_client.delete(self.detail_url,
                                   format='json',
                                   authentication=self.get_credentials(self.regular_user)))

        self.assertEqual(Link.objects.count(), count-1)

        self.assertHttpNotFound(
            self.api_client.get(self.detail_url,
                                format='json'))

    def test_should_reject_delete_from_users_who_dont_own_link(self):
        self.assertHttpOK(
            self.api_client.get(self.detail_url,
                                format='json'))

        self.assertHttpUnauthorized(
            self.api_client.delete(self.detail_url,
                                   format='json',
                                   authentication=self.get_credentials(self.vesting_member)))

        self.assertHttpUnauthorized(
            self.api_client.delete(self.detail_url,
                                   format='json',
                                   authentication=self.get_credentials(self.registrar_member)))

        self.assertHttpUnauthorized(
            self.api_client.delete(self.detail_url,
                                   format='json',
                                   authentication=self.get_credentials(self.vesting_manager)))

        self.assertHttpOK(
            self.api_client.get(self.detail_url,
                                format='json'))
