from django.test import TestCase, override_settings
from perma.tasks import update_stats, upload_all_to_internet_archive, upload_to_internet_archive, delete_from_internet_archive
from perma.models import Link

@override_settings(CELERY_ALWAYS_EAGER=True, UPLOAD_TO_INTERNET_ARCHIVE=True)
class TaskTestCase(TestCase):

    def testUpdateStats(self):
        # this tests only that the task runs,
        # not anything about the task itself
        self.assertTrue(update_stats.delay())

    def testUploadAllToInternetArchive(self):
        # this tests only that the task runs,
        # not anything about the task itself
        self.assertTrue(upload_all_to_internet_archive.delay())

    def testUploadToInternetArchive(self):
        # test when GUID does not exist
        self.assertTrue(upload_to_internet_archive.delay('ZZZZ-ZZZZ'))

    def testDeleteFromInternetArchive(self):
        # test when GUID does not exist
        with self.assertRaises(Link.DoesNotExist):
            delete_from_internet_archive.delay('ZZZZ-ZZZZ')
