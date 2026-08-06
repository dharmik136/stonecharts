"""Verify chart types meet the mandatory admission checklist (SC-ARCH-011).

Runs in CI on PRs that touch charts/<type>/ directories.  For each chart type
passed as an argument, verifies that all required admission phases are complete.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DECISIONS_PATH = ROOT / "docs" / "project" / "decisions.md"
SCHEMA_PATH = ROOT / "spec" / "chart-spec.schema.json"
CHARTS_DIR = ROOT / "charts"


def _load_schema_type_enum() -> list[str]:
    """Return the list of accepted chart type strings from the spec schema."""
    with SCHEMA_PATH.open(encoding="utf-8") as fh:
        schema = json.load(fh)
    return list(schema["properties"]["type"]["enum"])


def _load_decisions_text() -> str:
    """Return the full text of the decision register."""
    return DECISIONS_PATH.read_text(encoding="utf-8")


def check_decision_document(chart_type: str, decisions_text: str) -> str | None:
    """A DEC-* reference that mentions *chart_type* must exist in decisions.md."""
    for line in decisions_text.splitlines():
        if "DEC-" in line and chart_type in line:
            return None
    return f"No DEC-* reference mentioning '{chart_type}' found in {DECISIONS_PATH.relative_to(ROOT)}"


def check_schema_registration(chart_type: str, type_enum: list[str]) -> str | None:
    """The chart type string must appear in the schema's type enum."""
    if chart_type in type_enum:
        return None
    return (
        f"'{chart_type}' not found in {SCHEMA_PATH.relative_to(ROOT)} type enum "
        f"(registered types: {', '.join(type_enum)})"
    )


def check_golden_fixtures(chart_type: str) -> str | None:
    """charts/<type>/golden/ must exist and contain at least one .svg file."""
    golden_dir = CHARTS_DIR / chart_type / "golden"
    if not golden_dir.is_dir():
        return f"Directory {golden_dir.relative_to(ROOT)} does not exist"
    svg_files = list(golden_dir.glob("*.svg"))
    if not svg_files:
        return f"No .svg files found in {golden_dir.relative_to(ROOT)}"
    return None


def check_invalid_fixtures(chart_type: str) -> str | None:
    """charts/<type>/invalid-fixtures.json must exist."""
    path = CHARTS_DIR / chart_type / "invalid-fixtures.json"
    if not path.is_file():
        return f"File {path.relative_to(ROOT)} does not exist"
    return None


def check_design_document(chart_type: str) -> str | None:
    """charts/<type>/design.md must exist."""
    path = CHARTS_DIR / chart_type / "design.md"
    if not path.is_file():
        return f"File {path.relative_to(ROOT)} does not exist"
    return None


def check_example_specs(chart_type: str) -> str | None:
    """charts/<type>/examples/ must exist and contain at least one .json file."""
    examples_dir = CHARTS_DIR / chart_type / "examples"
    if not examples_dir.is_dir():
        return f"Directory {examples_dir.relative_to(ROOT)} does not exist"
    json_files = list(examples_dir.glob("*.json"))
    if not json_files:
        return f"No .json files found in {examples_dir.relative_to(ROOT)}"
    return None


def run_checks(chart_type: str) -> list[tuple[str, str | None]]:
    """Run all admission checks for a single chart type.

    Returns a list of (check_name, error_or_none) tuples.
    """
    decisions_text = _load_decisions_text()
    type_enum = _load_schema_type_enum()

    return [
        ("Decision document (DEC-*)", check_decision_document(chart_type, decisions_text)),
        ("Schema registration", check_schema_registration(chart_type, type_enum)),
        ("Golden fixtures", check_golden_fixtures(chart_type)),
        ("Invalid fixtures", check_invalid_fixtures(chart_type)),
        ("Design document", check_design_document(chart_type)),
        ("Example specs", check_example_specs(chart_type)),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify chart types meet the mandatory admission checklist (SC-ARCH-011). "
            "Checks decision approval, schema registration, golden fixtures, "
            "invalid fixtures, design document, and example specs."
        ),
    )
    parser.add_argument(
        "chart_types",
        nargs="+",
        metavar="CHART_TYPE",
        help="One or more chart type names to verify (e.g. line-basic scatter histogram)",
    )
    args = parser.parse_args()

    all_passed = True

    for chart_type in args.chart_types:
        print(f"\n{'=' * 60}")
        print(f"  Admission checks: {chart_type}")
        print(f"{'=' * 60}")

        chart_dir = CHARTS_DIR / chart_type
        if not chart_dir.is_dir():
            print(f"\n  SKIP  charts/{chart_type}/ directory does not exist\n")
            all_passed = False
            continue

        results = run_checks(chart_type)
        type_passed = True

        for check_name, error in results:
            if error is None:
                print(f"  PASS  {check_name}")
            else:
                print(f"  FAIL  {check_name}")
                print(f"        {error}")
                type_passed = False

        if type_passed:
            print(f"\n  All checks passed for '{chart_type}'.")
        else:
            print(f"\n  Some checks FAILED for '{chart_type}'.")
            all_passed = False

    print()
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
