import json
import logging
import sys

from perma import ia_metrics


def _lines(capfd):
    out, _err = capfd.readouterr()
    return [line for line in out.splitlines() if line]


def test_flow_is_one_bare_json_line_on_stdout(capfd):
    capfd.readouterr()

    ia_metrics.flow("upload_retry", item="daily_perma_cc_2026-09-29", reason="rate_limit")

    lines = _lines(capfd)
    assert lines == ['{"ia_metrics":1,"event":"ia_flow","kind":"upload_retry","n":1,"reason":"rate_limit","item":"daily_perma_cc_2026-09-29"}']


def test_flow_counts_and_omits_an_absent_item(capfd):
    capfd.readouterr()

    ia_metrics.flow("upload_confirmed", n=12)

    assert json.loads(_lines(capfd)[0]) == {"ia_metrics": 1, "event": "ia_flow", "kind": "upload_confirmed", "n": 12}


def test_state_is_one_json_line(capfd):
    capfd.readouterr()

    ia_metrics.state(decision="skip_lock", queue_ia=3, pending_by_day={"2026-09-22": 976})

    assert json.loads(_lines(capfd)[0]) == {
        "ia_metrics": 1, "event": "ia_state", "decision": "skip_lock", "queue_ia": 3, "pending_by_day": {"2026-09-22": 976},
    }


def test_metrics_logger_is_configured_apart_from_the_root_logger():
    logger = logging.getLogger("perma.ia_metrics")
    assert logger.propagate is False
    # pytest adds its own capture handlers; ours is the one on the real stdout
    [handler] = [h for h in logger.handlers if getattr(h, "stream", None) is sys.__stdout__]
    assert handler.formatter._fmt == "%(message)s"
