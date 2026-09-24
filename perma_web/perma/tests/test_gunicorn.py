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
def server(tmp_path, request):
    app = tmp_path / "acceptance_app.py"
    app.write_text("""
import time, os, concurrent.futures
from pathlib import Path

def application(environ, start_response):
    path = environ["PATH_INFO"]
    if path in ("/slow", "/nested", "/hang"):
        Path(__file__).with_suffix(".started").touch()
    if path == "/nested":
        time.sleep(2)
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(lambda: None).result()
    if path == "/hang":
        time.sleep(30)
    if path == "/block":
        Path(__file__).with_suffix(f".{os.getpid()}.blocked").touch()
        deadline = time.monotonic() + 10
        while not Path(__file__).with_suffix(".release").exists():
            if time.monotonic() > deadline:
                raise TimeoutError("Test did not release blocked request")
            time.sleep(0.01)
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
                "--worker-tmp-dir",
                str(tmp_path),
                "--chdir",
                str(tmp_path),
                *getattr(request, "param", []),
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


def test_head_then_get_reconnects_after_origin_close(server):
    port, _, _ = server
    with closing(http.client.HTTPConnection("127.0.0.1", port, timeout=5)) as conn:
        conn.request("HEAD", "/")
        response = conn.getresponse()
        assert response.read() == b""
        assert conn.sock is None  # sync closes the origin connection
        conn.request("GET", "/")
        response = conn.getresponse()
        assert response.status == 200
        assert response.read() == b"payload"
        assert conn.sock is None


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


def fetch(port, path="/", timeout=5):
    with closing(http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)) as conn:
        conn.request("GET", path)
        response = conn.getresponse()
        return response.status, response.read()


def wait_for(path):
    for _ in range(200):
        if path.exists():
            return
        time.sleep(0.01)
    pytest.fail(f"Request did not reach {path.name}")


@pytest.mark.parametrize("server", [["--max-requests", "1", "--max-requests-jitter", "0", "--graceful-timeout", "1"]], indirect=True)
def test_recycling_waits_for_request_using_nested_thread_pool(server):
    # Reproduces the upload's boto3-style late thread-pool creation. The old
    # gthread worker could start interpreter shutdown before this request ended.
    port, _, _ = server
    assert fetch(port, "/nested") == (200, b"payload")
    assert fetch(port) == (200, b"payload")


@pytest.mark.parametrize("server", [["--timeout", "2"]], indirect=True)
def test_stuck_request_is_terminated_and_worker_recovers(server):
    port, _, app = server
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fetch, port, "/hang", 8)
        wait_for(app.with_suffix(".started"))
        try:
            status, _ = future.result(timeout=8)
            assert status == 500
        except (http.client.RemoteDisconnected, ConnectionResetError):
            pass  # The timed-out worker may close before sending an error.
    assert time.monotonic() - started < 8
    assert "WORKER TIMEOUT" in (app.parent / "server.log").read_text()
    assert fetch(port) == (200, b"payload")


@pytest.mark.parametrize("server", [["--workers", "5"]], indirect=True)
def test_health_request_uses_spare_worker_during_slow_requests(server):
    port, _, app = server
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        pending = [pool.submit(fetch, port, "/block") for _ in range(4)]
        try:
            for _ in range(200):
                if len(list(app.parent.glob("*.blocked"))) == 4:
                    break
                time.sleep(0.01)
            assert len(list(app.parent.glob("*.blocked"))) == 4
            assert fetch(port, "/healthcheck/", timeout=1) == (200, b"payload")
        finally:
            app.with_suffix(".release").touch()
        assert all(f.result(timeout=5) == (200, b"payload") for f in pending)


@pytest.mark.parametrize("server", [["--graceful-timeout", "3"]], indirect=True)
def test_sigterm_allows_late_thread_pool_creation(server):
    port, process, app = server
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fetch, port, "/nested")
        wait_for(app.with_suffix(".started"))
        process.terminate()
        assert future.result(timeout=5) == (200, b"payload")
    assert process.wait(timeout=5) == 0


def test_statement_timeout_is_below_worker_timeout():
    # Postgres should cancel a long statement before gunicorn kills the worker
    # waiting on it; see raw_env in gunicorn_config.py.
    import runpy
    config = runpy.run_path(str(Path(__file__).resolve().parents[2] / "gunicorn_config.py"))
    env = dict(item.split("=", 1) for item in config["raw_env"])
    statement_timeout = env["PERMA_STATEMENT_TIMEOUT"]
    assert statement_timeout.endswith("s")
    assert int(statement_timeout[:-1]) < config["timeout"]
