from .utils import ApiResourceTestCase
from api.resources import FolderResource
from perma.models import LinkUser


class FolderResourceTestCase(ApiResourceTestCase):

    resource = FolderResource

    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/groups.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(FolderResourceTestCase, self).setUp()
        self.vesting_member = LinkUser.objects.get(pk=3)

        self.list_url = "{0}/{1}/".format(self.url_base, FolderResource.Meta.resource_name)

    def test_should_strip_whitespace_from_name(self):
        name = 'This is a folder name'
        obj = self.successful_post(self.list_url,
                                   data={'name': ' '+name+'  '},
                                   user=self.vesting_member)

        self.assertEqual(obj['name'], name)
