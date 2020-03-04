from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.test import override_settings, Client

from perma.urls import urlpatterns
from perma.models import Registrar, Link, CaptureJob
from perma.tasks import cache_playback_status_for_new_links

from .utils import PermaTestCase

from bs4 import BeautifulSoup
from urllib.parse import urlencode
from mock import patch
import os

@override_settings(CONTACT_REGISTRARS=True)
class CommonViewsTestCase(PermaTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.users = ['test_user@example.com', 'test_org_user@example.com', 'multi_registrar_org_user@example.com', 'test_registrar_user@example.com', 'test_admin_user@example.com']
        cls.from_email = 'example@example.com'
        cls.custom_subject = 'Just some subject here'
        cls.message_text = 'Just some message here.'
        cls.refering_page = 'http://elsewhere.com'
        cls.our_address = settings.DEFAULT_FROM_EMAIL
        cls.subject_prefix = '[perma-contact] '
        cls.flag = "zzzz-zzzz"
        cls.flag_message = "http://perma.cc/{} contains material that is inappropriate.".format(cls.flag)
        cls.flag_subject = "Reporting Inappropriate Content"

        # populate this now-necessary field dynamically, instead of hard-coding in our test fixtures
        cache_playback_status_for_new_links.apply()


    def test_public_views(self):
        # test static template views
        for urlpattern in urlpatterns:
            if urlpattern.callback.__name__ == 'DirectTemplateView':
                self.get(urlpattern.name)

    # Record page

    def assert_not_500(self, guid):
        # only makes sure the template renders without internal server error.
        # makes no claims about the contents of the iframe
        with patch('perma.models.default_storage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
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
            self.assertEqual(response._headers['memento-datetime'][1], 'Sun, 07 Dec 2014 18:55:37 GMT')
            self.assertIn('<http://metafilter.com>; rel=original,', response._headers['link'][1])
            self.assertIn('<http://testserver/timegate/http://metafilter.com>; rel=timegate,', response._headers['link'][1])
            self.assertIn('<http://testserver/timemap/link/http://metafilter.com>; rel=timemap; type=application/link-format,', response._headers['link'][1])
            self.assertIn('<http://testserver/timemap/json/http://metafilter.com>; rel=timemap; type=application/json,', response._headers['link'][1])
            self.assertIn('<http://testserver/timemap/html/http://metafilter.com>; rel=timemap; type=text/html,', response._headers['link'][1])
            self.assertIn('<http://testserver/3SLN-JHX9>; rel=memento; datetime="Sun, 07 Dec 2014 18:55:37 GMT"', response._headers['link'][1])

    def test_regular_archive(self):
        # ensure capture job present and 'completed'
        link = Link.objects.get(guid='UU32-XY8I')
        link.capture_job.status = 'completed'
        link.capture_job.save()
        self.assert_not_500('UU32-XY8I')
        for user in self.users:
            self.log_in_user(user)
            response = self.assert_not_500('UU32-XY8I')
            self.assertEqual(response._headers['memento-datetime'][1], 'Sat, 19 Jul 2014 20:21:31 GMT')
            self.assertIn('<https://www.wikipedia.org/?special=true>; rel=original,', response._headers['link'][1])
            self.assertIn('<http://testserver/timegate/https://www.wikipedia.org/?special=true>; rel=timegate,', response._headers['link'][1])
            self.assertIn('<http://testserver/timemap/link/https://www.wikipedia.org/?special=true>; rel=timemap; type=application/link-format,', response._headers['link'][1])
            self.assertIn('<http://testserver/timemap/json/https://www.wikipedia.org/?special=true>; rel=timemap; type=application/json,', response._headers['link'][1])
            self.assertIn('<http://testserver/timemap/html/https://www.wikipedia.org/?special=true>; rel=timemap; type=text/html,', response._headers['link'][1])
            self.assertIn('<http://testserver/UU32-XY8I>; rel=memento; datetime="Sat, 19 Jul 2014 20:21:31 GMT"', response._headers['link'][1])

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
        self.assertNotIn('memento-datetime', response._headers)
        self.assertNotIn('link', response._headers)
        # TODO: this just renders a blank iframe... not desirable.
        # See https://github.com/harvard-lil/perma/issues/2574

    def test_archive_with_only_screenshot(self):
        link = Link.objects.get(guid='ABCD-0007')
        self.assertTrue(link.capture_job.status == 'completed')
        self.assertTrue(link.captures.count())
        with patch('perma.models.default_storage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'ABCD-0007'}}, request_kwargs={'follow': True})
            self.assertEqual(response.request.get('QUERY_STRING'), 'type=image')
            self.assertIn('memento-datetime', response._headers)
            self.assertIn('link', response._headers)

    # patch default storage so that it returns a sample warc
    def test_dark_archive(self):
        with patch('perma.models.default_storage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            response = self.get('single_permalink', reverse_kwargs={'kwargs':{'guid': 'ABCD-0001'}}, require_status_code=403)
            self.assertIn(b"This record is private and cannot be displayed.", response.content)
            self.assertNotIn('memento-datetime', response._headers)
            self.assertNotIn('link', response._headers)

            # check that top bar is displayed to logged-in users
            for user in self.users:
                self.log_in_user(user)
                response = self.get('single_permalink', reverse_kwargs={'kwargs': {'guid': 'ABCD-0001'}})
                self.assertIn(b"This record is private.", response.content)
                self.assertNotIn('memento-datetime', response._headers)
                self.assertNotIn('link', response._headers)

    def test_redirect_to_download(self):
        with patch('perma.models.default_storage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
            # Give user option to download to view pdf if on mobile
            link = Link.objects.get(pk='7CF8-SS4G')

            file_url = "im_/" + link.captures.filter(role='primary').get().url

            client = Client(HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 6_1_4 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10B350 Safari/8536.25')
            response = client.get(reverse('single_permalink', kwargs={'guid': link.guid}))
            self.assertIn(b"Perma.cc can\'t display this file type on mobile", response.content)

            # Make sure that we're including the archived capture url
            self.assertIn(bytes(file_url, 'utf-8'), response.content)

            # If not on mobile, display link as normal
            client = Client(HTTP_USER_AGENT='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/601.7.7 (KHTML, like Gecko) Version/9.1.2 Safari/601.7.7')
            response = client.get(reverse('single_permalink', kwargs={'guid': link.guid}))
            self.assertNotIn(b"Perma.cc can\'t display this file type on mobile", response.content)

    def test_deleted(self):
        response = self.get('single_permalink', reverse_kwargs={'kwargs': {'guid': 'ABCD-0003'}}, require_status_code=410, request_kwargs={'follow': True})
        self.assertIn(b"This record has been deleted.", response.content)
        self.assertNotIn('memento-datetime', response._headers)
        self.assertNotIn('link', response._headers)

    def test_misformatted_nonexistent_links_404(self):
        response = self.client.get(reverse('single_permalink', kwargs={'guid': 'JJ99--JJJJ'}))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('single_permalink', kwargs={'guid': '988-JJJJ=JJJJ'}))
        self.assertEqual(response.status_code, 404)

    def test_properly_formatted_nonexistent_links_404(self):
        response = self.client.get(reverse('single_permalink', kwargs={'guid': 'JJ99-JJJJ'}))
        self.assertEqual(response.status_code, 404)

        # Test the original ID style. We shouldn't get a redirect.
        response = self.client.get(reverse('single_permalink', kwargs={'guid': '0J6pkzDeQwT'}))
        self.assertEqual(response.status_code, 404)

    def test_replacement_link(self):
        response = self.client.get(reverse('single_permalink', kwargs={'guid': 'ABCD-0006'}))
        self.assertRedirects(response, reverse('single_permalink', kwargs={'guid': '3SLN-JHX9'}), fetch_redirect_response=False)


    ###
    ### Memento
    ###
    def test_timemap_json(self):
        response = self.client.get(reverse('timemap', args=['json', 'wikipedia.org']))
        self.assertEqual(response._headers['content-type'][1], 'application/json')
        self.assertEqual(response._headers['x-memento-count'][1], '3')
        self.assertEqual(response.json(), {
            'self': 'http://testserver/timemap/json/wikipedia.org',
            'original_uri': 'wikipedia.org',
            'timegate_uri': 'http://testserver/timegate/wikipedia.org',
            'timemap_uri': {
                'json_format': 'http://testserver/timemap/json/wikipedia.org',
                'link_format': 'http://testserver/timemap/link/wikipedia.org',
                'html_format': 'http://testserver/timemap/html/wikipedia.org'
            },
            'mementos': {
                'first': {'uri': 'http://testserver/ABCD-0007', 'datetime': '2014-07-19T20:21:31Z'},
                'last': {'uri': 'http://testserver/ABCD-0009', 'datetime': '2016-07-19T20:21:31Z'},
                'list': [
                    {'uri': 'http://testserver/ABCD-0007', 'datetime': '2014-07-19T20:21:31Z'},
                    {'uri': 'http://testserver/ABCD-0008', 'datetime': '2015-07-19T20:21:31Z'},
                    {'uri': 'http://testserver/ABCD-0009', 'datetime': '2016-07-19T20:21:31Z'}
                ]
            }
        })

    def test_timemap_link(self):
        response = self.client.get(reverse('timemap', args=['link', 'wikipedia.org']))
        self.assertEqual(response._headers['content-type'][1], 'application/link-format')
        self.assertEqual(response._headers['x-memento-count'][1], '3')
        expected =b"""\
<wikipedia.org>; rel=original,
<http://testserver/timegate/wikipedia.org>; rel=timegate,
<http://testserver/timemap/link/wikipedia.org>; rel=self; type=application/link-format,
<http://testserver/timemap/link/wikipedia.org>; rel=timemap; type=application/link-format,
<http://testserver/timemap/json/wikipedia.org>; rel=timemap; type=application/json,
<http://testserver/timemap/html/wikipedia.org>; rel=timemap; type=text/html,
<http://testserver/ABCD-0007>; rel=memento; datetime="Sat, 19 Jul 2014 20:21:31 GMT",
<http://testserver/ABCD-0008>; rel=memento; datetime="Sun, 19 Jul 2015 20:21:31 GMT",
<http://testserver/ABCD-0009>; rel=memento; datetime="Tue, 19 Jul 2016 20:21:31 GMT",
"""
        self.assertEqual(response.content, expected)

    def test_timemap_not_found_standard(self):
        for response_type in ['link', 'json']:
            response = self.client.get(reverse('timemap', args=[response_type, 'wikipedia.org?foo=bar']))
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response._headers['x-memento-count'][1], '0')
            self.assertEqual(response.content, b'404 page not found\n')

    def test_timemap_not_found_html(self):
        response = self.client.get(reverse('timemap', args=['html', 'wikipedia.org?foo=bar']))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response._headers['x-memento-count'][1], '0')
        self.assertIn(b'<i>No captures found for <b>wikipedia.org?foo=bar</b></i>', response.content)

    def test_timegate_most_recent(self):
        response = self.client.get(reverse('timegate', args=['wikipedia.org']))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response._headers['location'][1], 'http://testserver/ABCD-0009')
        self.assertIn('accept-datetime', response._headers['vary'][1])
        self.assertIn('<http://testserver/ABCD-0007>; rel="first memento"; datetime="Sat, 19 Jul 2014 20:21:31 GMT"', response._headers['link'][1])
        self.assertIn('<http://testserver/ABCD-0009>; rel="last memento"; datetime="Tue, 19 Jul 2016 20:21:31 GMT"', response._headers['link'][1])
        self.assertIn('<http://testserver/ABCD-0009>; rel=memento; datetime="Tue, 19 Jul 2016 20:21:31 GMT"', response._headers['link'][1])
        self.assertIn('<wikipedia.org>; rel=original,', response._headers['link'][1])
        self.assertIn('<http://testserver/timegate/wikipedia.org>; rel=timegate,', response._headers['link'][1])
        self.assertIn('<http://testserver/timemap/link/wikipedia.org>; rel=timemap; type=application/link-format,', response._headers['link'][1])
        self.assertIn('<http://testserver/timemap/json/wikipedia.org>; rel=timemap; type=application/json,', response._headers['link'][1])
        self.assertIn('<http://testserver/timemap/html/wikipedia.org>; rel=timemap; type=text/html,', response._headers['link'][1])

    def test_timegate_with_target_date(self):
        response = self.client.get(reverse('timegate', args=['wikipedia.org']), HTTP_ACCEPT_DATETIME='Thu, 26 Jul 2015 20:21:31 GMT')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response._headers['location'][1], 'http://testserver/ABCD-0008')
        self.assertIn('accept-datetime', response._headers['vary'][1])
        self.assertIn('<http://testserver/ABCD-0007>; rel="first memento"; datetime="Sat, 19 Jul 2014 20:21:31 GMT"', response._headers['link'][1])
        self.assertIn('<http://testserver/ABCD-0009>; rel="last memento"; datetime="Tue, 19 Jul 2016 20:21:31 GMT"', response._headers['link'][1])
        self.assertIn('<http://testserver/ABCD-0008>; rel=memento; datetime="Sun, 19 Jul 2015 20:21:31 GMT"', response._headers['link'][1])
        self.assertIn('<wikipedia.org>; rel=original,', response._headers['link'][1])
        self.assertIn('<http://testserver/timegate/wikipedia.org>; rel=timegate,', response._headers['link'][1])
        self.assertIn('<http://testserver/timemap/link/wikipedia.org>; rel=timemap; type=application/link-format,', response._headers['link'][1])
        self.assertIn('<http://testserver/timemap/json/wikipedia.org>; rel=timemap; type=application/json,', response._headers['link'][1])
        self.assertIn('<http://testserver/timemap/html/wikipedia.org>; rel=timemap; type=text/html,', response._headers['link'][1])

    def test_timegate_not_found(self):
        response = self.client.get(reverse('timegate', args=['wikipedia.org?foo=bar']))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, b'404 page not found\n')


    ###
    ###   Does the contact form render as expected?
    ###

    def test_contact_blank_when_logged_out(self):
        '''
            Check correct fields are blank for logged out user
        '''
        response = self.get('contact').content
        soup = BeautifulSoup(response, 'html.parser')
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 4)
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'referer', 'email', 'subject'])
            if input['name'] == 'csrfmiddlewaretoken':
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))
        textareas = soup.select('textarea')
        self.assertEqual(len(textareas), 2)
        for textarea in textareas:
            self.assertIn(textarea['name'],['box1', 'box2'])
            self.assertEqual(textarea.text.strip(), "")

    def test_contact_blank_regular(self):
        '''
            Check correct fields are blank for regular user
        '''
        response = self.get('contact', user="test_user@example.com").content
        soup = BeautifulSoup(response, 'html.parser')
        inputs = soup.select('input')
        # Two csrf inputs: one by logout button, one in this form
        self.assertEqual(len(inputs), 4 + 1)
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'referer', 'email', 'subject'])
            if input['name'] in ['csrfmiddlewaretoken', 'email']:
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))
        textareas = soup.select('textarea')
        self.assertEqual(len(textareas), 2)
        for textarea in textareas:
            self.assertIn(textarea['name'],['box1', 'box2'])
            self.assertEqual(textarea.text.strip(), "")

    def test_contact_blank_registrar(self):
        '''
            Check correct fields are blank for registrar user
        '''
        response = self.get('contact', user="test_registrar_user@example.com").content
        soup = BeautifulSoup(response, 'html.parser')
        inputs = soup.select('input')
        # Two csrf inputs: one by logout button, one in this form
        self.assertEqual(len(inputs), 4 + 1)
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'referer', 'email', 'subject'])
            if input['name'] in ['csrfmiddlewaretoken', 'email']:
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))
        textareas = soup.select('textarea')
        self.assertEqual(len(textareas), 2)
        for textarea in textareas:
            self.assertIn(textarea['name'],['box1', 'box2'])
            self.assertEqual(textarea.text.strip(), "")

    def test_contact_blank_single_reg_org_user(self):
        '''
            Check correct fields are blank for a single-registrar org user
        '''
        response = self.get('contact', user="test_org_user@example.com").content
        soup = BeautifulSoup(response, 'html.parser')
        inputs = soup.select('input')
        # Two csrf inputs: one by logout button, one in this form
        self.assertEqual(len(inputs), 5 + 1)
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'referer', 'email', 'subject', 'registrar'])
            if input['name'] in ['csrfmiddlewaretoken', 'email', 'registrar']:
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))
        textareas = soup.select('textarea')
        self.assertEqual(len(textareas), 2)
        for textarea in textareas:
            self.assertIn(textarea['name'],['box1', 'box2'])
            self.assertEqual(textarea.text.strip(), "")

    def test_contact_blank_multi_reg_org_user(self):
        '''
            Check correct fields are blank for a multi-registrar org user
        '''
        response = self.get('contact', user="multi_registrar_org_user@example.com").content
        soup = BeautifulSoup(response, 'html.parser')
        inputs = soup.select('input')
        # Two csrf inputs: one by logout button, one in this form
        self.assertEqual(len(inputs), 4 + 1)
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'referer', 'email', 'subject'])
            if input['name'] in ['csrfmiddlewaretoken', 'email']:
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))
        textareas = soup.select('textarea')
        self.assertEqual(len(textareas), 2)
        for textarea in textareas:
            self.assertIn(textarea['name'],['box1', 'box2'])
            self.assertEqual(textarea.text.strip(), "")
        selects = soup.select('select')
        self.assertEqual(len(selects), 1)
        for select in selects:
            self.assertIn(select['name'],['registrar'])
            self.assertGreaterEqual(len(select.find_all("option")), 2)

    def check_contact_params(self, soup):
        subject_field = soup.find('input', {'name': 'subject'})
        self.assertEqual(subject_field.get('value', ''), self.custom_subject)
        message_field = soup.find('textarea', {'name': 'box2'})
        self.assertEqual(message_field.text.strip(), self.message_text)

    def test_contact_params_regular(self):
        '''
            Check subject line, message, read in from GET params
        '''
        for user in self.users + [None]:
            response = self.get('contact', query_params={ 'message': self.message_text,
                                                          'subject': self.custom_subject, },
                                           user=user).content
            self.check_contact_params(BeautifulSoup(response, 'html.parser'))

    def check_contact_flags(self, soup):
        subject_field = soup.find('input', {'name': 'subject'})
        self.assertEqual(subject_field.get('value', ''), self.flag_subject)
        message_field = soup.find('textarea', {'name': 'box2'})
        self.assertEqual(message_field.text.strip(), self.flag_message)

    def test_contact_flags(self):
        '''
            Check flag read in from GET params, and that its subject/message override other GET params
        '''
        for user in self.users + [None]:
            response = self.get('contact', query_params={ 'flag': self.flag,
                                                          'message': self.message_text,
                                                          'subject': self.custom_subject },
                                           user=user).content
            self.check_contact_flags(BeautifulSoup(response, 'html.parser'))


    ###
    ###   Does the contact form submit as expected?
    ###

    def test_contact_standard_submit_fail(self):
        '''
            Blank submission should fail and, for most users, request
            email address and message.
            We should get the contact page back.
        '''
        response = self.submit_form('contact',
                                     data = { 'email': '',
                                              'box2': '' },
                                     error_keys = ['email', 'box2'])
        self.assertEqual(response.request['PATH_INFO'], reverse('contact'))

    def test_contact_org_user_submit_fail(self):
        '''
            Org users are special. Blank submission should fail
            and request email address, message, and registrar.
            We should get the contact page back.
        '''
        response = self.submit_form('contact',
                                     data = { 'email': '',
                                              'box2': '' },
                                     user='test_org_user@example.com',
                                     error_keys = ['email', 'box2', 'registrar'])
        self.assertEqual(response.request['PATH_INFO'], reverse('contact'))

    def test_contact_standard_submit_required(self):
        '''
            All fields, including custom subject and referer
        '''
        self.submit_form('contact',
                          data = { 'email': self.from_email,
                                   'box2': self.message_text,
                                   'subject': self.custom_subject,
                                   'referer': self.refering_page },
                          success_url=reverse('contact_thanks'))

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(self.message_text, message.body)
        self.assertIn("Referring Page: " + self.refering_page, message.body)
        self.assertIn("Affiliations: (none)", message.body)
        self.assertIn("Logged in: false", message.body)
        self.assertEqual(message.subject, self.subject_prefix + self.custom_subject)
        self.assertEqual(message.from_email, self.our_address)
        self.assertEqual(message.recipients(), [self.our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': self.from_email})

    def test_contact_standard_submit_required_with_spam_catcher(self):
        '''
            All fields, including custom subject and referer
        '''
        self.submit_form('contact',
                          data = { 'email': self.from_email,
                                   'box1': "I'm a bot",
                                   'box2': self.message_text,
                                   'subject': self.custom_subject,
                                   'referer': self.refering_page },
                          success_url=reverse('contact_thanks'))

        self.assertEqual(len(mail.outbox), 0)

    def test_contact_standard_submit_no_optional(self):
        '''
            All fields except custom subject and referer
        '''
        self.submit_form('contact',
                          data = { 'email': self.from_email,
                                   'box2': self.message_text },
                          success_url=reverse('contact_thanks'))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(self.message_text, message.body)
        self.assertIn("Referring Page: ", message.body)
        self.assertIn("Affiliations: (none)", message.body)
        self.assertIn("Logged in: false", message.body)
        self.assertEqual(message.subject, self.subject_prefix + 'New message from Perma contact form')
        self.assertEqual(message.from_email, self.our_address )
        self.assertEqual(message.recipients(), [self.our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': self.from_email})

    def test_contact_org_user_submit_invalid(self):
        '''
            Org users get extra fields. Registrar must be a valid choice.
            We should get the contact page back.
        '''
        response = self.submit_form('contact',
                                     data = { 'email': self.from_email,
                                              'box2': self.message_text,
                                              'registrar': 'not_a_licit_registrar_id'},
                                     user='test_org_user@example.com',
                                     error_keys = ['registrar'])
        self.assertEqual(response.request['PATH_INFO'], reverse('contact'))

    def test_contact_org_user_submit(self):
        '''
            Should be sent to registrar users.
        '''
        registrar = Registrar.objects.get(email='library@university.edu')
        registrar_users = registrar.active_registrar_users()
        success = reverse('contact_thanks') + "?{}".format(urlencode({'registrar': registrar.id}))
        expected_emails = 0
        for user in ['test_org_user@example.com', 'multi_registrar_org_user@example.com']:
            self.submit_form('contact',
                              data = { 'email': self.from_email,
                                       'box2': self.message_text,
                                       'registrar': registrar.id },
                              user=user,
                              success_url=success)

            expected_emails +=1
            self.assertEqual(len(mail.outbox), expected_emails)
            message = mail.outbox[expected_emails -1]
            self.assertIn(self.message_text, message.body)
            self.assertIn("Logged in: true", message.body)
            self.assertEqual(message.from_email, self.our_address )
            self.assertEqual(message.to, [user.email for user in registrar_users])
            self.assertEqual(message.cc, [self.our_address, self.from_email] )
            self.assertEqual(message.reply_to, [self.from_email])

    def test_contact_org_user_affiliation_string(self):
        '''
            Verify org affiliations are printed correctly
        '''
        self.submit_form('contact',
                          data = { 'email': self.from_email,
                                   'box2': self.message_text,
                                   'registrar': 2 },
                          user='test_another_library_org_user@example.com')
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn("Affiliations: Another Library's Journal (Another Library), A Third Journal (Test Library)", message.body)
        self.assertIn("Logged in: true", message.body)

    def test_contact_reg_user_affiliation_string(self):
        '''
            Verify registrar affiliations are printed correctly
        '''
        self.submit_form('contact',
                          data = { 'email': self.from_email,
                                   'box2': self.message_text },
                          user='test_registrar_user@example.com')
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn("Affiliations: Test Library (Registrar)", message.body)
        self.assertIn("Logged in: true", message.body)


    def test_about_partner_list(self):
        '''
            Is the partner list populated, and split evenly into 2 columns?
        '''
        response = self.get('about').content
        soup = BeautifulSoup(response, 'html.parser')
        partner_columns = soup.find('div', {'class':'partner-list'}).find_all('div', recursive=False)
        self.assertEqual(len(partner_columns), 2)
        first_partners = partner_columns[0].select('.perma-partner')
        self.assertTrue(partner.text for partner in first_partners)
        second_partners = partner_columns[1].select('.perma-partner')
        self.assertTrue(partner.text for partner in second_partners)
        first_partners = partner_columns[0].select('.perma-partner')
        self.assertTrue(len(first_partners) == len(second_partners) or
                        len(first_partners) == len(second_partners) + 1)
