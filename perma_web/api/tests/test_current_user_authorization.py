from .utils import ApiResourceTransactionTestCase
from perma.tests.test_capture_job import create_capture_job
from perma.models import LinkUser, Link


class CurrentUserAuthorizationTestCase(ApiResourceTransactionTestCase):
    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/api_keys.json',
                'fixtures/archive.json']

    def setUp(self):
        super(CurrentUserAuthorizationTestCase, self).setUp()
        self.org_user = LinkUser.objects.get(pk=3)
        self.regular_user = LinkUser.objects.get(pk=4)
        self.detail_url = self.url_base+'/user/'

    def test_should_allow_user_to_get_self(self):
        self.successful_get(self.detail_url, user=self.org_user)

    def test_get_reject_request_from_unauthenticated_visitor(self):
        self.assertHttpUnauthorized(self.api_client.get(self.detail_url))

    def test_should_provide_different_detail_data_relative_to_user(self):
        vm_data = self.successful_get(self.detail_url, user=self.org_user)
        reg_data = self.successful_get(self.detail_url, user=self.regular_user)

        self.assertEqual(list(vm_data.keys()), list(reg_data.keys()))
        self.assertNotEqual(vm_data, reg_data)

    # folders

    def test_should_provide_different_folder_data_relative_to_user(self):
        vm_data = self.successful_get(self.detail_url + 'folders/', user=self.org_user)
        reg_data = self.successful_get(self.detail_url + 'folders/', user=self.regular_user)

        self.assertEqual(list(vm_data.keys()), list(reg_data.keys()))
        self.assertNotEqual(vm_data['objects'], reg_data['objects'])

    def test_should_allow_folder_detail(self):
        self.successful_get(self.detail_url + 'folders/%s/' % (self.org_user.root_folder.pk,), user=self.org_user)

    def test_should_reject_folder_detail_for_other_user(self):
        self.rejected_get(self.detail_url + 'folders/%s/' % (self.org_user.root_folder.pk,),
                          user=self.regular_user,
                          expected_status_code=403)

    # archives

    def test_should_provide_different_archive_data_relative_to_user(self):
        vm_data = self.successful_get(self.detail_url + 'archives/', user=self.org_user)
        reg_data = self.successful_get(self.detail_url + 'archives/', user=self.regular_user)

        self.assertEqual(list(vm_data.keys()), list(reg_data.keys()))
        self.assertNotEqual(vm_data['objects'], reg_data['objects'])

    def test_should_allow_archive_detail(self):
        self.successful_get(self.detail_url + 'archives/%s/' % (self.org_user.organizations.first().links.first().pk,), user=self.org_user)

    def test_should_reject_archive_detail_for_other_user(self):
        link = Link.objects.exclude(created_by=self.regular_user)[0]
        self.rejected_get(self.detail_url + 'archives/%s/' % (link.pk,),
                          user=self.regular_user,
                          expected_status_code=403)

    # organizations

    def test_should_provide_different_org_data_relative_to_user(self):
        vm_data = self.successful_get(self.detail_url + 'organizations/', user=self.org_user)
        reg_data = self.successful_get(self.detail_url + 'organizations/', user=self.regular_user)

        self.assertEqual(list(vm_data.keys()), list(reg_data.keys()))
        self.assertNotEqual(vm_data['objects'], reg_data['objects'])

    def test_should_allow_org_detail(self):
        self.successful_get(self.detail_url + 'organizations/%s/' % (self.org_user.organizations.first().pk,), user=self.org_user)

    def test_should_reject_org_detail_for_other_user(self):
        self.rejected_get(self.detail_url + 'organizations/%s/' % (self.org_user.organizations.first().pk,),
                          user=self.regular_user,
                          expected_status_code=403)

    # capture jobs

    def test_should_provide_different_capture_jobs_data_relative_to_user(self):
        create_capture_job(self.org_user)
        create_capture_job(self.regular_user)

        vm_data = self.successful_get(self.detail_url + 'capture_jobs/', user=self.org_user)
        reg_data = self.successful_get(self.detail_url + 'capture_jobs/', user=self.regular_user)

        self.assertEqual(list(vm_data.keys()), list(reg_data.keys()))
        self.assertNotEqual(vm_data['objects'], reg_data['objects'])

    def test_should_allow_capture_job_detail(self):
        job = create_capture_job(self.org_user)
        self.successful_get(self.detail_url + 'capture_jobs/%s/' % (job.link_id,), user=self.org_user)

    def test_should_reject_capture_job_detail_for_other_user(self):
        job = create_capture_job(self.org_user)
        self.rejected_get(self.detail_url + 'capture_jobs/%s/' % (job.link_id,), user=self.regular_user,
                          expected_status_code=403)

