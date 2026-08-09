"""Unit checks for the first StoneVerify proof tool."""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest
from stonecharts.verify.result import SCHEMA_VERSION

ROOT = pathlib.Path(__file__).resolve().parents[3]
VERIFY_PATH = ROOT / "tools" / "stonecharts_verify.py"

spec = importlib.util.spec_from_file_location("stonecharts_verify", VERIFY_PATH)
stonecharts_verify = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stonecharts_verify)

SVG_BASIC = (
    b'<svg class="sc-chart" role="img">'
    b'<g class="sc-series" data-series="0">'
    b'<path class="sc-series-line" data-series="0" d="M0,0 L10,10" stroke="#ff0000"/>'
    b'<circle class="sc-point" data-series="0" cx="10" cy="10" r="3.5"/>'
    b"</g></svg>"
)


@pytest.fixture(scope="session")
def stoneverify_go_binary(tmp_path_factory):
    if shutil.which("go") is None:
        pytest.skip("Go toolchain is not available")

    binary = tmp_path_factory.mktemp("go-adapter") / (
        "stoneverify-go-render.exe" if os.name == "nt" else "stoneverify-go-render"
    )
    build = subprocess.run(
        ["go", "build", "-o", str(binary), "./cmd/stoneverify-go-render"],
        cwd=ROOT / "libs/go",
        capture_output=True,
    )
    assert build.returncode == 0, build.stderr.decode()
    return binary


def test_classify_semantic_byte_equal():
    result = stonecharts_verify.classify_semantic(SVG_BASIC, SVG_BASIC)

    assert result["equality"] == "byte"
    assert result["category"] == "unknown-structural"
    assert result["confidence"] == "high"
    assert result["basis"] == ["byte-identical"]


def test_classify_semantic_geometry_change():
    changed = SVG_BASIC.replace(b'd="M0,0 L10,10"', b'd="M0,0 L20,20"')

    result = stonecharts_verify.classify_semantic(SVG_BASIC, changed)

    assert result["category"] == "geometry"
    assert result["equality"] == "unknown"
    assert result["confidence"] == "high"
    assert any("d" in basis for basis in result["basis"])


def test_classify_semantic_theme_change():
    changed = SVG_BASIC.replace(b'stroke="#ff0000"', b'stroke="#00ff00"')

    result = stonecharts_verify.classify_semantic(SVG_BASIC, changed)

    assert result["category"] == "theme-style"
    assert result["equality"] == "semantic"
    assert result["confidence"] == "high"
    assert any("stroke" in basis for basis in result["basis"])


def test_classify_semantic_accessibility_change():
    changed = SVG_BASIC.replace(b'role="img"', b'role="figure"')

    result = stonecharts_verify.classify_semantic(SVG_BASIC, changed)

    assert result["category"] == "accessibility-metadata"
    assert result["equality"] == "semantic"
    assert result["confidence"] == "high"


def test_classify_semantic_label_text_change():
    left = b'<svg role="img"><text class="sc-tt-title">Jan</text></svg>'
    right = b'<svg role="img"><text class="sc-tt-title">Feb</text></svg>'

    result = stonecharts_verify.classify_semantic(left, right)

    assert result["category"] == "label-text"
    assert result["equality"] == "unknown"
    assert result["confidence"] == "high"


def test_classify_semantic_input_data_change():
    left = b'<svg role="img"><circle class="sc-point" data-x="Jan" data-y="10" cx="10" cy="80" r="3.5"/></svg>'
    right = b'<svg role="img"><circle class="sc-point" data-x="Jan" data-y="12" cx="10" cy="70" r="3.5"/></svg>'

    result = stonecharts_verify.classify_semantic(left, right)

    assert result["category"] == "input-data"
    assert result["equality"] == "unknown"
    assert result["confidence"] == "high"
    assert any("data-y" in basis for basis in result["basis"])


def test_classify_semantic_scale_domain_change_when_data_is_stable():
    left = b'<svg role="img"><g class="sc-axis sc-axis-y"><text x="42" y="80">10</text></g><circle class="sc-point" data-y="10" cx="10" cy="80" r="3.5"/></svg>'
    right = b'<svg role="img"><g class="sc-axis sc-axis-y"><text x="42" y="60">10</text></g><circle class="sc-point" data-y="10" cx="10" cy="60" r="3.5"/></svg>'

    result = stonecharts_verify.classify_semantic(left, right)

    assert result["category"] == "scale-domain"
    assert result["equality"] == "unknown"
    assert result["confidence"] == "medium"
    assert any("cy" in basis or "[y]" in basis for basis in result["basis"])


def test_classify_semantic_malformed_input_falls_back_safely():
    result = stonecharts_verify.classify_semantic(b"<svg><unterminated", b"<svg><also-unterminated")

    assert result["category"] == "unknown-structural"
    assert result["equality"] == "unknown"
    assert result["confidence"] == "low"


def test_classify_semantic_whitespace_only_is_serialization_only():
    left = b'<svg role="img"><g class="sc-series"><path d="M0,0 L1,1"/></g></svg>'
    right = b'<svg role="img"><g class="sc-series"><path d="M0,0 L1,1"/></g></svg>\n'

    result = stonecharts_verify.classify_semantic(left, right)

    assert result["category"] == "serialization-only"
    assert result["equality"] == "structural"


def test_classify_semantic_attribute_ordering_is_serialization_only():
    left = b'<svg role="img" class="sc-chart"></svg>'
    right = b'<svg class="sc-chart" role="img"></svg>'

    result = stonecharts_verify.classify_semantic(left, right)

    assert result["category"] == "serialization-only"
    assert result["equality"] == "structural"


