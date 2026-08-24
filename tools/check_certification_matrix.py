#!/usr/bin/env python3
"""Execute and verify the complete per-chart SC-CERT evidence matrix."""

from __future__ import annotations

import argparse
import copy
import json
import runpy
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/quality/certification-ledger.json"
CAPABILITIES = ROOT / "spec/capabilities.json"
SCHEMA = ROOT / "spec/chart-spec.schema.json"
RELEASE = "0.0.0.34"

sys.path.insert(0, str(ROOT / "libs/python"))
from stonecharts import ChartSpec
from stonecharts.render import render_svg
from stonecharts.validate import validate


def run(command: list[str], *, cwd: Path = ROOT) -> tuple[bool, str]:
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return process.returncode == 0, (process.stdout + process.stderr).strip()


def baseline_ok(chart_id: str) -> tuple[bool, str]:
    path = ROOT / "evidence-baselines" / chart_id / "manifest.json"
    if not path.exists():
        return False, "baseline manifest missing"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assurance = manifest.get("assurance", {})
    runtimes = manifest.get("runtimes", [])
    source = str(manifest.get("input", {}).get("source", ""))
    go_runtime = next((runtime for runtime in runtimes if runtime.get("runtime") == "go"), {})
    go_binary = str(go_runtime.get("goBinary", ""))
    checks = {
        "status": manifest.get("status") == "pass",
        "profile": assurance.get("profile") == "certified",
        "tier": assurance.get("tier") == "certified",
        "eligible": assurance.get("eligibleForCertifiedGuarantee") is True,
        "chartType": assurance.get("chartType") == chart_id,
        "runtimes": {runtime.get("runtime") for runtime in runtimes} == {"python", "go"},
        "version": bool(runtimes) and all(runtime.get("stonechartsVersion") == RELEASE for runtime in runtimes),
        "parity": len(runtimes) == 2 and len({runtime.get("sha256") for runtime in runtimes}) == 1,
        "relativeSource": bool(source) and not Path(source).is_absolute() and not PureWindowsPath(source).is_absolute(),
        "portableGoBinary": bool(go_binary)
        and not Path(go_binary).is_absolute()
        and not PureWindowsPath(go_binary).is_absolute(),
        "hashedGoBinary": len(str(go_runtime.get("goBinarySha256", ""))) == 64,
    }
    missing = [name for name, passed in checks.items() if not passed]
    return not missing, ", ".join(missing)


