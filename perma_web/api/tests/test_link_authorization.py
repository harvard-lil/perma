import unittest
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

        self.link_1 = Link.objects.get(pk="3SLN-JHX9")

        self.list_url = "{0}/{1}/".format(self.url_base, LinkResource.Meta.resource_name)
        self.detail_url = "{0}{1}/".format(self.list_url, self.link_1.pk)

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

    def reject_patch_link(self, user, new_vals):
        old_data = self.deserialize(self.api_client.get(self.detail_url, format='json'))
        new_data = old_data.copy()
        new_data.update(new_vals)

        count = Link.objects.count()
        self.assertHttpUnauthorized(
            self.api_client.patch(self.detail_url,
                                  format='json',
                                  data=new_data,
                                  authentication=self.get_credentials(user)))

        self.assertEqual(Link.objects.count(), count)
        self.assertEqual(
            self.deserialize(self.api_client.get(self.detail_url, format='json')),
            old_data)

    def test_should_allow_link_owner_to_patch_notes_and_title(self):
        self.patch_link(self.regular_user,
                        {'notes': 'These are new notes',
                         'title': 'This is a new title'})

    def test_should_allow_user_of_link_vesting_org_folder_to_patch_notes_and_title(self):
        self.patch_link(self.vesting_member,
                        {'notes': 'These are new notes',
                         'title': 'This is a new title'})

    def test_should_reject_patch_from_unauthorized_user(self):
        self.reject_patch_link(self.vesting_manager,
                               {'notes': 'These are new notes',
                                'title': 'This is a new title'})

    @unittest.expectedFailure
    def test_should_allow_registrar_user_of_link_vesting_org_registrar_to_dark_archive(self):
        self.fail()
        # if request.user.has_group('registrar_user') and not link.vesting_org.registrar == request.user.registrar:
        #     return HttpResponseRedirect(reverse('single_linky', args=[guid]))

    @unittest.expectedFailure
    def test_should_allow_vesting_user_of_link_vesting_org_to_dark_archive(self):
        self.fail()
        # if request.user.has_group('vesting_user') and not link.vesting_org == request.user.vesting_org:
        #     return HttpResponseRedirect(reverse('single_linky', args=[guid]))

    def test_should_limit_delete_to_link_owner(self):
        self.assertHttpOK(
            self.api_client.get(self.detail_url,
                                format='json'))

        self.assertHttpUnauthorized(
            self.api_client.delete(self.detail_url,
                                   format='json',
                                   authentication=self.get_credentials(self.user_2)))
        # confirm that the link wasn't deleted
        self.assertHttpOK(
            self.api_client.get(self.detail_url,
                                format='json'))
