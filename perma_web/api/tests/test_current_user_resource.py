from .utils import ApiResourceTestCase

from perma.models import LinkUser


class CurrentUserResourceTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/groups.json',
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
        self.successful_get(self.detail_url, user=self.vesting_member, fields=self.fields)

    def test_get_archives_json(self):
        self.successful_get(self.detail_url + 'archives/', user=self.vesting_member, count=1)

    def test_get_folders_json(self):
        self.successful_get(self.detail_url + 'folders/', user=self.vesting_member, count=2)

    def test_get_vesting_orgs_json(self):
        self.successful_get(self.detail_url + 'vesting_orgs/', user=self.vesting_member, count=1)