def test_classify_difference_includes_semantic_fields():
    left = b'<svg role="img"><g class="sc-series"><path d="M0,0 L1,1" stroke="#111"/></g></svg>'
    right = b'<svg role="img"><g class="sc-series"><path d="M0,0 L2,2" stroke="#111"/></g></svg>'

    result = stonecharts_verify.classify_difference(left, right, "left.svg", "right.svg")

    assert result["equal"] is False
    assert "likelyCause" in result
    assert "structural" in result
    assert result["category"] == "geometry"
    assert result["equality"] == "unknown"
    assert result["confidence"] == "high"
    assert isinstance(result["basis"], list) and result["basis"]


def test_classify_difference_equal_case_includes_semantic_fields():
    svg = b'<svg role="img"></svg>'

    result = stonecharts_verify.classify_difference(svg, svg, "left.svg", "right.svg")

    assert result["equal"] is True
    assert result["likelyCause"] == "none"
    assert result["equality"] == "byte"


def test_compare_outputs_passes_on_equal_svg():
    svg = b'<svg role="img"><g><text>same</text></g></svg>'

    comparison = stonecharts_verify.compare_outputs({"python": svg, "go": svg})

    assert comparison["status"] == "pass"
    assert comparison["equal"] is True
    assert comparison["pairs"][0]["visual"]["status"] == "equivalent-by-byte-identity"
    assert comparison["pairs"][0]["likelyCause"] == "none"


def test_compare_outputs_reports_structural_drift():
    comparison = stonecharts_verify.compare_outputs(
        {
            "python": b'<svg role="img"><g><circle /></g></svg>',
            "go": b'<svg role="img"><g><rect /></g></svg>',
        }
    )

    assert comparison["status"] == "fail"
    assert comparison["equal"] is False
    pair = comparison["pairs"][0]
    assert pair["structural"]["equalTagInventory"] is False
    assert pair["firstDifference"]["byteOffset"] > 0
    assert pair["visual"]["status"] == "not-computed"
    assert "structural renderer drift" in pair["likelyCause"]


def test_write_report_escapes_runtime_fields(tmp_path):
    report = tmp_path / "report.html"
    comparison = stonecharts_verify.compare_outputs(
        {"python": b"<svg><text>a</text></svg>", "go": b"<svg><text>b</text></svg>"}
    )
    manifest = {
        "input": {"sha256": "abc123"},
        "runtimes": [
            {
                "runtime": "python<script>",
                "output": "python-output.svg",
                "sha256": "left",
                "bytes": 24,
            },
            {
                "runtime": "go",
                "output": "go-output.svg",
                "sha256": "right",
                "bytes": 24,
            },
        ],
    }

    stonecharts_verify.write_report(report, manifest, comparison)

    html = report.read_text(encoding="utf-8")
    assert "StoneVerify Report: FAIL" in html
    assert "python&lt;script&gt;" in html
    assert "python<script>" not in html


def test_canonical_json_bytes_is_stable():
    first = stonecharts_verify.canonical_json_bytes({"b": 2, "a": [1, 3]})
    second = stonecharts_verify.canonical_json_bytes(json.loads('{"a":[1,3],"b":2}'))

    assert first == second
    assert first.endswith(b"\n")


def test_apply_demo_drift_text_is_explicit_and_structural():
    svg = b'<svg role="img"><g><text>same</text></g></svg>'

    drifted = stonecharts_verify.apply_demo_drift(svg, "text")
    comparison = stonecharts_verify.compare_outputs({"python": svg, "go": drifted})

    assert b"demo drift" in drifted
    assert comparison["status"] == "fail"
    assert comparison["pairs"][0]["structural"]["equalTagInventory"] is False


def test_apply_demo_drift_attribute_keeps_structure_but_changes_bytes():
    svg = b'<svg role="img"><g><text>same</text></g></svg>'

    drifted = stonecharts_verify.apply_demo_drift(svg, "attribute")
    comparison = stonecharts_verify.compare_outputs({"python": svg, "go": drifted})

    assert b'role="figure"' in drifted
    assert comparison["status"] == "fail"
    assert comparison["pairs"][0]["structural"]["equalTagInventory"] is True
    assert "attribute" in comparison["pairs"][0]["likelyCause"]


def test_compare_baseline_passes_when_hashes_match():
    current_manifest = {
        "input": {"sha256": "input-a"},
        "runtimes": [
            {"runtime": "python", "sha256": "svg-a"},
            {"runtime": "go", "sha256": "svg-a"},
        ],
    }
    baseline_manifest = {
        "input": {"sha256": "input-a"},
        "runtimes": [
            {"runtime": "python", "sha256": "svg-a"},
            {"runtime": "go", "sha256": "svg-a"},
        ],
    }

    baseline = stonecharts_verify.compare_baseline(
        current_manifest,
        {"python": b"<svg></svg>", "go": b"<svg></svg>"},
        baseline_manifest,
    )

    assert baseline["status"] == "pass"
    assert baseline["inputEqual"] is True
    assert all(item["equal"] for item in baseline["runtimes"])


def test_compare_baseline_fails_when_input_or_runtime_hash_changes():
    current_manifest = {
        "input": {"sha256": "input-b"},
        "runtimes": [
            {"runtime": "python", "sha256": "svg-a"},
            {"runtime": "go", "sha256": "svg-b"},
        ],
    }
    baseline_manifest = {
        "input": {"sha256": "input-a"},
        "runtimes": [
            {"runtime": "python", "sha256": "svg-a"},
            {"runtime": "go", "sha256": "svg-a"},
        ],
    }

    baseline = stonecharts_verify.compare_baseline(
        current_manifest,
        {"python": b"<svg></svg>", "go": b"<svg></svg>"},
        baseline_manifest,
    )

    assert baseline["status"] == "fail"
    assert baseline["inputEqual"] is False
    go_result = next(item for item in baseline["runtimes"] if item["runtime"] == "go")
    assert go_result["equal"] is False
    assert go_result["reason"] == "output hash changed from baseline"


