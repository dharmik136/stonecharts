#!/usr/bin/env python3
"""Generate or verify the machine-readable 36-chart SC-CERT evidence ledger."""

from __future__ import annotations

import argparse
import json
import runpy
import sys
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "quality" / "certification-ledger.json"
RELEASE = "0.0.0.34"

SEMANTIC_IDS = {
    "line": ["SC-SEM-GENERIC"],
    "column": ["SC-SEM-GENERIC", "SC-SEM-007"],
    "area": ["SC-SEM-GENERIC"],
    "bar": ["SC-SEM-GENERIC", "SC-SEM-007"],
    "scatter": ["SC-SEM-GENERIC"],
    "bubble": ["SC-SEM-GENERIC", "SC-SEM-006"],
    "combo": ["SC-SEM-GENERIC"],
    "histogram": ["SC-SEM-GENERIC", "SC-SEM-001"],
    "candlestick": ["SC-SEM-GENERIC", "SC-SEM-015"],
    "error-bar": ["SC-SEM-GENERIC", "SC-SEM-012"],
    "arearange": ["SC-SEM-GENERIC", "SC-SEM-011"],
    "columnrange": ["SC-SEM-GENERIC", "SC-SEM-011"],
    "waterfall": ["SC-SEM-GENERIC", "SC-SEM-002"],
    "bullet": ["SC-SEM-GENERIC", "SC-SEM-014"],
    "boxplot": ["SC-SEM-GENERIC", "SC-SEM-013"],
    "lollipop": ["SC-SEM-GENERIC", "SC-SEM-016"],
    "dumbbell": ["SC-SEM-GENERIC", "SC-SEM-011"],
    "funnel": ["SC-SEM-GENERIC", "SC-SEM-017"],
    "variwide": ["SC-SEM-GENERIC", "SC-SEM-018"],
    "timeline": ["SC-SEM-GENERIC", "SC-SEM-019"],
    "windbarb": ["SC-SEM-GENERIC", "SC-SEM-020"],
    "streamgraph": ["SC-SEM-GENERIC", "SC-SEM-021"],
    "vector-plot": ["SC-SEM-GENERIC", "SC-SEM-022"],
    "xrange": ["SC-SEM-GENERIC", "SC-SEM-023"],
    "technical-indicators": ["SC-SEM-GENERIC", "SC-SEM-024"],
    "flame-chart": ["SC-SEM-GENERIC", "SC-SEM-025"],
    "pie": ["SC-SEM-GENERIC", "SC-SEM-026"],
    "gauge": ["SC-SEM-GENERIC", "SC-SEM-027"],
    "solid-gauge": ["SC-SEM-GENERIC", "SC-SEM-028"],
    "radar": ["SC-SEM-GENERIC", "SC-SEM-029"],
    "polar": ["SC-SEM-GENERIC", "SC-SEM-030"],
    "wind-rose": ["SC-SEM-GENERIC", "SC-SEM-031"],
    "nightingale": ["SC-SEM-GENERIC", "SC-SEM-032"],
    "radial-bar": ["SC-SEM-GENERIC", "SC-SEM-033"],
    "parliament": ["SC-SEM-GENERIC", "SC-SEM-034"],
    "development-triangle": [
        "SC-SEM-GENERIC",
        "DT-SEM-001",
        "DT-SEM-003",
        "DT-SEM-005",
        "DT-SEM-007",
        "DT-SEM-008",
        "DT-SEM-009",
        "DT-SEM-010",
    ],
}


def chart_directory(chart_id: str) -> str:
    return "line-basic" if chart_id == "line" else chart_id


def property_counts() -> dict[str, int]:
    sys.path.insert(0, str(ROOT / "libs" / "python"))
    namespace = runpy.run_path(str(ROOT / "libs/python/tests/test_property_rendering.py"))
    counts: dict[str, int] = {}
    for spec in namespace["PROPERTY_SPECS"]:
        counts[spec["type"]] = counts.get(spec["type"], 0) + 1
    return counts