def structural_checks() -> list[str]:
    failures: list[str] = []
    if not LEDGER.exists():
        return ["certification ledger missing"]

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    registry = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator_class = jsonschema.validators.validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema)

    expected = [item["id"] for item in registry["chartTypes"] if item["tier"] == "certified"]
    entries = ledger.get("charts", [])
    actual = [entry.get("id") for entry in entries]
    if ledger.get("release") != RELEASE:
        failures.append(f"ledger release must be {RELEASE}")
    if ledger.get("chartCount") != 36 or len(expected) != 36 or actual != expected:
        failures.append("ledger and capability registry must contain the same ordered 36-chart inventory")

    property_namespace = runpy.run_path(str(ROOT / "libs/python/tests/test_property_rendering.py"))
    property_counts: dict[str, int] = {}
    for spec in property_namespace["PROPERTY_SPECS"]:
        property_counts[spec["type"]] = property_counts.get(spec["type"], 0) + 1

    python_semantics = (ROOT / "libs/python/tests/test_semantic_invariants.py").read_text(encoding="utf-8")
    python_portfolio = (ROOT / "libs/python/tests/test_certification_portfolio.py").read_text(encoding="utf-8")
    go_tests = (ROOT / "libs/go/render_test.go").read_text(encoding="utf-8")
    browser_test = (ROOT / "runtime/all-charts-browser-qualification.test.js").read_text(encoding="utf-8")

    for entry in entries:
        chart_id = entry["id"]
        directory = entry["directory"]
        chart_root = ROOT / "charts" / directory
        gates = entry.get("gates", {})
        if set(gates) != {f"SC-CERT-{index:02d}" for index in range(1, 9)}:
            failures.append(f"{chart_id}: incomplete eight-gate ledger")
        elif any(gate.get("status") != "qualified" for gate in gates.values()):
            failures.append(f"{chart_id}: one or more SC-CERT gates are not qualified")

        examples = sorted((chart_root / "examples").glob("*.json"), key=lambda path: path.stem)
        goldens = sorted((chart_root / "golden").glob("*.svg"), key=lambda path: path.stem)
        if [path.stem for path in examples] != sorted(entry.get("examples", [])):
            failures.append(f"{chart_id}: example inventory drift")
        if {path.stem for path in examples} != {path.stem for path in goldens}:
            failures.append(f"{chart_id}: examples and goldens differ")

        for example in examples:
            raw = json.loads(example.read_text(encoding="utf-8"))
            if list(validator.iter_errors(raw)) or validate(raw):
                failures.append(f"{chart_id}/{example.name}: valid fixture rejected")
                continue
            spec = ChartSpec.from_dict(raw)
            before = copy.deepcopy(spec)
            svg = render_svg(spec)
            if spec != before:
                failures.append(f"{chart_id}/{example.name}: Python renderer mutated input")
            golden = chart_root / "golden" / f"{example.stem}.svg"
            if svg != golden.read_text(encoding="utf-8"):
                failures.append(f"{chart_id}/{example.name}: Python output differs from golden")

        invalid_path = chart_root / "invalid-fixtures.json"
        invalid_cases = json.loads(invalid_path.read_text(encoding="utf-8"))
        if len(invalid_cases) != entry.get("invalidFixtureCount") or len(invalid_cases) < 3:
            failures.append(f"{chart_id}: invalid fixture inventory drift")
        for index, case in enumerate(invalid_cases):
            raw = case["spec"]
            rejected = bool(list(validator.iter_errors(raw)) or validate(raw))
            if not rejected:
                try:
                    render_svg(ChartSpec.from_dict(raw))
                except (TypeError, ValueError):
                    rejected = True
            if not rejected:
                failures.append(f"{chart_id}: invalid fixture {index} was accepted")

        if property_counts.get(chart_id, 0) != entry.get("propertyCaseCount") or property_counts.get(chart_id, 0) < 8:
            failures.append(f"{chart_id}: fewer than eight named property cases")

        semantic_ids = entry.get("semanticInvariants", [])
        if not semantic_ids or semantic_ids[0] != "SC-SEM-GENERIC":
            failures.append(f"{chart_id}: generic semantic floor missing")
        if "test_certified_chart_contract_and_semantic_floor" not in python_portfolio:
            failures.append("portfolio semantic test missing")
        for semantic_id in semantic_ids[1:]:
            if semantic_id not in python_semantics or semantic_id not in go_tests:
                failures.append(f"{chart_id}: {semantic_id} missing from a language suite")

        browser_fixture = chart_root / "examples" / f"{entry.get('browserFixture')}.json"
        if not browser_fixture.exists() or "fixtures.length, 36" not in browser_test:
            failures.append(f"{chart_id}: browser fixture or portfolio assertion missing")

        baseline_passed, detail = baseline_ok(chart_id)
        if not baseline_passed:
            failures.append(f"{chart_id}: baseline is not certified for {RELEASE} ({detail})")
        if gates.get("SC-CERT-08", {}).get("status") != "qualified":
            failures.append(f"{chart_id}: ledger baseline gate is not qualified")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structural-only", action="store_true", help="Skip executable language/browser suites")
    args = parser.parse_args()

    failures = structural_checks()
    if failures:
        print("certification matrix FAILED", file=sys.stderr)
        for message in failures:
            print(f"- {message}", file=sys.stderr)
        return 1

    if not args.structural_only:
        commands = [
            (
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "libs/python/tests/test_certification_portfolio.py",
                    "libs/python/tests/test_property_rendering.py",
                    "libs/python/tests/test_renderer_purity.py",
                    "libs/python/tests/test_semantic_invariants.py",
                    "-q",
                ],
                ROOT,
            ),
            (
                [
                    "go",
                    "test",
                    ".",
                    "-run",
                    "TestGolden|TestRendererPurity|TestRandomizedAll36Types|TestSemanticInvariants",
                ],
                ROOT / "libs/go",
            ),
            ([sys.executable, "tools/check_direct_cross_render.py"], ROOT),
            (["node", "--test", "runtime/all-charts-browser-qualification.test.js"], ROOT),
        ]
        for command, cwd in commands:
            passed, output = run(command, cwd=cwd)
            if output:
                print(output)
            if not passed:
                print(f"certification matrix FAILED: {' '.join(command)}", file=sys.stderr)
                return 1

    print("certification matrix PASS: 36 charts x 8 executable SC-CERT gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
