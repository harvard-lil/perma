from datetime import datetime, timedelta
import decimal
from mock import patch, sentinel

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.test.client import RequestFactory


from hypothesis import given
from hypothesis.strategies import characters, text, integers, booleans, datetimes, dates, decimals, uuids, binary, dictionaries
from perma.utils import (
    AlphaNumericValidator,
    InvalidTransmissionException,
    decrypt_from_perma_payments,
    encrypt_for_perma_payments,
    get_client_ip, prep_for_perma_payments,
    is_valid_timestamp,
    process_perma_payments_transmission,
    retrieve_fields,
    stringify_data,
    unstringify_data
)
import pytest

from .utils import SentinelException


def test_get_client_ip():
    request = RequestFactory().get('/some/route', REMOTE_ADDR="1.2.3.4")
    assert get_client_ip(request) == "1.2.3.4"

#
# our custom password validator
#

def test_lower_upper_number_required():
    validator = AlphaNumericValidator()
    lower ='a'
    upper = 'A'
    number = '1'
    for char in (lower, upper, number):
        with pytest.raises(ValidationError):
            validator.validate('a')
    assert validator.validate(lower+upper+number) is None


def test_custom_validator_in_use():
    lower ='a'
    upper = 'A'
    number = '1'
    padding = 'qwertyuio'
    with pytest.raises(ValidationError):
        validate_password(padding)
    assert validate_password(lower+upper+number+padding) is None


#
# communicate with perma payments
#

@patch('perma.utils.encrypt_for_perma_payments', autospec=True)
@patch('perma.utils.stringify_data', autospec=True)
def test_prep_for_perma_payments(stringify, encrypt):
    stringify.return_value = sentinel.stringified
    encrypt.return_value = sentinel.encrypted

    assert prep_for_perma_payments({}) == sentinel.encrypted
    stringify.assert_called_once_with({})
    encrypt.assert_called_once_with(sentinel.stringified)


def test_process_perma_payments_transmission_encrypted_data_not_in_post():
    with pytest.raises(InvalidTransmissionException) as excinfo:
        assert process_perma_payments_transmission({}, [])
    assert 'No encrypted_data in POST.' in str(excinfo.value)


def test_process_perma_payments_transmission_encrypted_data_none():
    with pytest.raises(InvalidTransmissionException) as excinfo:
        assert process_perma_payments_transmission({'encrypted_data': None}, [])
    assert 'No encrypted_data in POST.' in str(excinfo.value)


def test_process_perma_payments_transmission_encrypted_data_empty():
    with pytest.raises(InvalidTransmissionException) as excinfo:
        assert process_perma_payments_transmission({'encrypted_data': ''}, [])
    assert 'No encrypted_data in POST.' in str(excinfo.value)


@patch('perma.utils.decrypt_from_perma_payments', autospec=True)
def test_process_perma_payments_transmission_encryption_problem(decrypt, spoof_perma_payments_post):
    decrypt.side_effect = SentinelException
    with pytest.raises(InvalidTransmissionException) as excinfo:
        process_perma_payments_transmission(spoof_perma_payments_post, [])
    assert 'SentinelException' in str(excinfo.value)
    assert decrypt.call_count == 1


@patch('perma.utils.unstringify_data', autospec=True)
@patch('perma.utils.decrypt_from_perma_payments', autospec=True)
def test_process_perma_payments_transmission_not_valid_json(decrypt, unstringify, spoof_perma_payments_post):
    unstringify.side_effect = SentinelException
    with pytest.raises(InvalidTransmissionException) as excinfo:
        process_perma_payments_transmission(spoof_perma_payments_post, [])
    assert 'SentinelException' in str(excinfo.value)
    assert unstringify.call_count == 1


@patch('perma.utils.unstringify_data', autospec=True)
@patch('perma.utils.decrypt_from_perma_payments', autospec=True)
def test_process_perma_payments_transmission_missing_timestamp(decrypt, unstringify, spoof_perma_payments_post):
    post = spoof_perma_payments_post
    del post['encrypted_data']['timestamp']
    unstringify.return_value = post['encrypted_data']
    with pytest.raises(InvalidTransmissionException) as excinfo:
        process_perma_payments_transmission(post, [])
    assert 'Missing timestamp in data.' in str(excinfo.value)


