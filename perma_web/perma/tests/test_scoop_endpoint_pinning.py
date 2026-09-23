"""Which Scoop instance a capture talks to, and when that may change.

A capture is several requests: start it, poll it until it finishes, then fetch
the WACZ. The last two name an `id_capture` that only the instance which issued
it has ever heard of. So the choice between the standard and beta APIs has to
be made once per capture and reused, not re-read per request -- otherwise
flipping `use_beta_capture_api` while captures are in flight sends their polls
to an instance that 404s them, and the captures fail.

Pinning is also what makes the switch safe to flip during a cutover: in-flight
captures finish where they started, and only new ones move.
"""

import ast
from pathlib import Path
from unittest.mock import patch

import pytest
from django.test import override_settings
from waffle.testutils import override_switch

from perma.utils import current_scoop_api, send_to_scoop

STANDARD = {"SCOOP_API_URL": "https://standard.example/", "SCOOP_API_KEY": "standard-key"}
BETA = {"BETA_SCOOP_API_URL": "https://beta.example/", "BETA_SCOOP_API_KEY": "beta-key"}


@pytest.mark.django_db
@override_settings(**STANDARD, **BETA)
def test_the_switch_chooses_the_beta_api():
    with override_switch("use_beta_capture_api", active=True):
        assert current_scoop_api() == ("https://beta.example/", "beta-key")
    with override_switch("use_beta_capture_api", active=False):
        assert current_scoop_api() == ("https://standard.example/", "standard-key")


@pytest.mark.django_db
@override_settings(**STANDARD, BETA_SCOOP_API_URL=None, BETA_SCOOP_API_KEY=None)
def test_the_switch_falls_back_when_the_beta_api_is_not_configured():
    with override_switch("use_beta_capture_api", active=True):
        assert current_scoop_api() == ("https://standard.example/", "standard-key")


def call_send_to_scoop(api):
    """Run send_to_scoop against a stubbed transport; return the URL and key it used."""
    with patch("perma.utils.requests.request") as request:
        request.return_value.status_code = 200
        request.return_value.json.return_value = {"ok": True}
        send_to_scoop(method="get", path="capture/abc", valid_if=lambda code, _: True, api=api)
    args, kwargs = request.call_args
    return args[1], kwargs["headers"]["Access-Key"]


@pytest.mark.django_db
@override_settings(**STANDARD, **BETA)
def test_a_pinned_capture_keeps_its_instance_when_the_switch_flips():
    api = current_scoop_api()
    assert api == ("https://standard.example/", "standard-key")

    # The operator flips mid-capture. The poll must still go where the capture
    # was started, not to the instance that has never heard of this job.
    with override_switch("use_beta_capture_api", active=True):
        assert call_send_to_scoop(api) == ("https://standard.example/capture/abc", "standard-key")


@pytest.mark.django_db
@override_settings(**STANDARD, **BETA)
def test_an_unpinned_request_follows_the_switch():
    """Requests that stand alone -- URL validation -- carry no id and may move freely."""
    with override_switch("use_beta_capture_api", active=True):
        assert call_send_to_scoop(None) == ("https://beta.example/capture/abc", "beta-key")


CAPTURE_PATH_FUNCTIONS = {"capture_with_scoop", "save_scoop_archive"}


def test_every_scoop_request_in_the_capture_path_is_pinned():
    """
    The invariant, checked structurally: a send_to_scoop call inside the
    capture path passes the instance it was given. A new call added there
    without `api=` would re-read the switch and reintroduce the bug, which no
    unit test of the surrounding function would notice while the switch is off.
    """
    source = Path(__file__).resolve().parents[1] / "celery_tasks.py"
    tree = ast.parse(source.read_text())

    unpinned = []
    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef) or function.name not in CAPTURE_PATH_FUNCTIONS:
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.Call):
                continue
            callee = node.func
            if isinstance(callee, ast.Name) and callee.id == "send_to_scoop":
                if not any(keyword.arg == "api" for keyword in node.keywords):
                    unpinned.append(f"{function.name}, line {node.lineno}")

    assert not unpinned, f"send_to_scoop without api= in the capture path: {unpinned}"


def test_the_capture_path_resolves_the_instance_exactly_once():
    """One resolution per capture; a second would be a second chance to differ."""
    source = Path(__file__).resolve().parents[1] / "celery_tasks.py"
    tree = ast.parse(source.read_text())

    resolutions = 0
    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef) or function.name != "capture_with_scoop":
            continue
        for node in ast.walk(function):
            callee = node.func if isinstance(node, ast.Call) else None
            if isinstance(callee, ast.Name) and callee.id == "current_scoop_api":
                resolutions += 1

    assert resolutions == 1
