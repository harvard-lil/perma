from .utils import ApiResourceTestCase


class RegistrarResourceTestCase(ApiResourceTestCase):
    pass
    # Currently there is no registrar resource.
    # We may want to add one for public registrars, however.

    # fixtures = ['fixtures/users.json',
    #             'fixtures/folders.json']
    #
    # def setUp(self):
    #     super(RegistrarResourceTestCase, self).setUp()
    #     self.list_url = self.url_base+'/registrars/'
    #     self.detail_url = self.list_url+'1/'
    #     self.fields = [
    #         'id',
    #         'name'
    #     ]
    #
    # def test_get_list_json(self):
    #     self.successful_get(self.list_url, count=1)
    #
    # def test_get_detail_json(self):
    #     self.successful_get(self.detail_url, fields=self.fields)
    #
    # def test_get_organizations_json(self):
    #     self.successful_get(self.detail_url + 'organizations/', count=3)
