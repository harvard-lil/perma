from django.test.client import RequestFactory

from perma.utils import *

from .utils import PermaTestCase

class UtilsTestCase(PermaTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_client_ip(self):
        request = self.factory.get('/some/route', REMOTE_ADDR="1.2.3.4")
        self.assertEqual(get_client_ip(request), "1.2.3.4")

    # perma-payments

    def test_pack_and_unpack_data(self):
        data = {'a': "a", 'b': "b"}
        self.assertEqual(unpack_data(pack_data(data)), data)

    def test_is_valid_timestamp(self):
        max_age = 60
        now = to_timestamp(datetime.utcnow())
        still_valid = to_timestamp(datetime.utcnow() + timedelta(seconds=max_age))
        invalid = to_timestamp(datetime.utcnow() + timedelta(seconds=max_age * 2))
        self.assertTrue(is_valid_timestamp(now, max_age))
        self.assertTrue(is_valid_timestamp(still_valid, max_age))
        self.assertFalse(is_valid_timestamp(invalid, max_age))

    def test_perma_payments_encrypt_and_decrypt(self):
        message = u'hi there'
        ci = encrypt_for_perma_payments(message.encode('utf-8'))
        self.assertEqual(decrypt_from_perma_payments(ci).decode('utf-8'), message)
