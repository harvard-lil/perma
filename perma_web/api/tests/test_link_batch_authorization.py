from .utils import ApiResourceTestCase
from perma.models import LinkBatch, LinkUser


class LinkBatchAuthorizationTestCase(ApiResourceTestCase):

    resource_url = '/archives/batches'

    @classmethod
    def setUpTestData(cls):
        cls.org_user = LinkUser.objects.get(pk=3)
        cls.regular_user = LinkUser.objects.get(pk=4)

    def post_batch(self, user, target_folder):
        self.api_client.force_authenticate(user=user)
        return self.api_client.post(
            self.list_url,
            data={'urls': [], 'target_folder': target_folder.pk},
            format='json',
        )

    def test_should_allow_batch_in_accessible_folder(self):
        response = self.post_batch(self.regular_user, self.regular_user.root_folder)

        self.assertHttpCreated(response)
        data = self.deserialize(response)
        self.assertEqual(data['created_by'], self.regular_user.pk)
        self.assertEqual(data['target_folder']['id'], self.regular_user.root_folder.pk)
        self.assertTrue(
            LinkBatch.objects.filter(
                pk=data['id'],
                created_by=self.regular_user,
                target_folder=self.regular_user.root_folder,
            ).exists()
        )

    def test_should_reject_batch_in_inaccessible_folder_without_returning_folder_data(self):
        target_folder = self.org_user.root_folder
        response = self.post_batch(self.regular_user, target_folder)

        self.assertEqual(response.status_code, 400)
        self.assertIn('target_folder', self.deserialize(response))
        self.assertNotContains(response, target_folder.name, status_code=400)
        self.assertFalse(
            LinkBatch.objects.filter(
                created_by=self.regular_user,
                target_folder=target_folder,
            ).exists()
        )

    def test_batch_list_fetches_target_folders_in_main_query(self):
        LinkBatch.objects.create(
            created_by=self.regular_user,
            target_folder=self.regular_user.root_folder,
        )
        LinkBatch.objects.create(
            created_by=self.regular_user,
            target_folder=self.regular_user.root_folder,
        )
        self.api_client.force_authenticate(user=self.regular_user)

        with self.assertNumQueries(2):
            response = self.api_client.get(self.list_url)

        self.assertHttpOK(response)
