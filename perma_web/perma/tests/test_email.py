import random
from createsend import Subscriber
from mock import patch, Mock

from django.db.models.query import QuerySet

from perma.email import registrar_users_plus_stats, users_to_unsubscribe
from perma.models import LinkUser

from .utils import PermaTestCase

class EmailTestCase(PermaTestCase):

    def test_registrar_users_plus_stats(self):
        '''
            Returns data in the expected format.
        '''
        r_list = registrar_users_plus_stats()
        self.assertEqual(type(r_list), list)
        for user in r_list:
            self.assertEqual(type(user), dict)
            expected_keys = [ 'email',
                              'first_name',
                              'last_name',
                              'registrar_email',
                              'registrar_name',
                              'registrar_users',
                              'total_links' ]
            self.assertEqual(sorted(user.keys()), expected_keys)
            for key in ['email', 'first_name', 'last_name', 'registrar_email', 'registrar_name']:
                self.assertEqual(type(user[key]), unicode)
                self.assertTrue(user[key])
            perma_user = LinkUser.objects.get(email=user['email'])
            self.assertTrue(perma_user.registrar)
            self.assertTrue(perma_user.is_active)
            self.assertTrue(perma_user.is_confirmed)
            self.assertEqual(type(user['total_links']), long)
            self.assertEqual(type(user['registrar_users']), QuerySet)
            self.assertGreaterEqual(len(user['registrar_users']), 1)
            for user in user['registrar_users']:
                self.assertEqual(type(user), LinkUser)

    def test_registrar_users_plus_stats_cm(self):
        '''
            Returns data in the expected format for Campaign Monitor.
        '''
        r_list = registrar_users_plus_stats(destination="cm")
        self.assertEqual(type(r_list), list)
        for user in r_list:
            self.assertEqual(type(user), dict)
            self.assertEqual(sorted(user.keys()), ['CustomFields','EmailAddress','Name' ])
            for key in ['Name', 'EmailAddress']:
                self.assertEqual(type(user[key]), unicode)
                self.assertTrue(user[key])
            self.assertEqual(type(user['CustomFields']), list)
            self.assertEqual(len(user['CustomFields']), 4)
            custom_field_list = [ 'RegistrarEmail',
                                  'RegistrarName',
                                  'RegistrarUsers',
                                  'TotalLinks' ]
            for custom_field in user['CustomFields']:
                self.assertEqual(type(custom_field), dict)
                self.assertEqual(sorted(custom_field.keys()), ['Key', 'Value'])
                self.assertIn(custom_field['Key'], custom_field_list)
                self.assertEqual(type(custom_field['Value']), unicode)
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
        self.assertEqual(type(results), list)
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
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)
        for subscriber in results:
            self.assertEqual(type(subscriber), str)
            self.assertIn('@', subscriber)
        results = users_to_unsubscribe('1', ['subscriber@example.com'])
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)
        results = users_to_unsubscribe('1', ['subscriber1@example.com'])
        self.assertEqual(type(results), list)
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
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 6)
        for subscriber in results:
            self.assertEqual(type(subscriber), str)
            self.assertIn('@', subscriber)
        results = users_to_unsubscribe('1', ['sdhjfkhsdjhfs@example.com'])
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 6)
        results = users_to_unsubscribe('1', ['known@example.com'])
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 3)




