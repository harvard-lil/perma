from .utils import ApiResourceTestCase


class VestingOrgResourceTestCase(ApiResourceTestCase):
    pass
    # Currently there is no vesting org resource.
    # We may want to add one for public vesting orgs, however.

    # fixtures = ['fixtures/users.json',
    #             'fixtures/folders.json']
    #
    # def setUp(self):
    #     super(VestingOrgResourceTestCase, self).setUp()
    #     self.list_url = self.url_base+'/vesting_orgs/'
    #     self.detail_url = self.list_url+'1/'
    #     self.fields = [
    #         'id',
    #         'name'
    #     ]
    #
    # def test_get_list_json(self):
    #     self.successful_get(self.list_url, count=3)
    #
    # def test_get_detail_json(self):
    #     self.successful_get(self.detail_url, fields=self.fields)
    #
    # def test_get_folders_json(self):
    #     self.successful_get(self.detail_url + 'folders/', count=1)
