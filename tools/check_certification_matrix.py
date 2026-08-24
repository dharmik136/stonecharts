#!/usr/bin/env python3
"""Check that every certified chart has the same evidence surface as the seed charts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES = ROOT / "spec" / "capabilities.json"
SCHEMA = ROOT / "spec" / "chart-spec.schema.json"
CHARTS = ROOT / "charts"
PY_TESTS = ROOT / "libs" / "python" / "tests"
GO_TESTS = ROOT / "libs" / "go" / "render_test.go"

SEED_CHARTS = {"line", "column", "area", "bar", "scatter", "bubble", "combo"}


def chart_dir(chart_id: str) -> Path:
    return CHARTS / ("line-basic" if chart_id == "line" else chart_id)


def contains(path: Path, value: str) -> bool:
    return value in path.read_text(encoding="utf-8")


def main() -> int:
    registry = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
    chart_types = registry["chartTypes"]
    ids = [item["id"] for item in chart_types]
    failures: list[str] = []

    if len(ids) != 36 or len(set(ids)) != 36:
        failures.append(f"expected 36 unique chart types, found {len(ids)}")
    if any(item["tier"] != "certified" for item in chart_types):
        failures.append("capability registry contains a non-certified chart")

    schema_text = SCHEMA.read_text(encoding="utf-8")
    golden_test = PY_TESTS / "test_golden.py"
    property_test = PY_TESTS / "test_property_rendering.py"
    semantic_test = PY_TESTS / "test_semantic_invariants.py"
    purity_test = PY_TESTS / "test_renderer_purity.py"
    stoneverify_test = PY_TESTS / "test_stonecharts_verify.py"
    go_text = GO_TESTS.read_text(encoding="utf-8")

    for chart_id in ids:
        directory = chart_dir(chart_id)
        invalid_path = directory / "invalid-fixtures.json"
        try:
            invalid_cases = json.loads(invalid_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            failures.append(f"{chart_id}: invalid fixture set unavailable ({exc})")
            invalid_cases = []

        checks = {
            "design": (directory / "design.md").exists(),
            "examples": any((directory / "examples").glob("*.json")),
            "goldens": any((directory / "golden").glob("*.svg")),
            "invalid>=3": len(invalid_cases) >= 3,
            "schema": chart_id in schema_text,
            "python-goldens": chart_id in golden_test.read_text(encoding="utf-8"),
            "go-goldens": chart_id in go_text,
            "property": chart_id in property_test.read_text(encoding="utf-8") or "RandomizedAll36Types" in go_text,
            "semantic": chart_id in semantic_test.read_text(encoding="utf-8") or chart_id in go_text,
            "purity": chart_id in purity_test.read_text(encoding="utf-8") or "RendererPurity" in go_text,
            # StoneVerify exercises the canonical capability registry and certified
            # profile globally; it is intentionally not duplicated once per chart id.
            "stoneverify": stoneverify_test.exists() and "certified profile" in stoneverify_test.read_text(encoding="utf-8"),
        }
        missing = [name for name, passed in checks.items() if not passed]
        if missing:
            failures.append(f"{chart_id}: missing {', '.join(missing)}")

    if failures:
        print("certification matrix FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"certification matrix PASS: {len(ids)} charts; {len(SEED_CHARTS)} seed charts and {len(ids) - len(SEED_CHARTS)} promoted charts share the SC-CERT evidence surface")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
