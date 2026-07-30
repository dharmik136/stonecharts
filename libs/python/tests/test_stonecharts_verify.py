"""Unit checks for the first StoneVerify proof tool."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys

from stonecharts.verify.result import SCHEMA_VERSION


ROOT = pathlib.Path(__file__).resolve().parents[3]
VERIFY_PATH = ROOT / "tools" / "stonecharts_verify.py"

spec = importlib.util.spec_from_file_location("stonecharts_verify", VERIFY_PATH)
stonecharts_verify = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stonecharts_verify)


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
    checksums = [
        f"{stonecharts_verify.sha256_file(evidence / name)}  {name}"
        for name in sorted(files)
    ]
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
    checksums = [
        f"{stonecharts_verify.sha256_file(evidence / name)}  {name}"
        for name in sorted(files)
    ]
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
    for key in ("os", "arch", "pythonVersion", "stonechartsVersion", "stoneverifyVersion", "schemaVersion", "locale", "timezone"):
        assert key in env
    # existing fields untouched
    assert manifest["tool"] == "stonecharts_verify"
    assert manifest["toolVersion"] == 1
    assert "input" in manifest and "runtimes" in manifest


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
        "tool", "toolVersion", "generatedAt", "status", "demoDrift",
        "input", "runtimes", "comparison", "report", "baseline",
    }
    new_keys = {"schemaVersion", "environment", "evidence"}
    assert set(manifest.keys()) == pre_014a_keys | new_keys


def test_comparison_json_only_adds_schema_version(tmp_path):
    spec_path = (ROOT / "charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    subprocess.run(
        [sys.executable, str(VERIFY_PATH), str(spec_path), "--runtime", "python", "--runtime", "go", "--evidence", str(evidence_dir)],
        capture_output=True,
        cwd=ROOT,
        check=True,
    )
    comparison = json.loads((evidence_dir / "comparison.json").read_text(encoding="utf-8"))
    assert set(comparison.keys()) == {"schemaVersion", "status", "equal", "message", "pairs"}
