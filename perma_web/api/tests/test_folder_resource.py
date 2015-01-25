from .utils import ApiResourceTestCase
from api.resources import FolderResource
from perma.models import LinkUser, Folder


class FolderResourceTestCase(ApiResourceTestCase):

    resource = FolderResource

    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(FolderResourceTestCase, self).setUp()

        self.vesting_member = LinkUser.objects.get(pk=3)
        self.empty_child_folder = Folder.objects.get(pk=29)
        self.nonempty_child_folder = Folder.objects.get(pk=30)

    def test_should_strip_whitespace_from_name(self):
        name = 'This is a folder name'
        obj = self.successful_post(self.list_url,
                                   data={'name': ' '+name+'  '},
                                   user=self.vesting_member)

        self.assertEqual(obj['name'], name)

    def test_moving(self):
        user = self.empty_child_folder.created_by
        parent_folder = self.nonempty_child_folder
        child_folder = self.empty_child_folder

        self.successful_put(
            "{0}folders/{1}/".format(self.detail_url(parent_folder), child_folder.pk),
            user=user
        )

        # Make sure it's listed in the folder
        obj = self.successful_get(self.detail_url(child_folder), user=user)
        data = self.successful_get(self.detail_url(parent_folder)+"folders/", user=user)
        self.assertIn(obj, data['objects'])
