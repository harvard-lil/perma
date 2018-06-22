import random
from createsend import Subscriber
from mock import patch, Mock

from django.conf import settings
from django.core import mail
from django.db.models.query import QuerySet
from django.http import HttpRequest

from perma.email import registrar_users_plus_stats, users_to_unsubscribe, send_user_email_copy_admins
from perma.models import LinkUser, Organization, Registrar

from .utils import PermaTestCase

class EmailTestCase(PermaTestCase):

    def test_send_user_email_copy_admins(self):
        send_user_email_copy_admins(
            "title",
            "from@example.com",
            ["to@example.com"],
            HttpRequest(),
            "email/default.txt",
            {"message": "test message"}
        )
        self.assertEqual(len(mail.outbox),1)
        message = mail.outbox[0]
        self.assertEqual(message.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(message.cc, [settings.DEFAULT_FROM_EMAIL, "from@example.com"])
        self.assertEqual(message.to, ["to@example.com"])
        self.assertEqual(message.reply_to, ["from@example.com"])

    def test_registrar_users_plus_stats(self):
        '''
            Returns data in the expected format.
        '''
        r_list = registrar_users_plus_stats()
        self.assertIsInstance(r_list, list)
        self.assertGreater(len(r_list), 0)
        for user in r_list:
            self.assertIsInstance(user, dict)
            expected_keys = [ 'email',
                              'first_name',
                              'last_name',
                              'most_active_org',
                              'registrar_email',
                              'registrar_id',
                              'registrar_name',
                              'registrar_users',
                              'total_links',
                              'year_links' ]
            self.assertEqual(sorted(user.keys()), expected_keys)
            for key in ['email', 'first_name', 'last_name', 'registrar_email', 'registrar_name']:
                self.assertIsInstance(user[key], str)
                self.assertTrue(user[key])
            perma_user = LinkUser.objects.get(email=user['email'])
            self.assertTrue(perma_user.registrar)
            self.assertTrue(perma_user.is_active)
            self.assertTrue(perma_user.is_confirmed)
            self.assertIsInstance(user['total_links'], int)
            self.assertIsInstance(user['year_links'], int)
            self.assertIsInstance(user['registrar_id'], int)
            self.assertIsInstance(user['most_active_org'], (Organization, type(None)))
            self.assertIsInstance(user['registrar_users'], QuerySet)
            self.assertGreaterEqual(len(user['registrar_users']), 1)
            for user in user['registrar_users']:
                self.assertIsInstance(user, LinkUser)

    def test_registrar_users_plus_stats_specific_registrars(self):
        '''
            Returns data in the expected format.
        '''
        r_list = registrar_users_plus_stats(registrars=Registrar.objects.filter(email='library@university.edu'))
        self.assertIsInstance(r_list, list)
        self.assertEqual(len(r_list), 1)
        self.assertEqual(r_list[0]['registrar_email'], 'library@university.edu')

    def test_registrar_users_plus_stats_cm(self):
        '''
            Returns data in the expected format for Campaign Monitor.
        '''
        r_list = registrar_users_plus_stats(destination="cm")
        self.assertIsInstance(r_list, list)
        self.assertGreater(len(r_list), 0)
        for user in r_list:
            self.assertIsInstance(user, dict)
            self.assertEqual(sorted(user.keys()), ['CustomFields', 'EmailAddress', 'Name'])
            for key in ['Name', 'EmailAddress']:
                self.assertIsInstance(user[key], str)
                self.assertTrue(user[key])
            self.assertIsInstance(user['CustomFields'], list)
            self.assertEqual(len(user['CustomFields']), 7)
            custom_field_list = [ 'MostActiveOrg',
                                  'RegistrarId',
                                  'RegistrarEmail',
                                  'RegistrarName',
                                  'RegistrarUsers',
                                  'YearLinks',
                                  'TotalLinks' ]
            for custom_field in user['CustomFields']:
                self.assertIsInstance(custom_field, dict)
                self.assertEqual(sorted(custom_field.keys()), ['Key', 'Value'])
                self.assertIn(custom_field['Key'], custom_field_list)
                self.assertIsInstance(custom_field['Value'], str)
                self.assertTrue(custom_field['Value'])
            perma_user = LinkUser.objects.get(email=user['EmailAddress'])
            self.assertTrue(perma_user.registrar)
            self.assertTrue(perma_user.is_active)
            self.assertTrue(perma_user.is_confirmed)


    @patch('perma.email.List', autospec=True)
    def test_users_to_unsubscribe_empty(self, MockList):
        '''
            If CM returns no subscribers, we should get an empty list.
        '''
        MockList().active.return_value = Mock(NumberOfPages=0, Results=[])
        results = users_to_unsubscribe('1', [])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    @patch('perma.email.List', autospec=True)
    def test_users_to_unsubscribe_one_page(self, MockList):
        '''
            If CM returns a list of subscribers, we should get a list of
            email addresses that appear in their list,
        '''
        s1 = Mock(EmailAddress='subscriber1@example.com', autospec=Subscriber)
        s2 = Mock(EmailAddress='subscriber2@example.com', autospec=Subscriber)
        MockList().active.return_value = Mock( NumberOfPages=1,
                                               PageNumber=1,
                                               Results=[s1, s2] )
        results = users_to_unsubscribe('1', [])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        for subscriber in results:
            self.assertIsInstance(subscriber, str)
            self.assertIn('@', subscriber)
        results = users_to_unsubscribe('1', ['subscriber@example.com'])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        results = users_to_unsubscribe('1', ['subscriber1@example.com'])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)

    @patch('perma.email.List', autospec=True)
    def test_users_to_unsubscribe_multi_pages(self, MockList):
        '''
            If CM returns a list of subscribers, we should get a list of
            email addresses that appear in their list,
        '''
        def random_subscribers(page=1, *args, **kwargs):
            unknown = Mock(EmailAddress='subscriber{}@example.com'.format(random.random()), autospec=Subscriber)
            known = Mock(EmailAddress='known@example.com', autospec=Subscriber)
            return Mock(NumberOfPages=3,
                        PageNumber=page,
                        Results=[unknown, known])

        MockList().active.side_effect = random_subscribers
        results = users_to_unsubscribe('1', [])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 6)
        for subscriber in results:
            self.assertIsInstance(subscriber, str)
            self.assertIn('@', subscriber)
        results = users_to_unsubscribe('1', ['sdhjfkhsdjhfs@example.com'])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 6)
        results = users_to_unsubscribe('1', ['known@example.com'])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 3)
