"""Filecheck contracts for both ECS and the legacy development image."""
from io import BytesIO
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import requests

from api.filecheck import scan_upload


class FilecheckTestCase(TestCase):
    def scan(self, response):
        upload = SimpleNamespace(name='image.gif', file=BytesIO(b'file contents'))
        upload.file.seek(4)
        with patch('api.filecheck.requests.post', return_value=response) as post:
            result = scan_upload(upload, 'http://filecheck:8888/scan/', (5, 60))
        self.assertEqual(upload.file.tell(), 0)
        self.assertEqual(post.call_args.kwargs['timeout'], (5, 60))
        return result

    def test_new_verdicts_take_precedence(self):
        for verdict in ('clean', 'unsafe', 'rejected', 'unavailable'):
            with self.subTest(verdict=verdict):
                response = Mock()
                response.json.return_value = {'verdict': verdict, 'safe': True, 'reason': 'detail'}
                self.assertEqual(self.scan(response), (verdict, 'detail'))

    def test_legacy_responses(self):
        for payload, expected in (
            ({'safe': True}, 'clean'),
            ({'safe': False, 'reason': 'virus detected'}, 'unsafe'),
            ({'safe': False, 'reason': 'invalid file type'}, 'unsafe'),
            ({'safe': False, 'reason': 'clamav not running'}, 'unavailable'),
            ({'safe': False, 'reason': 'clamav out of date'}, 'unavailable'),
            ({'safe': False, 'reason': 'Communication with filecheck API failed: timeout'}, 'unavailable'),
        ):
            with self.subTest(payload=payload):
                response = Mock()
                response.json.return_value = payload
                self.assertEqual(self.scan(response)[0], expected)

    def test_malformed_responses_fail_open(self):
        for payload in (None, [], 'bad', {}, {'safe': 'false'}, {'safe': False},
                        {'safe': False, 'reason': None}, {'verdict': 'future', 'safe': False},
                        {'verdict': []}, {'verdict': None}):
            with self.subTest(payload=payload):
                response = Mock()
                response.json.return_value = payload
                self.assertEqual(self.scan(response)[0], 'unavailable')

    def test_non_json_response_fails_open(self):
        response = Mock()
        response.json.side_effect = requests.exceptions.JSONDecodeError('Invalid JSON', 'bad', 0)
        self.assertEqual(self.scan(response)[0], 'unavailable')

    def test_http_errors_fail_open(self):
        response = requests.Response()
        response.status_code = 503
        self.assertEqual(self.scan(response)[0], 'unavailable')

    def test_transport_failures_restore_file_position(self):
        for error in (requests.Timeout('timeout'), requests.ConnectionError('connection failed')):
            with self.subTest(error=error):
                upload = SimpleNamespace(name='image.gif', file=BytesIO(b'file contents'))
                with patch('api.filecheck.requests.post', side_effect=error):
                    self.assertEqual(scan_upload(upload, 'http://filecheck/scan', (5, 60))[0], 'unavailable')
                self.assertEqual(upload.file.tell(), 0)

    def test_multipart_request_contains_complete_upload(self):
        upload = SimpleNamespace(name='image.gif', file=BytesIO(b'file contents'))
        upload.file.seek(4)
        response = Mock()
        response.json.return_value = {'verdict': 'clean'}

        def send(url, **kwargs):
            prepared = requests.Request('POST', url, files=kwargs['files']).prepare()
            self.assertIn(b'filename="image.gif"', prepared.body)
            self.assertIn(b'file contents', prepared.body)
            return response

        with patch('api.filecheck.requests.post', side_effect=send):
            self.assertEqual(scan_upload(upload, 'http://filecheck/scan', (5, 60))[0], 'clean')
        self.assertEqual(upload.file.tell(), 0)