def test_load_baseline_requires_manifest(tmp_path):
    missing = tmp_path / "missing-baseline"
    missing.mkdir()

    try:
        stonecharts_verify.load_baseline(missing)
    except FileNotFoundError as exc:
        assert "manifest.json" in str(exc)
    else:
        raise AssertionError("expected missing manifest to fail")


def test_check_evidence_bundle_passes_for_valid_bundle(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    files = {
        "input-spec.json": "{}\n",
        "comparison.json": '{"status":"pass"}\n',
        "report.html": "<!doctype html>\n",
        "python-output.svg": "<svg></svg>",
        "go-output.svg": "<svg></svg>",
    }
    manifest = {
        "schemaVersion": 1,
        "tool": "stonecharts_verify",
        "toolVersion": 1,
        "generatedAt": "2026-07-28T00:00:00+00:00",
        "status": "pass",
        "input": {"file": "input-spec.json", "sha256": "0" * 64, "bytes": 3},
        "comparison": "comparison.json",
        "report": "report.html",
        "baseline": {"status": "not-checked"},
        "runtimes": [
            {
                "runtime": "python",
                "output": "python-output.svg",
                "sha256": "1" * 64,
                "bytes": 11,
                "demoDriftApplied": "none",
            },
            {
                "runtime": "go",
                "output": "go-output.svg",
                "sha256": "1" * 64,
                "bytes": 11,
                "demoDriftApplied": "none",
            },
        ],
    }
    files["manifest.json"] = json.dumps(manifest, sort_keys=True) + "\n"
    for name, content in files.items():
        (evidence / name).write_text(content, encoding="utf-8")
    checksums = [f"{stonecharts_verify.sha256_file(evidence / name)}  {name}" for name in sorted(files)]
    (evidence / "checksums.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")

    result = stonecharts_verify.check_evidence_bundle(evidence)

    assert result["status"] == "pass"
    assert result["missing"] == []
    assert result["checksumErrors"] == []


def test_check_evidence_bundle_fails_on_tampered_file(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "manifest.json").write_text(
        json.dumps({"status": "pass", "runtimes": [{"runtime": "python", "output": "python-output.svg"}]}) + "\n",
        encoding="utf-8",
    )
    (evidence / "input-spec.json").write_text("{}\n", encoding="utf-8")
    (evidence / "comparison.json").write_text('{"status":"pass"}\n', encoding="utf-8")
    (evidence / "report.html").write_text("<!doctype html>\n", encoding="utf-8")
    (evidence / "python-output.svg").write_text("<svg>before</svg>", encoding="utf-8")
    checksum_names = ["manifest.json", "input-spec.json", "comparison.json", "report.html", "python-output.svg"]
    checksums = [f"{stonecharts_verify.sha256_file(evidence / name)}  {name}" for name in sorted(checksum_names)]
    (evidence / "checksums.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    (evidence / "python-output.svg").write_text("<svg>after</svg>", encoding="utf-8")

    result = stonecharts_verify.check_evidence_bundle(evidence)

    assert result["status"] == "fail"
    assert result["checksumErrors"] == ["checksum mismatch for python-output.svg"]


def test_check_evidence_bundle_enforces_bundle_size_limit(tmp_path, monkeypatch):
    evidence = tmp_path / "evidence"
    _write_valid_bundle(evidence)
    monkeypatch.setitem(stonecharts_verify.evidence_bundle_size.__globals__, "MAX_EVIDENCE_BUNDLE_BYTES", 10)

    try:
        stonecharts_verify.check_evidence_bundle(evidence)
    except stonecharts_verify.ResourceLimitError as exc:
        assert exc.code == "LIMIT.EVIDENCE_BUNDLE_BYTES"
    else:
        raise AssertionError("expected evidence bundle size limit")


def test_validate_manifest_shape_reports_missing_and_invalid_fields():
    manifest = {
        "tool": "wrong",
        "toolVersion": "1",
        "status": "maybe",
        "generatedAt": "",
        "input": {"file": 7, "sha256": "bad", "bytes": -1},
        "runtimes": [
            {
                "runtime": "python",
                "output": "python-output.svg",
                "sha256": "0" * 64,
                "bytes": 10,
                "demoDriftApplied": "none",
            },
            {
                "runtime": "python",
                "output": "not-svg.txt",
                "sha256": "bad",
                "bytes": -2,
                "demoDriftApplied": "surprise",
            },
        ],
        "baseline": {"status": "unknown"},
    }

    errors = stonecharts_verify.validate_manifest_shape(manifest)

    assert "manifest.tool must be stonecharts_verify" in errors
    assert "manifest.toolVersion must be an integer" in errors
    assert "manifest.status must be pass or fail" in errors
    assert "manifest.generatedAt must be a non-empty string" in errors
    assert "manifest.runtimes[1].runtime duplicates python" in errors
    assert "manifest.baseline.status must be pass, fail, or not-checked" in errors


def test_check_evidence_bundle_fails_on_malformed_manifest(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "manifest.json").write_text(
        json.dumps({"tool": "wrong", "runtimes": []}) + "\n",
        encoding="utf-8",
    )
    (evidence / "input-spec.json").write_text("{}\n", encoding="utf-8")
    (evidence / "comparison.json").write_text('{"status":"pass"}\n', encoding="utf-8")
    (evidence / "report.html").write_text("<!doctype html>\n", encoding="utf-8")
    checksum_names = ["manifest.json", "input-spec.json", "comparison.json", "report.html"]
    checksums = [f"{stonecharts_verify.sha256_file(evidence / name)}  {name}" for name in sorted(checksum_names)]
    (evidence / "checksums.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")

    result = stonecharts_verify.check_evidence_bundle(evidence)

    assert result["status"] == "fail"
    assert "manifest.tool must be stonecharts_verify" in result["manifestErrors"]
    assert "manifest.runtimes must be a non-empty array" in result["manifestErrors"]


def _write_valid_bundle(
    evidence: pathlib.Path,
    runtime_svg: str = "<svg></svg>",
    input_sha: str = "0" * 64,
    runtimes: tuple[str, ...] = ("python", "go"),
) -> None:
    evidence.mkdir()
    files = {
        "input-spec.json": "{}\n",
        "comparison.json": '{"status":"pass"}\n',
        "report.html": "<!doctype html>\n",
    }
    for runtime in runtimes:
        files[f"{runtime}-output.svg"] = runtime_svg
    manifest = {
        "schemaVersion": 1,
        "tool": "stonecharts_verify",
        "toolVersion": 1,
        "generatedAt": "2026-07-28T00:00:00+00:00",
        "status": "pass",
        "input": {"file": "input-spec.json", "sha256": input_sha, "bytes": 3},
        "comparison": "comparison.json",
        "report": "report.html",
        "baseline": {"status": "not-checked"},
        "runtimes": [
            {
                "runtime": runtime,
                "output": f"{runtime}-output.svg",
                "sha256": stonecharts_verify.sha256_bytes(runtime_svg.encode("utf-8")),
                "bytes": len(runtime_svg.encode("utf-8")),
                "demoDriftApplied": "none",
            }
            for runtime in runtimes
        ],
    }
    files["manifest.json"] = json.dumps(manifest, sort_keys=True) + "\n"
    for name, content in files.items():
        (evidence / name).write_text(content, encoding="utf-8")
    checksums = [f"{stonecharts_verify.sha256_file(evidence / name)}  {name}" for name in sorted(files)]
    (evidence / "checksums.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")


def test_compare_evidence_bundles_passes_for_matching_bundles(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    _write_valid_bundle(left)
    _write_valid_bundle(right)

    result = stonecharts_verify.compare_evidence_bundles(left, right)

    assert result["status"] == "pass"
    assert result["runtimes"]
    assert all(item["equal"] for item in result["runtimes"])


def test_compare_evidence_bundles_fails_for_different_outputs(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    _write_valid_bundle(left, "<svg>left</svg>")
    _write_valid_bundle(right, "<svg>right</svg>")

    result = stonecharts_verify.compare_evidence_bundles(left, right)

    assert result["status"] == "fail"
    assert any(not item["equal"] for item in result["runtimes"])


def test_compare_evidence_bundles_explains_each_runtime_difference(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    _write_valid_bundle(left, '<svg role="img"><g><text>same</text></g></svg>')
    _write_valid_bundle(right, '<svg role="img"><g><circle /></g></svg>')

    result = stonecharts_verify.compare_evidence_bundles(left, right)

    assert result["status"] == "fail"
    assert result["input"]["equal"] is True
    python_result = next(item for item in result["runtimes"] if item["runtime"] == "python")
    assert python_result["structural"]["equalTagInventory"] is False
    assert "structural renderer drift" in python_result["likelyCause"]
    assert python_result["firstDifference"]["byteOffset"] > 0
    assert python_result["leftBytes"] != python_result["rightBytes"]
    assert "same input spec rendered differently" in python_result["reason"]


def test_compare_evidence_bundles_separates_spec_change_from_renderer_drift(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    _write_valid_bundle(left, "<svg>left</svg>", input_sha="a" * 64)
    _write_valid_bundle(right, "<svg>right</svg>", input_sha="b" * 64)

    result = stonecharts_verify.compare_evidence_bundles(left, right)

    assert result["status"] == "fail"
    assert result["input"]["equal"] is False
    assert "different input specs" in result["message"]
    python_result = next(item for item in result["runtimes"] if item["runtime"] == "python")
    assert "input spec differs between bundles" in python_result["reason"]


def test_compare_evidence_bundles_fails_when_runtime_coverage_differs(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    _write_valid_bundle(left, runtimes=("python", "go"))
    _write_valid_bundle(right, runtimes=("python",))

    result = stonecharts_verify.compare_evidence_bundles(left, right)

    assert result["status"] == "fail"
    assert result["runtimeCoverage"]["onlyLeft"] == ["go"]
    assert result["runtimeCoverage"]["onlyRight"] == []
    assert "runtime coverage" in result["message"]
    go_result = next(item for item in result["runtimes"] if item["runtime"] == "go")
    assert go_result["equal"] is False
    assert go_result["rightSha256"] is None


def test_compare_evidence_bundles_enforces_finding_limit(tmp_path, monkeypatch):
    left = tmp_path / "left"
    right = tmp_path / "right"
    _write_valid_bundle(left, "<svg>left</svg>")
    _write_valid_bundle(right, "<svg>right</svg>")
    monkeypatch.setitem(stonecharts_verify.enforce_finding_limit.__globals__, "MAX_FINDINGS", 0)

    try:
        stonecharts_verify.compare_evidence_bundles(left, right)
    except stonecharts_verify.ResourceLimitError as exc:
        assert exc.code == "LIMIT.FINDING_COUNT"
    else:
        raise AssertionError("expected finding-count limit")


def test_compare_outputs_enforces_comparison_timeout(monkeypatch):
    monkeypatch.setitem(stonecharts_verify.comparison_deadline.__globals__, "COMPARISON_TIMEOUT_SECONDS", -1.0)

    try:
        stonecharts_verify.compare_outputs({"python": b"<svg>a</svg>", "go": b"<svg>b</svg>"})
    except stonecharts_verify.ResourceLimitError as exc:
        assert exc.code == "LIMIT.COMPARISON_TIMEOUT"
    else:
        raise AssertionError("expected comparison timeout")


def test_render_python_enforces_render_timeout(monkeypatch):
    import time as _time

    from stonecharts.verify import cli as _cli

    original = _cli._render_python_inner

    def slow_render(*args, **kwargs):
        _time.sleep(2)
        return original(*args, **kwargs)

    monkeypatch.setattr(_cli, "_render_python_inner", slow_render)
    monkeypatch.setattr(_cli, "RENDER_TIMEOUT_SECONDS", 0.01)

    try:
        _cli.render_python({"type": "line", "series": [{"name": "s", "data": [1]}]})
    except stonecharts_verify.ResourceLimitError as exc:
        assert exc.code == "LIMIT.RENDER_TIMEOUT"
    else:
        raise AssertionError("expected render timeout")


def test_write_compare_report_escapes_and_reports_status(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    _write_valid_bundle(left, "<svg><text>a</text></svg>")
    _write_valid_bundle(right, "<svg><text>b</text></svg>")
    result = stonecharts_verify.compare_evidence_bundles(left, right)
    result["runtimes"][0]["runtime"] = "python<script>"
    report = tmp_path / "compare-report.html"

    stonecharts_verify.write_compare_report(report, result)

    html = report.read_text(encoding="utf-8")
    assert "StoneVerify Compare: FAIL" in html
    assert "python&lt;script&gt;" in html
    assert "python<script>" not in html


def test_classify_difference_is_shared_by_both_comparison_paths(tmp_path):
    left_svg = b'<svg role="img"><g><text>same</text></g></svg>'
    right_svg = stonecharts_verify.apply_demo_drift(left_svg, "attribute")
    left = tmp_path / "left"
    right = tmp_path / "right"
    _write_valid_bundle(left, left_svg.decode("utf-8"))
    _write_valid_bundle(right, right_svg.decode("utf-8"))

    rendered = stonecharts_verify.compare_outputs({"python": left_svg, "go": right_svg})
    stored = stonecharts_verify.compare_evidence_bundles(left, right)

    python_result = next(item for item in stored["runtimes"] if item["runtime"] == "python")
    assert rendered["pairs"][0]["likelyCause"] == python_result["likelyCause"]
    assert python_result["structural"]["equalTagInventory"] is True


def test_compare_outputs_includes_schema_version():
    result = stonecharts_verify.compare_outputs({"python": b"<svg>a</svg>", "go": b"<svg>a</svg>"})

    assert result["schemaVersion"] == SCHEMA_VERSION
    # existing fields untouched
    assert result["status"] == "pass"
    assert result["equal"] is True
    assert "pairs" in result


def test_compare_outputs_single_runtime_includes_schema_version():
    result = stonecharts_verify.compare_outputs({"python": b"<svg>a</svg>"})

    assert result["schemaVersion"] == SCHEMA_VERSION
    assert result["pairs"] == []


def test_compare_baseline_not_checked_includes_schema_version():
    result = stonecharts_verify.compare_baseline({"input": {"sha256": "x"}, "runtimes": []}, {}, None)

    assert result["schemaVersion"] == SCHEMA_VERSION
    assert result["status"] == "not-checked"


def test_baseline_identity_includes_manifest_hash_tool_version_and_timestamp(tmp_path):
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    manifest = {
        "toolVersion": 1,
        "generatedAt": "2026-08-03T00:00:00+00:00",
        "input": {"sha256": "input-a"},
        "runtimes": [{"runtime": "python", "sha256": "svg-a"}],
    }
    (baseline / "manifest.json").write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")

    result = stonecharts_verify.compare_baseline(
        manifest,
        {"python": b"<svg></svg>"},
        manifest,
        baseline_dir=baseline,
        supersedes_baseline_dir=baseline,
        supersedes_baseline_manifest=manifest,
        note="approved in ticket SC-123",
    )

    assert result["identity"]["evidence"] == str(baseline)
    assert result["identity"]["manifestSha256"] == stonecharts_verify.sha256_file(baseline / "manifest.json")
    assert result["identity"]["toolVersion"] == 1
    assert result["identity"]["generatedAt"] == "2026-08-03T00:00:00+00:00"
    assert result["supersedes"]["manifestSha256"] == result["identity"]["manifestSha256"]
    assert result["note"] == "approved in ticket SC-123"


def test_manifest_includes_schema_version_and_environment(tmp_path):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    proc = subprocess.run(
        [sys.executable, str(VERIFY_PATH), str(spec_path), "--runtime", "python", "--evidence", str(evidence_dir)],
        capture_output=True,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stderr.decode()
    manifest = json.loads((evidence_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schemaVersion"] == 1
    env = manifest["environment"]
    for key in (
        "os",
        "arch",
        "pythonVersion",
        "stonechartsVersion",
        "stoneverifyVersion",
        "schemaVersion",
        "locale",
        "timezone",
    ):
        assert key in env
    # existing fields untouched
    assert manifest["tool"] == "stonecharts_verify"
    assert manifest["toolVersion"] == 1
    assert "input" in manifest and "runtimes" in manifest


def test_baseline_workflow_defaults_to_single_python_runtime(tmp_path):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    baseline_dir = tmp_path / "baseline"
    candidate_dir = tmp_path / "candidate"
    superseded_dir = tmp_path / "superseded"
    env = {**os.environ, "STONEVERIFY_GENERATED_AT": "2026-08-03T00:00:00+00:00"}

    subprocess.run(
        [sys.executable, str(VERIFY_PATH), str(spec_path), "--runtime", "python", "--evidence", str(superseded_dir)],
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(VERIFY_PATH), str(spec_path), "--runtime", "python", "--evidence", str(baseline_dir)],
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=True,
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            str(spec_path),
            "--baseline-evidence",
            str(baseline_dir),
            "--supersedes-baseline",
            str(superseded_dir),
            "--baseline-note",
            "approved baseline SC-123",
            "--evidence",
            str(candidate_dir),
        ],
        capture_output=True,
        cwd=ROOT,
        env=env,
    )

    assert proc.returncode == stonecharts_verify.EXIT_PASS, proc.stderr.decode()
    manifest = json.loads((candidate_dir / "manifest.json").read_text(encoding="utf-8"))
    assert [runtime["runtime"] for runtime in manifest["runtimes"]] == ["python"]
    baseline = manifest["baseline"]
    assert baseline["status"] == "pass"
    assert baseline["identity"]["evidence"] == str(baseline_dir.resolve())
    assert baseline["identity"]["manifestSha256"] == stonecharts_verify.sha256_file(baseline_dir / "manifest.json")
    assert baseline["supersedes"]["evidence"] == str(superseded_dir.resolve())
    assert baseline["note"] == "approved baseline SC-123"


def test_manifest_evidence_block_is_algorithm_qualified(tmp_path):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    proc = subprocess.run(
        [sys.executable, str(VERIFY_PATH), str(spec_path), "--runtime", "python", "--evidence", str(evidence_dir)],
        capture_output=True,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stderr.decode()
    manifest = json.loads((evidence_dir / "manifest.json").read_text(encoding="utf-8"))
    evidence = manifest["evidence"]
    assert evidence["inputSpec"]["algorithm"] == "sha-256"
    assert evidence["inputSpec"]["value"] == manifest["input"]["sha256"]
    assert "python-output.svg" in evidence["artifacts"]
    assert evidence["artifacts"]["python-output.svg"]["algorithm"] == "sha-256"
    # checksums.txt format is untouched (still plain sha256sum-compatible text)
    checksums_text = (evidence_dir / "checksums.txt").read_text(encoding="utf-8")
    assert "  manifest.json" in checksums_text


def test_demo_drift_text_reports_semantic_fields(tmp_path, stoneverify_go_binary):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    junit_report = tmp_path / "junit.xml"
    proc = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            str(spec_path),
            "--runtime",
            "python",
            "--runtime",
            "go",
            "--go-binary",
            str(stoneverify_go_binary),
            "--demo-drift",
            "text",
            "--evidence",
            str(evidence_dir),
            "--junit-report",
            str(junit_report),
        ],
        capture_output=True,
        cwd=ROOT,
    )

    assert proc.returncode == 1, proc.stdout.decode()
    comparison = json.loads((evidence_dir / "comparison.json").read_text(encoding="utf-8"))
    pair = comparison["pairs"][0]
    assert pair["category"] in {"chart-type-capability", "label-text", "unknown-structural"}
    assert pair["equality"] in {"structural", "semantic", "unknown"}
    assert pair["confidence"] in {"high", "medium", "low"}
    assert pair["basis"]
    root = ET.parse(junit_report).getroot()
    assert root.attrib["failures"] == "1"
    assert len(root.findall("testcase/failure")) == 1


def test_demo_drift_attribute_reports_accessibility_category(tmp_path, stoneverify_go_binary):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    proc = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            str(spec_path),
            "--runtime",
            "python",
            "--runtime",
            "go",
            "--go-binary",
            str(stoneverify_go_binary),
            "--demo-drift",
            "attribute",
            "--evidence",
            str(evidence_dir),
        ],
        capture_output=True,
        cwd=ROOT,
    )

    assert proc.returncode == 1, proc.stdout.decode()
    comparison = json.loads((evidence_dir / "comparison.json").read_text(encoding="utf-8"))
    pair = comparison["pairs"][0]
    assert pair["category"] == "accessibility-metadata"
    assert pair["equality"] == "semantic"
    assert pair["confidence"] == "high"
    assert pair["findings"][0]["code"] == "VERIFY.ACCESSIBILITY.METADATA_CHANGED"


def test_manifest_only_adds_schema_version_environment_and_evidence(tmp_path):
    """Pins WORK-VERIFY-014A's compatibility promise: no existing manifest.json
    key changed shape, and exactly three new top-level keys were added.

    ``baseline`` is included in ``pre_014a_keys`` (not ``new_keys``) because
    ``main()`` calls ``compare_baseline()`` and assigns ``manifest["baseline"]``
    unconditionally, regardless of whether ``--baseline-evidence`` was passed
    (see tools/stonecharts_verify.py, compare_baseline's ``if baseline_manifest
    is None`` branch still returns a dict with status "not-checked" rather than
    omitting the key).
    """
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    subprocess.run(
        [sys.executable, str(VERIFY_PATH), str(spec_path), "--runtime", "python", "--evidence", str(evidence_dir)],
        capture_output=True,
        cwd=ROOT,
        check=True,
    )
    manifest = json.loads((evidence_dir / "manifest.json").read_text(encoding="utf-8"))
    pre_014a_keys = {
        "tool",
        "toolVersion",
        "generatedAt",
        "status",
        "demoDrift",
        "input",
        "runtimes",
        "comparison",
        "report",
        "baseline",
    }
    new_keys = {"schemaVersion", "environment", "evidence"}
    assert set(manifest.keys()) == pre_014a_keys | new_keys


def test_comparison_json_only_adds_schema_version(tmp_path, stoneverify_go_binary):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            str(spec_path),
            "--runtime",
            "python",
            "--runtime",
            "go",
            "--go-binary",
            str(stoneverify_go_binary),
            "--evidence",
            str(evidence_dir),
        ],
        capture_output=True,
        cwd=ROOT,
        check=True,
    )
    comparison = json.loads((evidence_dir / "comparison.json").read_text(encoding="utf-8"))
    assert set(comparison.keys()) == {"schemaVersion", "status", "equal", "message", "pairs"}


def test_compare_outputs_adds_stable_finding_codes():
    result = stonecharts_verify.compare_outputs(
        {
            "python": b'<svg role="img"><text>a</text></svg>',
            "go": b'<svg role="img"><text>b</text></svg>',
        }
    )

    finding = result["pairs"][0]["findings"][0]
    assert finding["code"] == "VERIFY.LABEL.TEXT_CHANGED"
    assert finding["category"] == "label-text"


def test_junit_report_pass_has_zero_failures(tmp_path):
    report = tmp_path / "junit.xml"
    comparison = stonecharts_verify.compare_outputs({"python": b"<svg/>", "go": b"<svg/>"})

    stonecharts_verify.write_junit_report(report, None, comparison)
    stonecharts_verify.validate_junit_report(report)

    root = ET.parse(report).getroot()
    assert root.tag == "testsuite"
    assert root.attrib["tests"] == "1"
    assert root.attrib["failures"] == "0"


def test_junit_report_failure_contains_semantic_finding_text(tmp_path):
    report = tmp_path / "junit.xml"
    comparison = stonecharts_verify.compare_outputs(
        {
            "python": b'<svg role="img"><text>a</text></svg>',
            "go": b'<svg role="img"><text>b</text></svg>',
        }
    )

    stonecharts_verify.write_junit_report(report, None, comparison)
    stonecharts_verify.validate_junit_report(report)

    root = ET.parse(report).getroot()
    failure = root.find("testcase/failure")
    assert failure is not None
    assert root.attrib["failures"] == "1"
    assert "VERIFY.LABEL.TEXT_CHANGED" in (failure.text or "")
    assert "category=label-text" in (failure.text or "")


def test_github_actions_output_writes_annotation_and_summary(tmp_path, monkeypatch, capsys):
    summary = tmp_path / "summary.md"
    comparison = stonecharts_verify.compare_outputs(
        {
            "python": b'<svg role="img"><text>a</text></svg>',
            "go": b'<svg role="img"><text>b</text></svg>',
        }
    )
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    stonecharts_verify.emit_github_actions_output(None, comparison)

    captured = capsys.readouterr()
    assert "::error title=StoneVerify " in captured.out
    assert "VERIFY.LABEL.TEXT_CHANGED" in captured.out
    assert "Status: **FAIL**" in summary.read_text(encoding="utf-8")


def test_single_demo_drift_run_keeps_all_output_formats_aligned(tmp_path, stoneverify_go_binary):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    junit_report = evidence_dir / "junit.xml"
    summary = tmp_path / "summary.md"
    env = os.environ.copy()
    env["GITHUB_ACTIONS"] = "true"
    env["GITHUB_STEP_SUMMARY"] = str(summary)

    proc = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            str(spec_path),
            "--runtime",
            "python",
            "--runtime",
            "go",
            "--go-binary",
            str(stoneverify_go_binary),
            "--demo-drift",
            "text",
            "--evidence",
            str(evidence_dir),
            "--junit-report",
            str(junit_report),
        ],
        capture_output=True,
        cwd=ROOT,
        env=env,
        text=True,
    )

    assert proc.returncode == stonecharts_verify.EXIT_DIFFERENCES
    assert "StoneVerify FAIL:" in proc.stdout
    assert "::error title=StoneVerify " in proc.stdout
    assert "VERIFY." in proc.stdout

    comparison = json.loads((evidence_dir / "comparison.json").read_text(encoding="utf-8"))
    assert comparison["status"] == "fail"
    finding = comparison["pairs"][0]["findings"][0]
    assert finding["code"].startswith("VERIFY.")

    root = ET.parse(junit_report).getroot()
    failure = root.find("testcase/failure")
    assert root.attrib["failures"] == "1"
    assert failure is not None
    assert finding["code"] in (failure.text or "")

    report_html = (evidence_dir / "report.html").read_text(encoding="utf-8")
    assert "StoneVerify Report: FAIL" in report_html
    assert finding["category"] in report_html

    summary_text = summary.read_text(encoding="utf-8")
    assert "Status: **FAIL**" in summary_text
    assert "Failures: 1" in summary_text


def test_stoneverify_exit_codes_are_stable(tmp_path):
    assert stonecharts_verify.EXIT_PASS == 0
    assert stonecharts_verify.EXIT_DIFFERENCES == 1
    assert stonecharts_verify.EXIT_USAGE == 2
    assert stonecharts_verify.EXIT_INVALID_SPEC == 3
    assert stonecharts_verify.EXIT_ADAPTER == 4
    assert stonecharts_verify.EXIT_RESOURCE_LIMIT == 5
    assert stonecharts_verify.EXIT_INTERNAL == 70


def test_generated_at_can_be_pinned_for_reproducible_evidence(monkeypatch):
    monkeypatch.setenv("STONEVERIFY_GENERATED_AT", "2026-08-03T00:00:00+00:00")
    assert stonecharts_verify.generated_at() == "2026-08-03T00:00:00+00:00"


def test_stoneverify_exit_code_pass(tmp_path):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    proc = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            str(spec_path),
            "--runtime",
            "python",
            "--evidence",
            str(tmp_path / "evidence"),
        ],
        capture_output=True,
        cwd=ROOT,
    )

    assert proc.returncode == stonecharts_verify.EXIT_PASS