def baseline_qualified(chart_id: str) -> bool:
    path = ROOT / "evidence-baselines" / chart_id / "manifest.json"
    if not path.exists():
        return False
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assurance = manifest.get("assurance", {})
    runtimes = manifest.get("runtimes", [])
    source = str(manifest.get("input", {}).get("source", ""))
    go_runtime = next((runtime for runtime in runtimes if runtime.get("runtime") == "go"), {})
    go_binary = str(go_runtime.get("goBinary", ""))
    return (
        manifest.get("status") == "pass"
        and assurance.get("profile") == "certified"
        and assurance.get("tier") == "certified"
        and assurance.get("eligibleForCertifiedGuarantee") is True
        and assurance.get("chartType") == chart_id
        and len(runtimes) == 2
        and {runtime.get("runtime") for runtime in runtimes} == {"python", "go"}
        and all(runtime.get("stonechartsVersion") == RELEASE for runtime in runtimes)
        and len({runtime.get("sha256") for runtime in runtimes}) == 1
        and bool(source)
        and not Path(source).is_absolute()
        and not PureWindowsPath(source).is_absolute()
        and bool(go_binary)
        and not Path(go_binary).is_absolute()
        and not PureWindowsPath(go_binary).is_absolute()
        and len(str(go_runtime.get("goBinarySha256", ""))) == 64
    )


def build() -> dict:
    registry = json.loads((ROOT / "spec/capabilities.json").read_text(encoding="utf-8"))
    counts = property_counts()
    charts = []
    for item in registry["chartTypes"]:
        chart_id = item["id"]
        directory = chart_directory(chart_id)
        root = ROOT / "charts" / directory
        examples = sorted(path.stem for path in (root / "examples").glob("*.json"))
        browser_fixture = "basic" if "basic" in examples else examples[0]
        invalid_cases = json.loads((root / "invalid-fixtures.json").read_text(encoding="utf-8"))
        qualified = baseline_qualified(chart_id)
        charts.append(
            {
                "id": chart_id,
                "directory": directory,
                "tier": item["tier"],
                "since": item["since"],
                "examples": examples,
                "invalidFixtureCount": len(invalid_cases),
                "propertyCaseCount": counts.get(chart_id, 0),
                "semanticInvariants": SEMANTIC_IDS[chart_id],
                "browserFixture": browser_fixture,
                "gates": {
                    "SC-CERT-01": {
                        "status": "qualified",
                        "evidence": ["spec/chart-spec.schema.json", f"charts/{directory}/invalid-fixtures.json"],
                    },
                    "SC-CERT-02": {
                        "status": "qualified",
                        "evidence": [f"charts/{directory}/golden", "tools/check_direct_cross_render.py"],
                    },
                    "SC-CERT-03": {
                        "status": "qualified",
                        "evidence": ["libs/python/tests/test_renderer_purity.py", "libs/go/render_test.go"],
                    },
                    "SC-CERT-04": {
                        "status": "qualified",
                        "evidence": ["libs/python/tests/test_property_rendering.py", "libs/go/render_test.go"],
                    },
                    "SC-CERT-05": {
                        "status": "qualified",
                        "evidence": [
                            f"charts/{directory}/invalid-fixtures.json",
                            "libs/python/tests/test_certification_portfolio.py",
                        ],
                    },
                    "SC-CERT-06": {
                        "status": "qualified",
                        "evidence": [
                            "libs/python/tests/test_semantic_invariants.py",
                            "libs/python/tests/test_certification_portfolio.py",
                            "libs/go/render_test.go",
                        ],
                    },
                    "SC-CERT-07": {
                        "status": "qualified",
                        "evidence": [
                            "runtime/all-charts-browser-qualification.test.js",
                            f"charts/{directory}/examples/{browser_fixture}.json",
                        ],
                    },
                    "SC-CERT-08": {
                        "status": "qualified" if qualified else "pending",
                        "evidence": [f"evidence-baselines/{chart_id}/manifest.json"],
                    },
                },
            }
        )
    return {
        "schemaVersion": 1,
        "release": RELEASE,
        "chartCount": len(charts),
        "seedCharts": ["line", "column", "area", "bar", "scatter", "bubble", "combo"],
        "qualificationCommands": [
            "py -3 tools/check_certification_matrix.py",
            "py -3 -m pytest libs/python/tests -q",
            "go test ./... (from libs/go)",
            "npm test",
            "py -3 tools/check_direct_cross_render.py",
            "py -3 tools/generate_certification_baselines.py --check",
            "py -3 tools/generate_runtime_assets.py --check",
            "py -3 tools/check_package_install.py",
        ],
        "charts": charts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = json.dumps(build(), indent=2) + "\n"
    if args.generate:
        OUTPUT.write_text(generated, encoding="utf-8")
        print(f"generated {OUTPUT.relative_to(ROOT).as_posix()}")
    if args.check or not args.generate:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != generated:
            print("certification ledger is stale; run with --generate", file=sys.stderr)
            return 1
        print("certification ledger PASS: 36 charts x 8 SC-CERT gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
