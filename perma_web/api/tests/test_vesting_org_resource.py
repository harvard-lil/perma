from .utils import ApiResourceTestCase


class VestingOrgResourceTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json']

    def setUp(self):
        super(VestingOrgResourceTestCase, self).setUp()
        self.list_url = self.url_base+'/vesting_orgs/'
        self.detail_url = self.list_url+'1/'
        self.fields = [
            'id',
            'name'
        ]

    def test_get_list_json(self):
        self.successful_list_get(self.list_url, 3)

    def test_get_detail_json(self):
        self.successful_detail_get(self.detail_url, self.fields)

    def test_get_vesting_orgs_json(self):
        self.successful_list_get(self.detail_url + 'folders/', 1)