def test_stoneverify_exit_code_differences(tmp_path, stoneverify_go_binary):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    proc = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            str(spec_path),
            "--runtime",
            "python",
            "--runtime",
            "go",
            "--go-binary",
            str(stoneverify_go_binary),
            "--demo-drift",
            "text",
            "--evidence",
            str(tmp_path / "evidence"),
        ],
        capture_output=True,
        cwd=ROOT,
    )

    assert proc.returncode == stonecharts_verify.EXIT_DIFFERENCES


def test_stoneverify_exit_code_usage_error(tmp_path):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    proc = subprocess.run(
        [sys.executable, str(VERIFY_PATH), str(spec_path), "--runtime", "python"],
        capture_output=True,
        cwd=ROOT,
    )

    assert proc.returncode == stonecharts_verify.EXIT_USAGE


def test_stoneverify_exit_code_invalid_spec(tmp_path):
    spec_path = tmp_path / "bad.json"
    spec_path.write_text('{"type": "line", "series": [{"name": "broken", "data": ["not numeric"]}]}', encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            str(spec_path),
            "--runtime",
            "python",
            "--evidence",
            str(tmp_path / "evidence"),
        ],
        capture_output=True,
        cwd=ROOT,
    )

    assert proc.returncode == stonecharts_verify.EXIT_INVALID_SPEC
    assert b"INVALID_SPEC" in proc.stderr


