from .utils import ApiResourceTestCase
from api.resources import VestingOrgResource
from perma.models import VestingOrg


class DefaultAuthorizationTestCase(ApiResourceTestCase):

    resource = VestingOrgResource
    assertHttpRejected = ApiResourceTestCase.assertHttpUnauthorized

    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/groups.json',
                'fixtures/api_keys.json']

    def setUp(self):
        super(DefaultAuthorizationTestCase, self).setUp()

        self.list_url = "{0}/{1}/".format(self.url_base, VestingOrgResource.Meta.resource_name)
        self.detail_url = "{0}{1}/".format(self.list_url, VestingOrg.objects.first().pk)

    #######
    # GET #
    #######

    def test_should_allow_logged_out_users_to_get_list(self):
        self.successful_get(self.list_url)

    def test_should_allow_logged_out_users_to_get_detail(self):
        self.successful_get(self.detail_url)

    ########
    # POST #
    ########

    def test_should_reject_create_from_logged_out_user(self):
        self.rejected_post(self.detail_url,
                           data={'name': 'Test Data'})

    #########
    # PATCH #
    #########

    def test_should_reject_update_from_logged_out_user(self):
        self.rejected_patch(self.detail_url,
                            data={'name': 'Test Data'})

    ##########
    # DELETE #
    ##########

    def test_should_reject_delete_from_logged_out_user(self):
        self.rejected_delete(self.detail_url)
