"""
Violation baselines for the axe accessibility gate.

Deals in axe's result dicts and JSON files only: no Playwright, no pytest.
A violation is identified by its rule id and the CSS selector path of the
element (axe's `target`). A baseline stores each violation's rule, target,
impact and help text, sorted by (rule, target), and the axe-core version that
produced it. It stores no `html`, which varies from run to run.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

Key = tuple[str, tuple]  # (rule id, target)


@dataclass(frozen=True)
class Violation:
    """
    One element failing one axe rule.

    `impact` and `help` come from axe. `failure_summary` is axe's advice for
    fixing the element; it is only known for the current scan, never stored in
    a baseline, and doesn't take part in equality.
    """

    rule: str
    target: tuple
    impact: str | None
    help: str
    failure_summary: str | None = field(default=None, compare=False)

    @property
    def key(self) -> Key:
        return (self.rule, self.target)


@dataclass(frozen=True)
class Baseline:
    """The violations recorded for one page, and the axe-core version that found them."""

    axe_version: str | None
    violations: dict[Key, Violation]


@dataclass(frozen=True)
class Comparison:
    """Violations in the current scan but not the baseline (`new`), and the reverse (`fixed`)."""

    new: list[Violation]
    fixed: list[Violation]

    @property
    def matches(self) -> bool:
        return not self.new and not self.fixed


def _freeze(target):
    # Targets inside shadow DOM or frames are nested lists, which can't be dict keys.
    return tuple(_freeze(part) if isinstance(part, list) else part for part in target)


def _sort_key(violation: Violation):
    return (violation.rule, json.dumps(violation.target))


def axe_version(response: dict) -> str | None:
    """The axe-core version recorded in an axe response, or None if it names none."""
    return (response.get("testEngine") or {}).get("version")


def violations_from_axe(response: dict) -> dict[Key, Violation]:
    """
    Flatten an axe response's `violations` into one entry per (rule, target).

    Args:
        response: The raw axe result dict, as returned by `Axe().run(page).response`.

    Returns:
        A dict keyed by (rule id, target). If axe reports one key twice, the first
        report is kept.
    """
    found: dict[Key, Violation] = {}
    for rule in response.get("violations", []):
        for node in rule.get("nodes", []):
            violation = Violation(
                rule=rule["id"],
                target=_freeze(node["target"]),
                impact=node.get("impact") or rule.get("impact"),
                help=rule.get("help", ""),
                failure_summary=node.get("failureSummary"),
            )
            found.setdefault(violation.key, violation)
    return found


def save_baseline(path: Path, version: str | None, violations: dict[Key, Violation]) -> None:
    """
    Write a baseline file, creating parent directories.

    The file is JSON with `axe_version` and `violations` (each with rule, target,
    impact and help), sorted by (rule, target) so that diffs read cleanly.
    """
    entries = [
        {"rule": v.rule, "target": list(v.target), "impact": v.impact, "help": v.help}
        for v in sorted(violations.values(), key=_sort_key)
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"axe_version": version, "violations": entries}, indent=2) + "\n")


def load_baseline(path: Path) -> Baseline:
    """
    Read a baseline file written by `save_baseline`.

    Raises:
        FileNotFoundError: The file doesn't exist.
        ValueError: The file isn't valid JSON or lacks the expected fields.
    """
    try:
        data = json.loads(path.read_text())
        violations = {}
        for entry in data["violations"]:
            violation = Violation(entry["rule"], _freeze(entry["target"]), entry["impact"], entry["help"])
            violations[violation.key] = violation
        return Baseline(data["axe_version"], violations)
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"Malformed accessibility baseline {path}: {exc!r}") from exc


def compare(baseline: dict[Key, Violation], current: dict[Key, Violation]) -> Comparison:
    """Split the difference between a baseline and a scan into new and fixed violations."""
    new = [current[key] for key in current.keys() - baseline.keys()]
    fixed = [baseline[key] for key in baseline.keys() - current.keys()]
    return Comparison(sorted(new, key=_sort_key), sorted(fixed, key=_sort_key))


def _format_entry(violation: Violation) -> str:
    lines = [f"  [{violation.impact}] {violation.rule}: {violation.help}", f"    target: {json.dumps(list(violation.target))}"]
    if violation.failure_summary:
        lines.extend(f"    {line}" for line in violation.failure_summary.splitlines())
    return "\n".join(lines)


def format_failure(
    name: str,
    baseline_path: Path,
    comparison: Comparison,
    baseline_axe_version: str | None,
    current_axe_version: str | None,
) -> str:
    """
    Describe a mismatch between a scan and its baseline.

    New and fixed violations are listed separately. The message names the
    baseline file, says how to re-record it, and notes when the baseline was
    recorded with a different axe-core version, since that alone can change results.
    """
    parts = [f"Accessibility violations for {name!r} differ from {baseline_path}."]
    if baseline_axe_version != current_axe_version:
        parts.append(
            f"The baseline was recorded with axe-core {baseline_axe_version}; this scan used {current_axe_version}. "
            "A different axe-core version can change results without any page change."
        )
    if comparison.new:
        parts.append(f"New violations ({len(comparison.new)}), not in the baseline:")
        parts.extend(_format_entry(v) for v in comparison.new)
    if comparison.fixed:
        parts.append(f"Fixed violations ({len(comparison.fixed)}), in the baseline but no longer found:")
        parts.extend(_format_entry(v) for v in comparison.fixed)
    parts.append("If the change is intended, re-run with --update-a11y-baselines and review the baseline diff.")
    return "\n".join(parts)