def test_stoneverify_exit_code_resource_limit(tmp_path):
    spec_path = tmp_path / "too-large.json"
    spec_path.write_text(
        '{"type":"line","series":[{"name":"s","data":[' + ",".join(["1"] * 10001) + "]}]}", encoding="utf-8"
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            str(spec_path),
            "--runtime",
            "python",
            "--evidence",
            str(tmp_path / "evidence"),
        ],
        capture_output=True,
        cwd=ROOT,
    )

    assert proc.returncode == stonecharts_verify.EXIT_RESOURCE_LIMIT
    assert b"RESOURCE_LIMIT" in proc.stderr
    assert b"LIMIT.POINTS_PER_SERIES" in proc.stderr


def test_stoneverify_resource_limit_leaves_existing_evidence_untouched(tmp_path, monkeypatch):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text('{"type":"line","series":[{"name":"s","data":[1]}]}', encoding="utf-8")
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    marker = evidence / "keep.txt"
    marker.write_text("original", encoding="utf-8")

    monkeypatch.setitem(stonecharts_verify.comparison_deadline.__globals__, "COMPARISON_TIMEOUT_SECONDS", -1.0)
    monkeypatch.setitem(
        stonecharts_verify.main.__globals__,
        "render_go",
        lambda spec_path, **kwargs: (b"<svg>go</svg>", {"runtime": "go"}),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "stoneverify",
            str(spec_path),
            "--runtime",
            "python",
            "--runtime",
            "go",
            "--evidence",
            str(evidence),
        ],
    )

    assert stonecharts_verify.main() == stonecharts_verify.EXIT_RESOURCE_LIMIT
    assert marker.read_text(encoding="utf-8") == "original"
    assert not list(tmp_path.glob(".evidence.tmp-*"))


