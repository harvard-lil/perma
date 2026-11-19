"""Unit tests of the accessibility baseline comparator; no browser."""

import json

import pytest

from functional_tests.accessibility_baseline import (
    Violation,
    axe_version,
    compare,
    format_failure,
    load_baseline,
    save_baseline,
    violations_from_axe,
)


def _node(target, impact="serious", html="<p>x</p>", summary="Fix any of the following"):
    return {"target": target, "impact": impact, "html": html, "failureSummary": summary}


def _response(*rules, version="4.12.1"):
    return {
        "testEngine": {"name": "axe-core", "version": version},
        "violations": [
            {"id": rule_id, "impact": "serious", "help": f"help for {rule_id}", "nodes": nodes}
            for rule_id, nodes in rules
        ],
    }


def _violation(rule, *target, impact="serious"):
    return Violation(rule, target, impact, f"help for {rule}")


def _keyed(*violations):
    return {v.key: v for v in violations}


def test_flattens_one_entry_per_rule_and_target():
    response = _response(
        ("color-contrast", [_node(["a.one"]), _node(["a.two"], impact="moderate")]),
        ("region", [_node(["p"])]),
    )

    found = violations_from_axe(response)

    assert set(found) == {("color-contrast", ("a.one",)), ("color-contrast", ("a.two",)), ("region", ("p",))}
    two = found[("color-contrast", ("a.two",))]
    assert (two.impact, two.help) == ("moderate", "help for color-contrast")
    assert two.failure_summary == "Fix any of the following"


def test_nested_targets_become_hashable_keys():
    found = violations_from_axe(_response(("label", [_node([["#host", "input"]])])))

    assert set(found) == {("label", (("#host", "input"),))}


def test_a_node_without_its_own_impact_takes_the_rules():
    found = violations_from_axe(_response(("region", [{"target": ["p"], "html": "<p>"}])))

    assert found[("region", ("p",))].impact == "serious"


def test_a_repeated_rule_and_target_keeps_the_first():
    found = violations_from_axe(_response(("region", [_node(["p"], impact="minor"), _node(["p"], impact="severe")])))

    assert found[("region", ("p",))].impact == "minor"


def test_response_without_violations_is_empty():
    assert violations_from_axe({}) == {}


def test_axe_version_is_read_from_the_test_engine():
    assert axe_version(_response(version="4.9.0")) == "4.9.0"
    assert axe_version({}) is None


def test_baseline_round_trips_sorted_without_html(tmp_path):
    path = tmp_path / "deep" / "page.json"
    violations = _keyed(_violation("region", "p"), _violation("color-contrast", "b"), _violation("color-contrast", "a"))

    save_baseline(path, "4.12.1", violations)

    data = json.loads(path.read_text())
    assert data["axe_version"] == "4.12.1"
    assert [(v["rule"], v["target"]) for v in data["violations"]] == [
        ("color-contrast", ["a"]), ("color-contrast", ["b"]), ("region", ["p"]),
    ]
    assert set(data["violations"][0]) == {"rule", "target", "impact", "help"}
    assert "html" not in path.read_text()
    loaded = load_baseline(path)
    assert loaded.axe_version == "4.12.1"
    assert loaded.violations == violations


def test_saving_is_deterministic(tmp_path):
    first, second = tmp_path / "1.json", tmp_path / "2.json"
    save_baseline(first, "1", _keyed(_violation("a", "x"), _violation("b", "y")))
    save_baseline(second, "1", _keyed(_violation("b", "y"), _violation("a", "x")))

    assert first.read_bytes() == second.read_bytes()


def test_nested_targets_survive_a_round_trip(tmp_path):
    path = tmp_path / "page.json"
    violations = _keyed(Violation("label", (("#host", "input"),), "critical", "h"))

    save_baseline(path, "1", violations)

    assert load_baseline(path).violations == violations


@pytest.mark.parametrize("content", ["not json", "{}", '{"axe_version": "1", "violations": [{"rule": "x"}]}'])
def test_malformed_baseline_raises_value_error(tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_text(content)

    with pytest.raises(ValueError, match="Malformed accessibility baseline"):
        load_baseline(path)


def test_missing_baseline_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_baseline(tmp_path / "nope.json")


def test_identical_sets_match():
    both = _keyed(_violation("region", "p"))

    result = compare(both, dict(both))

    assert result.matches and not result.new and not result.fixed


def test_new_and_fixed_are_separated():
    kept, gone, added = _violation("a", "1"), _violation("b", "2"), _violation("c", "3")

    result = compare(_keyed(kept, gone), _keyed(kept, added))

    assert result.new == [added]
    assert result.fixed == [gone]
    assert not result.matches


def test_the_same_rule_on_another_element_is_new_and_fixed():
    # Counts per rule would miss this: one node fixed, another broken.
    result = compare(_keyed(_violation("color-contrast", "a")), _keyed(_violation("color-contrast", "b")))

    assert [v.target for v in result.new] == [("b",)]
    assert [v.target for v in result.fixed] == [("a",)]


def test_impact_help_and_summary_do_not_affect_the_comparison():
    old = Violation("region", ("p",), "minor", "old help")
    new = Violation("region", ("p",), "serious", "new help", failure_summary="changed")

    assert compare(_keyed(old), _keyed(new)).matches


def test_comparison_lists_are_sorted():
    result = compare({}, _keyed(_violation("b", "2"), _violation("a", "9"), _violation("a", "1")))

    assert [(v.rule, v.target) for v in result.new] == [("a", ("1",)), ("a", ("9",)), ("b", ("2",))]


def test_failure_message_lists_new_and_fixed_separately(tmp_path):
    path = tmp_path / "page.json"
    added = Violation("image-alt", ("img",), "critical", "Images must have alternate text", "Fix any of the following:\n  no alt")
    gone = _violation("region", "p")

    message = format_failure("page", path, compare(_keyed(gone), _keyed(added)), "4.12.1", "4.12.1")

    assert str(path) in message
    assert "--update-a11y-baselines" in message
    new_part, fixed_part = message.split("Fixed violations")
    assert "New violations (1)" in new_part and "image-alt" in new_part and '["img"]' in new_part
    assert "[critical]" in new_part and "no alt" in new_part
    assert "(1), in the baseline but no longer found" in fixed_part and "region" in fixed_part
    assert "axe-core" not in message


def test_failure_message_omits_an_empty_section(tmp_path):
    message = format_failure("page", tmp_path / "p.json", compare({}, _keyed(_violation("a", "x"))), "1", "1")

    assert "New violations" in message
    assert "Fixed violations" not in message


def test_failure_message_mentions_a_different_axe_version(tmp_path):
    message = format_failure("page", tmp_path / "p.json", compare({}, _keyed(_violation("a", "x"))), "4.10.0", "4.12.1")

    assert "axe-core 4.10.0" in message and "4.12.1" in message
