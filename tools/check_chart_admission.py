"""Verify chart types meet the mandatory admission checklist (SC-ARCH-011).

Runs in CI for the complete certified portfolio or for chart types supplied on the
command line. For each chart type, verifies that all required admission phases are
complete.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "libs" / "python"))

DECISIONS_PATH = ROOT / "docs" / "project" / "decisions.md"
SCHEMA_PATH = ROOT / "spec" / "chart-spec.schema.json"
CAPABILITIES_PATH = ROOT / "spec" / "capabilities.json"
CHARTS_DIR = ROOT / "charts"
PYTHON_CHARTS_DIR = ROOT / "libs" / "python" / "stonecharts" / "charts"
GO_DIR = ROOT / "libs" / "go"

DIR_TO_TYPE = {"line-basic": "line"}
TYPE_TO_DIR = {value: key for key, value in DIR_TO_TYPE.items()}


def _load_schema_type_enum() -> list[str]:
    """Return the list of accepted chart type strings from the spec schema."""
    with SCHEMA_PATH.open(encoding="utf-8") as fh:
        schema = json.load(fh)
    return list(schema["properties"]["type"]["enum"])


def _load_decisions_text() -> str:
    """Return the full text of the decision register."""
    return DECISIONS_PATH.read_text(encoding="utf-8")


def _schema_type(chart_dir: str) -> str:
    """Map a chart directory name to its schema type identifier."""
    return DIR_TO_TYPE.get(chart_dir, chart_dir)


def _certified_chart_directories() -> list[str]:
    """Return every certified chart's repository directory in registry order."""
    registry = json.loads(CAPABILITIES_PATH.read_text(encoding="utf-8"))
    chart_ids = [item["id"] for item in registry["chartTypes"] if item["tier"] == "certified"]
    return [TYPE_TO_DIR.get(chart_id, chart_id) for chart_id in chart_ids]


def check_decision_document(chart_type: str, decisions_text: str) -> str | None:
    """A DEC-* reference that mentions *chart_type* must exist in decisions.md."""
    lookup = _schema_type(chart_type)
    for line in decisions_text.splitlines():
        if "DEC-" in line and lookup in line:
            return None
    return f"No DEC-* reference mentioning '{lookup}' found in {DECISIONS_PATH.relative_to(ROOT)}"


def check_schema_registration(chart_type: str, type_enum: list[str]) -> str | None:
    """The chart type string must appear in the schema's type enum."""
    lookup = _schema_type(chart_type)
    if lookup in type_enum:
        return None
    return (
        f"'{lookup}' not found in {SCHEMA_PATH.relative_to(ROOT)} type enum (registered types: {', '.join(type_enum)})"
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


def check_python_renderer(chart_type: str) -> str | None:
    """Phase 3: Python renderer module must exist."""
    type_id = _schema_type(chart_type)
    py_id = type_id.replace("-", "_")
    path = PYTHON_CHARTS_DIR / f"{py_id}.py"
    if not path.is_file():
        return f"Python renderer {path.relative_to(ROOT)} does not exist"
    return None


def check_go_renderer(chart_type: str) -> str | None:
    """Phase 3: Go renderer file must exist."""
    type_id = _schema_type(chart_type)
    candidates = [
        GO_DIR / f"{type_id.replace('-', '_')}.go",
        GO_DIR / f"{type_id.replace('-', '')}.go",
    ]
    if any(p.is_file() for p in candidates):
        return None
    return f"Go renderer {candidates[0].relative_to(ROOT)} does not exist"


def check_capabilities_registration(chart_type: str) -> str | None:
    """Phase 3: Chart type must be listed in the capabilities manifest."""
    type_id = _schema_type(chart_type)
    from stonecharts.capabilities import capabilities

    cap_types = capabilities()["chartTypes"]
    if type_id not in cap_types:
        return f"'{type_id}' not in capabilities chartTypes: {cap_types}"
    return None


def check_adversarial_fixture(chart_type: str) -> str | None:
    """Phase 4: An adversarial example must exist for edge-case coverage."""
    adversarial = CHARTS_DIR / chart_type / "examples" / "adversarial.json"
    if not adversarial.is_file():
        return f"No adversarial example at {adversarial.relative_to(ROOT)}"
    return None


def check_cross_render_corpus(chart_type: str) -> str | None:
    """Phase 5: Chart type must be in the direct cross-render ACTIVE corpus."""
    cross_render = ROOT / "tools" / "check_direct_cross_render.py"
    if not cross_render.is_file():
        return None
    text = cross_render.read_text(encoding="utf-8")
    if f'"{chart_type}"' in text:
        return None
    return f"'{chart_type}' not in check_direct_cross_render.py ACTIVE corpus"


def run_checks(chart_type: str) -> list[tuple[str, str | None]]:
    """Run all admission checks for a single chart type.

    Returns a list of (check_name, error_or_none) tuples.
    """
    decisions_text = _load_decisions_text()
    type_enum = _load_schema_type_enum()

    return [
        ("Decision document (DEC-*)", check_decision_document(chart_type, decisions_text)),
        ("Schema registration", check_schema_registration(chart_type, type_enum)),
        ("Design document", check_design_document(chart_type)),
        ("Python renderer", check_python_renderer(chart_type)),
        ("Go renderer", check_go_renderer(chart_type)),
        ("Capabilities manifest", check_capabilities_registration(chart_type)),
        ("Golden fixtures", check_golden_fixtures(chart_type)),
        ("Invalid fixtures", check_invalid_fixtures(chart_type)),
        ("Adversarial fixture", check_adversarial_fixture(chart_type)),
        ("Example specs", check_example_specs(chart_type)),
        ("Cross-render corpus", check_cross_render_corpus(chart_type)),
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
        nargs="*",
        metavar="CHART_TYPE",
        help="One or more chart type names to verify (e.g. line-basic scatter histogram)",
    )
    parser.add_argument(
        "--all-certified",
        action="store_true",
        help="Verify every chart marked certified in spec/capabilities.json",
    )
    args = parser.parse_args()
    if args.all_certified and args.chart_types:
        parser.error("--all-certified cannot be combined with explicit chart types")
    chart_types = _certified_chart_directories() if args.all_certified else args.chart_types
    if not chart_types:
        parser.error("provide at least one chart type or use --all-certified")

    all_passed = True

    for chart_type in chart_types:
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
