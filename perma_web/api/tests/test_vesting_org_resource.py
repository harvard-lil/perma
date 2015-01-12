from .utils import ApiResourceTestCase


class VestingOrgResourceTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/groups.json']

    def setUp(self):
        super(VestingOrgResourceTestCase, self).setUp()
        self.list_url = self.url_base+'/vesting_orgs/'
        self.detail_url = self.list_url+'1/'
        self.fields = [
            'id',
            'name'
        ]

    def test_get_list_json(self):
        self.successful_get(self.list_url, count=3)

    def test_get_detail_json(self):
        self.successful_get(self.detail_url, fields=self.fields)

    def test_get_folders_json(self):
        self.successful_get(self.detail_url + 'folders/', count=1)
