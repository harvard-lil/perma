import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


def test_gunicorn_request_attribution(tmp_path):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    (tmp_path / 'logging_app.py').write_text(
        "def app(environ, start_response):\n"
        "    environ['REMOTE_ADDR'] = '192.0.2.99'\n"
        "    start_response('200 OK', [('Content-Length', '2')])\n"
        "    return [b'ok']\n"
    )
    env = {**os.environ, 'APP_CONFIG': '{"TIER":"staging"}',
           'SENTRY_RELEASE': 'perma@test-release',
           'GUNICORN_CMD_ARGS': '--access-logfile - --access-logformat legacy'}
    with subprocess.Popen(
        [sys.executable, '-m', 'gunicorn', '--config', str(Path(__file__).resolve().parents[2] / 'gunicorn_config.py'),
         '--worker-tmp-dir', str(tmp_path), '--workers', '1', '--bind', f'127.0.0.1:{port}', '--pythonpath', str(tmp_path),
         'logging_app:app'],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ) as process:
        try:
            request = Request(f'http://127.0.0.1:{port}/health/',
                              headers={'CF-Connecting-IP': '192.0.2.1'})
            for attempt in range(100):
                try:
                    with urlopen(request, timeout=1) as response:
                        assert response.read() == b'ok'
                    break
                except URLError:
                    if process.poll() is not None or attempt == 99:
                        raise
                    time.sleep(0.05)
        finally:
            process.terminate()
            stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 0, stderr
    record, = [json.loads(line) for line in stdout.splitlines()]
    assert record['event'] == 'http_access'
    assert record['service'] == 'perma'
    assert record['environment'] == 'staging'
    assert record['release'] == 'perma@test-release'
    assert record['client_ip'] == '192.0.2.1'
    assert record['peer_ip'] == '127.0.0.1'
