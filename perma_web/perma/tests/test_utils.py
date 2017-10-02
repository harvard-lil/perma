import decimal
from django.test.client import RequestFactory
from mock import patch, sentinel

from hypothesis import given
from hypothesis.strategies import characters, text, integers, booleans, datetimes, dates, decimals, uuids, binary, dictionaries

from perma.utils import *

from .utils import PermaTestCase, SentinelException

# Fixtures

def spoof_perma_payments_post():
    data = {
        'encrypted_data': {"timestamp": 1504884268.560902, "desired_field": "desired_field"},
    }
    assert 'encrypted_data' in data
    assert 'timestamp' in data['encrypted_data']
    assert 'desired_field' in data['encrypted_data']
    return data


def one_two_three_dict():
    data = {
        'one': 'one',
        'two': 'two',
        'three': 'three'
    }
    assert 'one' in data
    assert 'two' in data
    assert 'three' in data
    assert 'four' not in data
    return data


# Tests

class UtilsTestCase(PermaTestCase):

    def setUp(self):
        self.factory = RequestFactory()


    def test_get_client_ip(self):
        request = self.factory.get('/some/route', REMOTE_ADDR="1.2.3.4")
        self.assertEqual(get_client_ip(request), "1.2.3.4")


    # communicate with perma payments

    @patch('perma.utils.encrypt_for_perma_payments', autospec=True)
    @patch('perma.utils.stringify_data', autospec=True)
    def test_prep_for_perma_payments(self, stringify, encrypt):
        stringify.return_value = sentinel.stringified
        encrypt.return_value = sentinel.encrypted

        assert prep_for_perma_payments({}) == sentinel.encrypted
        stringify.assert_called_once_with({})
        encrypt.assert_called_once_with(sentinel.stringified)


    def test_process_perma_payments_transmission_encrypted_data_not_in_post(self):
        with self.assertRaises(InvalidTransmissionException) as excinfo:
            assert process_perma_payments_transmission({}, [])
        assert 'No encrypted_data in POST.' in str(excinfo.exception)


    def test_process_perma_payments_transmission_encrypted_data_none(self):
        with self.assertRaises(InvalidTransmissionException) as excinfo:
            assert process_perma_payments_transmission({'encrypted_data': None}, [])
        assert 'No encrypted_data in POST.' in str(excinfo.exception)


    def test_process_perma_payments_transmission_encrypted_data_empty(self):
        with self.assertRaises(InvalidTransmissionException) as excinfo:
            assert process_perma_payments_transmission({'encrypted_data': ''}, [])
        assert 'No encrypted_data in POST.' in str(excinfo.exception)


    @patch('perma.utils.decrypt_from_perma_payments', autospec=True)
    def test_process_perma_payments_transmission_encryption_problem(self, decrypt):
        decrypt.side_effect = SentinelException
        with self.assertRaises(InvalidTransmissionException) as excinfo:
            process_perma_payments_transmission(spoof_perma_payments_post(), [])
        assert 'SentinelException' in str(excinfo.exception)
        assert decrypt.call_count == 1


    @patch('perma.utils.unstringify_data', autospec=True)
    @patch('perma.utils.decrypt_from_perma_payments', autospec=True)
    def test_process_perma_payments_transmission_not_valid_json(self, decrypt, unstringify):
        unstringify.side_effect = SentinelException
        with self.assertRaises(InvalidTransmissionException) as excinfo:
            process_perma_payments_transmission(spoof_perma_payments_post(), [])
        assert 'SentinelException' in str(excinfo.exception)
        assert unstringify.call_count == 1


    @patch('perma.utils.unstringify_data', autospec=True)
    @patch('perma.utils.decrypt_from_perma_payments', autospec=True)
    def test_process_perma_payments_transmission_missing_timestamp(self, decrypt, unstringify):
        post = spoof_perma_payments_post()
        del post['encrypted_data']['timestamp']
        unstringify.return_value = post['encrypted_data']
        with self.assertRaises(InvalidTransmissionException) as excinfo:
            process_perma_payments_transmission(post, [])
        assert 'Missing timestamp in data.' in str(excinfo.exception)

    @patch('perma.utils.is_valid_timestamp', autospec=True)
    @patch('perma.utils.unstringify_data', autospec=True)
    @patch('perma.utils.decrypt_from_perma_payments', autospec=True)
    def test_process_perma_payments_transmission_expired_timestamp(self, decrypt, unstringify, timestamp):
        post = spoof_perma_payments_post()
        unstringify_data.return_value = post['encrypted_data']
        timestamp.return_value = False
        with self.assertRaises(InvalidTransmissionException) as excinfo:
            process_perma_payments_transmission(post, [])
        assert 'Expired timestamp in data.' in str(excinfo.exception)


    @patch('perma.utils.is_valid_timestamp', autospec=True)
    @patch('perma.utils.unstringify_data', autospec=True)
    @patch('perma.utils.decrypt_from_perma_payments', autospec=True)
    def test_process_perma_payments_transmission_happy_path(self, decrypt, unstringify, timestamp):
        post = spoof_perma_payments_post()
        decrypt.return_value = sentinel.decrypted
        unstringify.return_value = post['encrypted_data']
        timestamp.return_value = True

        assert process_perma_payments_transmission(post, ['desired_field']) == {'desired_field': 'desired_field'}

        decrypt.assert_called_once_with(post['encrypted_data'])
        unstringify.assert_called_once_with(sentinel.decrypted)
        timestamp.assert_called_once_with(post['encrypted_data']['timestamp'], settings.PERMA_PAYMENTS_TIMESTAMP_MAX_AGE_SECONDS)


    # perma-payments helpers

    def test_retrieve_fields_returns_only_specified_fields(self):
        one_two_three = one_two_three_dict()
        assert retrieve_fields(one_two_three, ['one']) == {'one': 'one'}
        assert retrieve_fields(one_two_three, ['two']) == {'two': 'two'}
        assert retrieve_fields(one_two_three, ['one', 'three']) == {'one': 'one', 'three': 'three'}


    def test_retrieve_fields_raises_if_field_absent(self):
        one_two_three = one_two_three_dict()
        with self.assertRaises(InvalidTransmissionException):
            retrieve_fields(one_two_three, ['four'])


    def test_is_valid_timestamp(self):
        max_age = 60
        now = to_timestamp(datetime.utcnow())
        still_valid = to_timestamp(datetime.utcnow() + timedelta(seconds=max_age))
        invalid = to_timestamp(datetime.utcnow() + timedelta(seconds=max_age * 2))
        self.assertTrue(is_valid_timestamp(now, max_age))
        self.assertTrue(is_valid_timestamp(still_valid, max_age))
        self.assertFalse(is_valid_timestamp(invalid, max_age))


    preserved = text(alphabet=characters(min_codepoint=1, blacklist_categories=('Cc', 'Cs'))) | integers() | booleans()
    @given(preserved | dictionaries(keys=text(alphabet=characters(min_codepoint=1, blacklist_categories=('Cc', 'Cs'))), values=preserved))
    def test_stringify_and_unstringify_data_types_preserved(self, data):
        assert unstringify_data(stringify_data(data)) == data


    oneway = decimals(places=2, min_value=decimal.Decimal(0.00), allow_nan=False, allow_infinity=False) | datetimes() | dates() | uuids()
    @given(oneway | dictionaries(keys=text(alphabet=characters(min_codepoint=1, blacklist_categories=('Cc', 'Cs'))), values=oneway))
    def test_stringify_types_lost(self, data):
        # Some types can be serialized, but not recovered from strings by json.loads.
        # Instead, you have to manually attempt to convert, by field, if you are expecting one of these types.
        #
        # If something can't be serialized, or unserialized,
        # this test will raise an Exception, rather than failing with an assertion error.
        unstringify_data(stringify_data(data))


    @given(binary())
    def test_perma_payments_encrypt_and_decrypt(self, b):
        ci = encrypt_for_perma_payments(b)
        assert decrypt_from_perma_payments(ci) == b

