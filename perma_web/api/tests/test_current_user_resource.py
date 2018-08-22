from .utils import ApiResourceTestCase
from perma.models import LinkUser


class CurrentUserResourceTestCase(ApiResourceTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.org_user = LinkUser.objects.get(pk=3)
        cls.regular_user = LinkUser.objects.get(pk=4)
        cls.detail_url = cls.url_base+'/user/'
        cls.fields = [
            'id',
            'first_name',
            'last_name',
            'short_name',
            'full_name',
            'top_level_folders',
        ]

    def test_get_self_detail_json(self):
        self.successful_get(self.detail_url, user=self.org_user, fields=self.fields)

    def test_get_archives_json(self):
        self.successful_get(self.detail_url + 'archives/', user=self.org_user, count=10)
        self.successful_get(self.detail_url + 'archives/', user=self.regular_user, count=11)

    def test_get_folders_json(self):
        self.successful_get(self.detail_url + 'folders/', user=self.org_user, count=2)

    def test_get_orgs_json(self):
        self.successful_get(self.detail_url + 'organizations/', user=self.org_user, count=1)
