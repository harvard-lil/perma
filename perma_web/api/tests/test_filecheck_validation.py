from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from rest_framework.exceptions import ValidationError

from api.serializers import AuthenticatedLinkSerializer


@override_settings(SCAN_UPLOADS=True, SCAN_URL='http://filecheck/scan', SCAN_TIMEOUT=(5, 60))
class FilecheckValidationTestCase(SimpleTestCase):
    def serializer(self):
        upload = SimpleUploadedFile('image.gif', b'GIF89a\x01\x00\x01\x00\x00\x00\x00')
        request = SimpleNamespace(user=SimpleNamespace(id=1), data={'file': upload})
        return AuthenticatedLinkSerializer(context={'request': request})

    def test_upload_policy_for_verdicts_and_invalid_responses(self):
        for payload, blocked in (
            ({'verdict': 'clean'}, False),
            ({'verdict': 'unsafe'}, True),
            ({'verdict': 'rejected'}, True),
            ({'verdict': 'unavailable'}, False),
            ({'safe': True}, False),
            ({'safe': False, 'reason': 'virus detected'}, False),
            ({'safe': False}, False),
            ([], False),
        ):
            with self.subTest(payload=payload):
                response = Mock()
                response.json.return_value = payload
                with patch('api.filecheck.requests.post', return_value=response), patch('api.serializers.logger') as logger:
                    serializer = self.serializer()
                    data = {'submitted_url': 'https://example.com/image.gif'}
                    if blocked:
                        with self.assertRaises(ValidationError) as raised:
                            serializer.validate(data)
                        self.assertEqual(str(raised.exception.detail['file']), 'Validation failed.')
                        logger.warning.assert_called_once()
                    else:
                        self.assertEqual(serializer.validate(data)['submitted_url'], data['submitted_url'])
                        logger.warning.assert_not_called()
                        if payload != {'verdict': 'clean'}:
                            logger.error.assert_called_once()

    @override_settings(SCAN_UPLOADS=False)
    def test_disabled_scanning_does_not_call_filecheck(self):
        with patch('api.filecheck.requests.post') as post:
            self.serializer().validate({'submitted_url': 'https://example.com/image.gif'})
        post.assert_not_called()
