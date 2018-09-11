from django.conf import settings
from django.core import mail
from django.db.models.query import QuerySet
from django.http import HttpRequest

from perma.email import registrar_users_plus_stats, send_user_email_copy_admins
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
