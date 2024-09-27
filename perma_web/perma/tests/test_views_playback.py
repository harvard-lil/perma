from django.conf import settings
from django.urls import reverse

from waffle.testutils import override_flag

from perma.models import Link, CaptureJob
from perma.celery_tasks import cache_playback_status_for_new_links

from .utils import PermaTestCase

from mock import patch
import os


class CommonViewsTestCase(PermaTestCase):

    @classmethod
    def setUpTestData(cls):
        # populate this now-necessary field dynamically, instead of hard-coding in our test fixtures
        cache_playback_status_for_new_links.apply()


    # Record page

    def assert_not_500(self, guid):
        # only makes sure the template renders without internal server error.
        # makes no claims about the contents of the iframe
        with patch('perma.storage_backends.S3MediaStorage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': guid}})
            self.assertIn(b"<iframe ", response.content)
            return response

    def test_archive_without_capture_job(self):
        # assert no capture job
        with self.assertRaises(CaptureJob.DoesNotExist):
            link = Link.objects.get(guid='3SLN-JHX9')
            link.capture_job
        self.assert_not_500('3SLN-JHX9')
        for user in self.users:
            self.log_in_user(user)
            response = self.assert_not_500('3SLN-JHX9')
            self.assertEqual(response.headers['memento-datetime'], 'Sun, 07 Dec 2014 18:55:37 GMT')
            self.assertIn('<http://metafilter.com>; rel=original,', response.headers['link'])
            self.assertIn('<https://testserver/timegate/http://metafilter.com>; rel=timegate,', response.headers['link'])
            self.assertIn('<https://testserver/timemap/link/http://metafilter.com>; rel=timemap; type=application/link-format,', response.headers['link'])
            self.assertIn('<https://testserver/timemap/json/http://metafilter.com>; rel=timemap; type=application/json,', response.headers['link'])
            self.assertIn('<https://testserver/timemap/html/http://metafilter.com>; rel=timemap; type=text/html,', response.headers['link'])
            self.assertIn('<https://testserver/3SLN-JHX9>; rel=memento; datetime="Sun, 07 Dec 2014 18:55:37 GMT"', response.headers['link'])

    def test_regular_archive(self):
        # ensure capture job present and 'completed'
        link = Link.objects.get(guid='UU32-XY8I')
        link.capture_job.status = 'completed'
        link.capture_job.save()
        self.assert_not_500('UU32-XY8I')
        for user in self.users:
            self.log_in_user(user)
            response = self.assert_not_500('UU32-XY8I')
            self.assertEqual(response.headers['memento-datetime'], 'Sat, 19 Jul 2014 20:21:31 GMT')
            self.assertIn('<https://www.wikipedia.org/?special=true>; rel=original,', response.headers['link'])
            self.assertIn('<https://testserver/timegate/https://www.wikipedia.org/?special=true>; rel=timegate,', response.headers['link'])
            self.assertIn('<https://testserver/timemap/link/https://www.wikipedia.org/?special=true>; rel=timemap; type=application/link-format,', response.headers['link'])
            self.assertIn('<https://testserver/timemap/json/https://www.wikipedia.org/?special=true>; rel=timemap; type=application/json,', response.headers['link'])
            self.assertIn('<https://testserver/timemap/html/https://www.wikipedia.org/?special=true>; rel=timemap; type=text/html,', response.headers['link'])
            self.assertIn('<https://testserver/UU32-XY8I>; rel=memento; datetime="Sat, 19 Jul 2014 20:21:31 GMT"', response.headers['link'])

    @override_flag('wacz-playback', active=False)
    def test_regular_archive_with_wacz_and_flag_off(self):
        link = Link.objects.get(guid='UU32-XY8I')
        link.capture_job.status = 'completed'
        link.capture_job.save()
        response = self.assert_not_500('UU32-XY8I')
        # We are playing back a WARC
        self.assertIn(b".warc.gz?", response.content)
        # We are not playing back a WACZ
        self.assertNotIn(b".wacz?", response.content)

    @override_flag('wacz-playback', active=True)
    def test_regular_archive_with_wacz_and_flag_on(self):
        link = Link.objects.get(guid='UU32-XY8I')
        link.capture_job.status = 'completed'
        link.capture_job.save()
        link.wacz_size = 1  # anything non-zero
        link.save()
        response = self.assert_not_500('UU32-XY8I')
        # We are not playing back a WARC
        self.assertNotIn(b".warc.gz?", response.content)
        # We are playing back a WACZ
        self.assertIn(b".wacz?", response.content)

    @override_flag('wacz-playback', active=True)
    def test_regular_archive_without_wacz_and_flag_on(self):
        link = Link.objects.get(guid='UU32-XY8I')
        link.capture_job.status = 'completed'
        link.capture_job.save()
        self.assertFalse(link.wacz_size)
        response = self.assert_not_500('UU32-XY8I')
        # We are playing back a WARC
        self.assertIn(b".warc.gz?", response.content)
        # We are not playing back a WACZ
        self.assertNotIn(b".wacz?", response.content)

    def test_archive_with_unsuccessful_capturejob(self):
        link = Link.objects.get(guid='UU32-XY8I')
        for status in ['pending','in_progress','deleted','failed', 'invalid']:
            link.capture_job.status = status
            link.capture_job.save()
            self.assert_not_500('UU32-XY8I')

    def test_archive_with_no_captures(self):
        link = Link.objects.get(guid='TE73-AKWM')
        self.assertTrue(link.capture_job.status == 'completed')
        self.assertFalse(link.captures.count())
        response = self.assert_not_500('TE73-AKWM')
        self.assertNotIn('memento-datetime', response.headers)
        self.assertNotIn('link', response.headers)
        # TODO: this just renders a blank iframe... not desirable.
        # See https://github.com/harvard-lil/perma/issues/2574

    def test_screenshot_only_archive_default_to_screenshot_view_false(self):
        link = Link.objects.get(guid='ABCD-0007')
        self.assertFalse(link.default_to_screenshot_view)
        self.assertTrue(link.capture_job.status == 'completed')
        self.assertTrue(link.captures.count())
        with patch('perma.storage_backends.S3MediaStorage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'ABCD-0007'}}, request_kwargs={'follow': True})
            self.assertEqual(response.request.get('QUERY_STRING'), 'type=image')
            self.assertIn('memento-datetime', response.headers)
            self.assertIn('link', response.headers)

    def test_capture_only_archive_default_to_screenshot_view_true(self):
        link = Link.objects.get(guid='N1N0-33DB')
        self.assertTrue(link.default_to_screenshot_view)
        with patch('perma.storage_backends.S3MediaStorage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'N1N0-33DB'}}, request_kwargs={'follow': True})
            self.assertFalse(b'Enhance screenshot playback' in response.content)
            self.assertEqual(response.request.get('QUERY_STRING'), 'type=standard')

    # This tests that where there is only a screenshot and default to screenshot, there's no redirect to add the "type=image" query
    def test_screenshot_only_archive_default_to_screenshot_view_true(self):
        link = Link.objects.get(guid='ABCD-0008')
        self.assertTrue(link.default_to_screenshot_view)
        with patch('perma.storage_backends.S3MediaStorage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'ABCD-0008'}}, request_kwargs={'follow': True})
            self.assertEqual(response.request.get('QUERY_STRING'), '')

    # This tests that where there is only a primary but no default to screenshot, there's no redirect to add the "type=standard" query
    def test_capture_only_archive_default_to_screenshot_view_false(self):
        link = Link.objects.get(guid='M1L0-87DB')
        self.assertFalse(link.default_to_screenshot_view)
        with patch('perma.storage_backends.S3MediaStorage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'M1L0-87DB'}}, request_kwargs={'follow': True})
            self.assertEqual(response.request.get('QUERY_STRING'), '')

    # This tests that where there is BOTH a primary and screenshot but no default to screenshot, there's no redirect to add the "type=standard" query
    def test_full_archive_default_to_screenshot_view_false(self):
        link = Link.objects.get(guid='UU32-XY8I')
        self.assertFalse(link.default_to_screenshot_view)
        with patch('perma.storage_backends.S3MediaStorage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'UU32-XY8I'}}, request_kwargs={'follow': True})
            self.assertFalse(b'Enhance screenshot playback' in response.content)
            self.assertEqual(response.request.get('QUERY_STRING'), '')
   
    # This tests that where there is BOTH a primary and screenshot and default to screenshot, there's no redirect to add the "type=standard" query
    def test_full_archive_default_to_screenshot_view_true(self):
        link = Link.objects.get(guid='F1X1-LS24')
        self.assertTrue(link.default_to_screenshot_view)
        with patch('perma.storage_backends.S3MediaStorage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'F1X1-LS24'}}, request_kwargs={'follow': True})
            self.assertTrue(b'Enhance screenshot playback' in response.content)
            self.assertEqual(response.request.get('QUERY_STRING'), '')

    def test_capture_only_default_to_screenshot_view_true(self):
        link = Link.objects.get(guid='N1N0-33DB')
        self.assertTrue(link.default_to_screenshot_view)
        with patch('perma.storage_backends.S3MediaStorage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'N1N0-33DB'}}, request_kwargs={'follow': True})
            self.assertFalse(b'Enhance screenshot playback' in response.content)
            self.assertEqual(response.request.get('QUERY_STRING'), 'type=standard')

    # patch default storage so that it returns a sample warc
    def test_dark_archive(self):
        with patch('perma.storage_backends.S3MediaStorage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'ABCD-0001'}}, require_status_code=403)
            self.assertIn(b"This record is private and cannot be displayed.", response.content)
            self.assertNotIn('memento-datetime', response.headers)
            self.assertNotIn('link', response.headers)

            # check that top bar is displayed to logged-in users
            for user in self.users:
                self.log_in_user(user)
                response = self.get('single_permalink', reverse_kwargs={'kwargs': {'guid': 'ABCD-0001'}})
                self.assertIn(b"This record is private.", response.content)
                self.assertNotIn('memento-datetime', response.headers)
                self.assertNotIn('link', response.headers)

    # Feature temporarily disabled
    """
    def test_redirect_to_download(self):
        with patch('perma.storage_backends.S3MediaStorage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            # Give user option to download to view pdf if on mobile
            link = Link.objects.get(pk='7CF8-SS4G')

            client = Client(HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 6_1_4 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10B350 Safari/8536.25')
            response = client.get(reverse('single_permalink', kwargs={'guid': link.guid}), secure=True)
            self.assertIn(b"Perma.cc can\xe2\x80\x99t display this file type on mobile", response.content)

            # If not on mobile, display link as normal
            client = Client(HTTP_USER_AGENT='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/601.7.7 (KHTML, like Gecko) Version/9.1.2 Safari/601.7.7')
            response = client.get(reverse('single_permalink', kwargs={'guid': link.guid}), secure=True)
            self.assertNotIn(b"Perma.cc can\xe2\x80\x99t display this file type on mobile", response.content)
    """

    def test_deleted(self):
        response = self.get('single_permalink', reverse_kwargs={'kwargs': {'guid': 'ABCD-0003'}}, require_status_code=410, request_kwargs={'follow': True})
        self.assertIn(b"This record has been deleted.", response.content)
        self.assertNotIn('memento-datetime', response.headers)
        self.assertNotIn('link', response.headers)

    def test_misformatted_nonexistent_links_404(self):
        self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'JJ99--JJJJ'}}, require_status_code=404)
        self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': '988-JJJJ=JJJJ'}}, require_status_code=404)

    def test_properly_formatted_nonexistent_links_404(self):
        self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'JJ99-JJJJ'}}, require_status_code=404)

        # Test the original ID style. We shouldn't get a redirect.
        self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': '0J6pkzDeQwT'}}, require_status_code=404)

    def test_replacement_link(self):
        response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'ABCD-0006'}}, require_status_code=302)
        self.assertRedirects(response, reverse('single_permalink', kwargs={'guid': '3SLN-JHX9'}), fetch_redirect_response=False)
