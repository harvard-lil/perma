from .utils import ApiResourceTestCase

from perma.models import LinkUser


class CurrentUserResourceTestCase(ApiResourceTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/api_keys.json',
                'fixtures/archive.json']

    def setUp(self):
        super(CurrentUserResourceTestCase, self).setUp()
        self.org_member = LinkUser.objects.get(pk=3)
        self.regular_user = LinkUser.objects.get(pk=4)

        self.detail_url = self.url_base+'/user/'
        self.fields = [
            'id',
            'first_name',
            'last_name',
            'short_name',
            'full_name',
        ]

    def test_get_schema_json(self):
        self.successful_get(self.detail_url + 'schema/', user=self.org_member)

    def test_get_self_detail_json(self):
        self.successful_get(self.detail_url, user=self.org_member, fields=self.fields)

    def test_get_archives_json(self):
        self.successful_get(self.detail_url + 'archives/', user=self.org_member, count=8)
        self.successful_get(self.detail_url + 'archives/', user=self.regular_user, count=9)

    def test_get_folders_json(self):
        self.successful_get(self.detail_url + 'folders/', user=self.org_member, count=1)

    def test_get_orgs_json(self):
        self.successful_get(self.detail_url + 'organizations/', user=self.org_member, count=1)