def test_stoneverify_exit_code_adapter_failure_when_go_is_unavailable(tmp_path):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    env = {**os.environ, "PATH": ""}
    proc = subprocess.run(
        [sys.executable, str(VERIFY_PATH), str(spec_path), "--runtime", "go", "--evidence", str(tmp_path / "evidence")],
        capture_output=True,
        cwd=ROOT,
        env=env,
    )

    assert proc.returncode == stonecharts_verify.EXIT_ADAPTER
    assert b"ADAPTER_FAILURE" in proc.stderr


def test_pyproject_installs_stoneverify_console_script():
    pyproject = (ROOT / "libs/python/pyproject.toml").read_text(encoding="utf-8")
    assert "[project.scripts]" in pyproject
    assert 'stoneverify = "stonecharts.verify.cli:main"' in pyproject


def test_go_runtime_uses_explicit_adapter_binary(tmp_path, stoneverify_go_binary):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    proc = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            str(spec_path),
            "--runtime",
            "go",
            "--go-binary",
            str(stoneverify_go_binary),
            "--evidence",
            str(evidence_dir),
        ],
        capture_output=True,
        cwd=tmp_path,
    )

    assert proc.returncode == stonecharts_verify.EXIT_PASS, proc.stderr.decode()
    manifest = json.loads((evidence_dir / "manifest.json").read_text(encoding="utf-8"))
    go_runtime = manifest["runtimes"][0]
    assert go_runtime["runtime"] == "go"
    assert go_runtime["module"] == "stonecharts"
    assert go_runtime["stonechartsVersion"] == "0.0.0.14"
    assert go_runtime["goAdapterVersion"] == "1.0.0"
    assert go_runtime["goBinary"] == str(stoneverify_go_binary)
