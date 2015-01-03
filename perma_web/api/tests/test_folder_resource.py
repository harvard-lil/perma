from .utils import ApiResourceTestCase
from api.resources import FolderResource
from perma.models import LinkUser, Folder


class FolderResourceTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(FolderResourceTestCase, self).setUp()
        self.user = LinkUser.objects.get(email='test_vesting_member@example.com')

        self.list_url = "{0}/{1}/".format(self.url_base, FolderResource.Meta.resource_name)

    def test_should_strip_whitespace_from_name(self):
        count = Folder.objects.count()
        name = 'This is a folder name'

        self.assertHttpCreated(
            self.api_client.post(self.list_url,
                                 data={'name': ' '+name+'  '},
                                 authentication=self.get_credentials()))

        self.assertEqual(Folder.objects.count(), count+1)
        self.assertEqual(name, Folder.objects.latest('creation_timestamp').name)
