from .utils import ApiResourceTestCase

from perma.models import LinkUser


class RegistrarResourceTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(RegistrarResourceTestCase, self).setUp()
        self.vesting_member = LinkUser.objects.get(pk=3)
        self.list_url = self.url_base+'/registrars/'
        self.detail_url = self.list_url+'1/'
        self.fields = [
            'id',
            'name'
        ]

    def test_get_list_json(self):
        self.successful_list_get(self.list_url, 1)

    def test_get_detail_json(self):
        self.successful_detail_get(self.detail_url, self.fields)

    def test_get_vesting_orgs_json(self):
        self.successful_list_get(self.detail_url + 'vesting_orgs/', 3)