@patch('perma.utils.is_valid_timestamp', autospec=True)
@patch('perma.utils.unstringify_data', autospec=True)
@patch('perma.utils.decrypt_from_perma_payments', autospec=True)
def test_process_perma_payments_transmission_expired_timestamp(decrypt, unstringify, timestamp, spoof_perma_payments_post):
    post = spoof_perma_payments_post
    unstringify_data.return_value = post['encrypted_data']
    timestamp.return_value = False
    with pytest.raises(InvalidTransmissionException) as excinfo:
        process_perma_payments_transmission(post, [])
    assert 'Expired timestamp in data.' in str(excinfo.value)


@patch('perma.utils.is_valid_timestamp', autospec=True)
@patch('perma.utils.unstringify_data', autospec=True)
@patch('perma.utils.decrypt_from_perma_payments', autospec=True)
def test_process_perma_payments_transmission_happy_path(decrypt, unstringify, timestamp, spoof_perma_payments_post):
    post = spoof_perma_payments_post
    decrypt.return_value = sentinel.decrypted
    unstringify.return_value = post['encrypted_data']
    timestamp.return_value = True

    assert process_perma_payments_transmission(post, ['desired_field']) == {'desired_field': 'desired_field'}

    decrypt.assert_called_once_with(post['encrypted_data'])
    unstringify.assert_called_once_with(sentinel.decrypted)
    timestamp.assert_called_once_with(post['encrypted_data']['timestamp'], settings.PERMA_PAYMENTS_TIMESTAMP_MAX_AGE_SECONDS)

#
# perma-payments helpers
#

def test_retrieve_fields_returns_only_specified_fields(one_two_three_dict):
    assert retrieve_fields(one_two_three_dict, ['one']) == {'one': 'one'}
    assert retrieve_fields(one_two_three_dict, ['two']) == {'two': 'two'}
    assert retrieve_fields(one_two_three_dict, ['one', 'three']) == {'one': 'one', 'three': 'three'}


def test_retrieve_fields_raises_if_field_absent(one_two_three_dict):
    with pytest.raises(InvalidTransmissionException):
        retrieve_fields(one_two_three_dict, ['four'])


def test_is_valid_timestamp():
    max_age = 60
    now = datetime.utcnow().timestamp()
    still_valid = (datetime.utcnow() + timedelta(seconds=max_age)).timestamp()
    invalid = (datetime.utcnow() + timedelta(seconds=max_age * 2)).timestamp()
    assert is_valid_timestamp(now, max_age)
    assert is_valid_timestamp(still_valid, max_age)
    assert not is_valid_timestamp(invalid, max_age)


preserved = text(alphabet=characters(min_codepoint=1, blacklist_categories=('Cc', 'Cs'))) | integers() | booleans()
@given(preserved | dictionaries(keys=text(alphabet=characters(min_codepoint=1, blacklist_categories=('Cc', 'Cs'))), values=preserved))
def test_stringify_and_unstringify_data_types_preserved(data):
    assert unstringify_data(stringify_data(data)) == data


oneway = decimals(places=2, min_value=decimal.Decimal(0.00), allow_nan=False, allow_infinity=False) | datetimes() | dates() | uuids()
@given(oneway | dictionaries(keys=text(alphabet=characters(min_codepoint=1, blacklist_categories=('Cc', 'Cs'))), values=oneway))
def test_stringify_types_lost(data):
    # Some types can be serialized, but not recovered from strings by json.loads.
    # Instead, you have to manually attempt to convert, by field, if you are expecting one of these types.
    #
    # If something can't be serialized, or unserialized,
    # this test will raise an Exception, rather than failing with an assertion error.
    unstringify_data(stringify_data(data))


@given(binary())
def test_perma_payments_encrypt_and_decrypt(b):
    ci = encrypt_for_perma_payments(b)
    assert decrypt_from_perma_payments(ci) == b

