"""Exercise the real HTTP server: Django's test client masks HEAD body bugs.

Copied from h2o (web/test/server/test_gunicorn.py) with the config path
adjusted; it runs gunicorn_config.py against a stand-in WSGI app, so it needs
no database.
"""

import concurrent.futures
from contextlib import closing
import http.client
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import pytest


@pytest.fixture
def server(tmp_path):
    app = tmp_path / "acceptance_app.py"
    app.write_text("""
import time
from pathlib import Path

def application(environ, start_response):
    path = environ["PATH_INFO"]
    if path == "/slow":
        Path(__file__).with_suffix(".started").touch()
        time.sleep(1)
    status = "302 Found" if path == "/redirect" else "200 OK"
    headers = [("Content-Type", "text/plain"), ("Content-Length", "7")]
    if path == "/redirect":
        headers.append(("Location", "/"))
    start_response(status, headers)
    try:
        yield b"payload"
    finally:
        Path(__file__).with_suffix(".closed").touch()
""")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    config = Path(__file__).resolve().parents[2] / "gunicorn_config.py"
    with (tmp_path / "server.log").open("w+") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "gunicorn",
                "-c",
                str(config),
                "--bind",
                f"127.0.0.1:{port}",
                "--workers",
                "1",
                "--chdir",
                str(tmp_path),
                "acceptance_app:application",
            ],
            stdout=log,
            stderr=log,
            env={k: v for k, v in os.environ.items() if k != "GUNICORN_CMD_ARGS"},
        )
        try:
            for _ in range(100):
                if process.poll() is not None:
                    log.seek(0)
                    pytest.fail(log.read())
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                        break
                except ConnectionRefusedError:
                    time.sleep(0.05)
            else:
                pytest.fail("Gunicorn did not start")
            yield port, process, app
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=30)


@pytest.mark.parametrize("path,status", [("/", 200), ("/redirect", 302)])
def test_head_keeps_headers_without_body(server, path, status):
    port, _, app = server
    # Read the wire directly: HTTP clients ordinarily discard HEAD bodies.
    with socket.create_connection(("127.0.0.1", port), timeout=5) as conn:
        conn.sendall(
            f"HEAD {path} HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n".encode()
        )
        chunks = []
        while chunk := conn.recv(65536):
            chunks.append(chunk)
    headers, body = b"".join(chunks).split(b"\r\n\r\n", 1)
    assert f" {status} ".encode() in headers
    assert b"Content-Length: 7" in headers
    assert body == b""
    assert app.with_suffix(".closed").exists()


def test_head_then_get_on_reused_connection(server):
    port, _, _ = server
    with closing(http.client.HTTPConnection("127.0.0.1", port, timeout=5)) as conn:
        conn.request("HEAD", "/")
        response = conn.getresponse()
        assert response.read() == b""
        original_socket = conn.sock
        conn.request("GET", "/")
        response = conn.getresponse()
        assert response.status == 200
        assert response.read() == b"payload"
        assert conn.sock is original_socket


def test_sigterm_completes_inflight_request(server):
    port, process, app = server

    def request():
        with closing(http.client.HTTPConnection("127.0.0.1", port, timeout=5)) as conn:
            conn.request("GET", "/slow")
            return conn.getresponse().read()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(request)
        for _ in range(100):
            if app.with_suffix(".started").exists():
                break
            time.sleep(0.01)
        assert app.with_suffix(".started").exists()
        process.terminate()
        assert future.result(timeout=5) == b"payload"
    assert process.wait(timeout=10) == 0
