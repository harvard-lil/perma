from .utils import ApiResourceTestCase

from perma.models import LinkUser


class CurrentUserResourceTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/api_keys.json',
                'fixtures/archive.json']

    def setUp(self):
        super(CurrentUserResourceTestCase, self).setUp()
        self.vesting_member = LinkUser.objects.get(pk=3)
        self.detail_url = self.url_base+'/user/'
        self.fields = [
            'id',
            'first_name',
            'last_name',
            'short_name',
            'full_name',
            'groups'
        ]

    def test_get_self_detail_json(self):
        self.successful_detail_get(self.detail_url, self.vesting_member, self.fields)

    def test_get_archives_json(self):
        self.successful_list_get(self.detail_url + 'archives/', self.vesting_member, 1)

    def test_get_folders_json(self):
        self.successful_list_get(self.detail_url + 'folders/', self.vesting_member, 2)

    def test_get_vesting_orgs_json(self):
        self.successful_list_get(self.detail_url + 'vesting_orgs/', self.vesting_member, 1)
