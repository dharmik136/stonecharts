"""Comprehensive unit tests targeting 90%+ code coverage for stonecharts.verify.cli."""

from __future__ import annotations

import json
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest
import stonecharts.verify.cli as cli
from stonecharts.limits import ResourceLimitError
from stonecharts.validate import SpecError


def test_timeout_env_parsing(monkeypatch):
    assert cli._timeout_env("NON_EXISTENT_TIMEOUT_VAR", 5.0) == 5.0

    monkeypatch.setenv("TEST_TIMEOUT_VAR", "12.5")
    assert cli._timeout_env("TEST_TIMEOUT_VAR", 5.0) == 12.5

    monkeypatch.setenv("TEST_TIMEOUT_VAR", "-3.0")
    assert cli._timeout_env("TEST_TIMEOUT_VAR", 5.0) == 5.0

    monkeypatch.setenv("TEST_TIMEOUT_VAR", "not-a-number")
    assert cli._timeout_env("TEST_TIMEOUT_VAR", 5.0) == 5.0


def test_commit_evidence_bundle(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "file1.txt").write_text("hello", encoding="utf-8")
    sub_staging = staging / "subdir"
    sub_staging.mkdir()
    (sub_staging / "subfile.txt").write_text("subcontent", encoding="utf-8")

    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "old.txt").write_text("old", encoding="utf-8")
    old_dir = evidence / "olddir"
    old_dir.mkdir()
    (old_dir / "oldsub.txt").write_text("oldsub", encoding="utf-8")

    cli.commit_evidence_bundle(staging, evidence)

    assert not (evidence / "old.txt").exists()
    assert not (evidence / "olddir").exists()
    assert (evidence / "file1.txt").read_text(encoding="utf-8") == "hello"
    assert (evidence / "subdir" / "subfile.txt").read_text(encoding="utf-8") == "subcontent"


def test_parse_checksums_errors(tmp_path):
    checksum_file = tmp_path / "checksums.txt"

    valid_hash = "a" * 64
    checksum_file.write_text(f"\n{valid_hash}  test.txt\n\n", encoding="utf-8")
    result = cli.parse_checksums(checksum_file)
    assert result == {"test.txt": valid_hash}

    checksum_file.write_text("badline_without_space\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected '<sha256>  <path>'"):
        cli.parse_checksums(checksum_file)

    checksum_file.write_text("not-a-valid-sha256  test.txt\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid SHA-256 digest"):
        cli.parse_checksums(checksum_file)


def test_validate_manifest_shape_branches():
    errors = cli.validate_manifest_shape({})
    assert any("manifest.tool" in e for e in errors)
    assert any("manifest.status" in e for e in errors)

    manifest = {
        "schemaVersion": cli.SCHEMA_VERSION,
        "tool": "stonecharts_verify",
        "toolVersion": 1,
        "status": "pass",
        "generatedAt": "2026-10-14T00:00:00Z",
        "comparison": "comparison.json",
        "report": "report.html",
        "input": {"file": "input-spec.json", "sha256": "0" * 64, "bytes": 100},
        "runtimes": [
            "not-a-dict",
            {"runtime": "ruby"},
        ],
        "baseline": "not-a-dict",
        "assurance": "not-a-dict",
        "presentationAdvisories": "not-a-list",
    }
    errors = cli.validate_manifest_shape(manifest)
    assert any("manifest.runtimes[0] must be an object" in e for e in errors)
    assert any("must be python or go" in e for e in errors)
    assert any("manifest.baseline must be an object" in e for e in errors)
    assert any("manifest.assurance must be an object" in e for e in errors)
    assert any("manifest.presentationAdvisories must be an array" in e for e in errors)

    manifest["assurance"] = {
        "profile": "certified",
        "chartType": "line",
        "tier": "candidate",
        "eligibleForCertifiedGuarantee": False,
    }
    manifest["presentationAdvisories"] = [
        "not-a-dict",
        {"code": "", "severity": "invalid", "message": "", "recommendation": ""},
    ]
    errors = cli.validate_manifest_shape(manifest)
    assert any("certified profile requires certified tier" in e for e in errors)
    assert any("certified profile requires eligibleForCertifiedGuarantee" in e for e in errors)
    assert any("presentationAdvisories[0] must be an object" in e for e in errors)
    assert any("severity must be info or warning" in e for e in errors)


def test_check_evidence_bundle_edge_cases(tmp_path):
    evidence = tmp_path / "evidence_invalid"
    evidence.mkdir()

    result = cli.check_evidence_bundle(evidence)
    assert result["status"] == "fail"
    assert "checksums.txt is missing" in result["checksumErrors"]

    (evidence / "manifest.json").write_text('"a string, not an object"', encoding="utf-8")
    (evidence / "checksums.txt").write_text("", encoding="utf-8")
    result = cli.check_evidence_bundle(evidence)
    assert result["status"] == "fail"
    assert "manifest.json must contain a JSON object" in result["manifestErrors"]


def test_go_adapter_version_and_go_version():
    output = "stonecharts=0.0.0.34 adapter=1.0.0 module=stonecharts/cmd"
    meta = cli._parse_go_adapter_version(output)
    assert meta["stonechartsVersion"] == "0.0.0.34"
    assert meta["goAdapterVersion"] == "1.0.0"
    assert meta["module"] == "stonecharts/cmd"

    with patch("subprocess.run", side_effect=OSError("go not found")):
        assert cli._go_version() == "unknown"


def test_resolve_go_binary(monkeypatch, tmp_path):
    bin_path = tmp_path / "my-go-bin"
    bin_path.touch()
    assert cli.resolve_go_binary(bin_path) == bin_path

    monkeypatch.setenv(cli.GO_BINARY_ENV, str(bin_path))
    assert cli.resolve_go_binary(None) == bin_path

    monkeypatch.delenv(cli.GO_BINARY_ENV, raising=False)
    with patch("shutil.which", return_value=str(bin_path)):
        assert cli.resolve_go_binary(None) == bin_path

    with (
        patch("shutil.which", return_value=None),
        pytest.raises(RuntimeError, match="stoneverify-go-render was not found"),
    ):
        cli.resolve_go_binary(None)


def test_render_go_exceptions(tmp_path):
    fake_bin = tmp_path / "fake-go-render"
    fake_bin.touch()
    spec_path = tmp_path / "spec.json"
    spec_path.write_text("{}", encoding="utf-8")

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="fake", timeout=10.0)):
        with pytest.raises(ResourceLimitError) as exc_info:
            cli.render_go(spec_path, go_binary=fake_bin)
        assert exc_info.value.code == "LIMIT.RENDER_TIMEOUT"

    with (
        patch("subprocess.run", side_effect=OSError("permission denied")),
        pytest.raises(RuntimeError, match="Go renderer adapter could not be executed"),
    ):
        cli.render_go(spec_path, go_binary=fake_bin)

    proc_mock = MagicMock(returncode=1, stderr=b"bad syntax in spec")
    with (
        patch("subprocess.run", return_value=proc_mock),
        pytest.raises(RuntimeError, match="failed with exit code 1: bad syntax in spec"),
    ):
        cli.render_go(spec_path, go_binary=fake_bin)


def test_cli_main_argument_errors(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["stoneverify", "--compare-report", "out.html"])
    with pytest.raises(SystemExit):
        cli.main()

    monkeypatch.setattr(sys, "argv", ["stoneverify", "--supersedes-baseline", "1.0", "spec.json"])
    with pytest.raises(SystemExit):
        cli.main()

    monkeypatch.setattr(sys, "argv", ["stoneverify"])
    with pytest.raises(SystemExit):
        cli.main()


def test_cli_main_check_evidence(tmp_path, monkeypatch, capsys):
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(
        json.dumps(
            {
                "type": "line",
                "title": "T",
                "xAxis": {"categories": ["A", "B"]},
                "series": [{"name": "S", "data": [1, 2]}],
            }
        ),
        encoding="utf-8",
    )
    evidence_dir = tmp_path / "valid_evidence"

    monkeypatch.setattr(
        sys, "argv", ["stoneverify", str(spec_file), "--evidence", str(evidence_dir), "--runtime", "python"]
    )
    assert cli.main() == 0

    monkeypatch.setattr(sys, "argv", ["stoneverify", "--check-evidence", str(evidence_dir)])
    exit_code = cli.main()
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "StoneVerify evidence PASS" in captured.out

    monkeypatch.setattr(sys, "argv", ["stoneverify", "--check-evidence", str(evidence_dir), "--output-format", "json"])
    exit_code = cli.main()
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "pass"
    assert data["exitCode"] == 0

    junit_out = tmp_path / "check-junit.xml"
    monkeypatch.setattr(
        sys, "argv", ["stoneverify", "--check-evidence", str(evidence_dir), "--junit-report", str(junit_out)]
    )
    exit_code = cli.main()
    assert exit_code == 0
    assert junit_out.exists()


def test_cli_main_compare_evidence(tmp_path, monkeypatch, capsys):
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(
        json.dumps(
            {
                "type": "line",
                "title": "T",
                "xAxis": {"categories": ["A", "B"]},
                "series": [{"name": "S", "data": [1, 2]}],
            }
        ),
        encoding="utf-8",
    )
    ev1 = tmp_path / "ev1"
    ev2 = tmp_path / "ev2"
    monkeypatch.setattr(sys, "argv", ["stoneverify", str(spec_file), "--evidence", str(ev1), "--runtime", "python"])
    assert cli.main() == 0

    monkeypatch.setattr(sys, "argv", ["stoneverify", str(spec_file), "--evidence", str(ev2), "--runtime", "python"])
    assert cli.main() == 0

    monkeypatch.setattr(sys, "argv", ["stoneverify", "--compare-evidence", str(ev1), str(ev2)])
    exit_code = cli.main()
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "StoneVerify compare PASS" in captured.out

    monkeypatch.setattr(
        sys, "argv", ["stoneverify", "--compare-evidence", str(ev1), str(ev2), "--output-format", "json"]
    )
    exit_code = cli.main()
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "pass"

    cmp_html = tmp_path / "cmp_report.html"
    cmp_junit = tmp_path / "cmp_junit.xml"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "stoneverify",
            "--compare-evidence",
            str(ev1),
            str(ev2),
            "--compare-report",
            str(cmp_html),
            "--junit-report",
            str(cmp_junit),
        ],
    )
    exit_code = cli.main()
    assert exit_code == 0
    assert cmp_html.exists()
    assert cmp_junit.exists()


def test_cli_main_errors_and_limits(tmp_path, monkeypatch):
    ev = tmp_path / "ev"

    # Spec file not found
    monkeypatch.setattr(sys, "argv", ["stoneverify", str(tmp_path / "missing.json"), "--evidence", str(ev)])
    assert cli.main() == cli.EXIT_INVALID_SPEC

    # Invalid JSON in spec
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["stoneverify", str(bad_json), "--evidence", str(ev)])
    assert cli.main() == cli.EXIT_INVALID_SPEC

    # Spec fails schema validation
    invalid_spec = tmp_path / "invalid_spec.json"
    invalid_spec.write_text(json.dumps({"type": "line", "title": "Missing series"}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["stoneverify", str(invalid_spec), "--evidence", str(ev)])
    assert cli.main() == cli.EXIT_INVALID_SPEC

    # ResourceLimitError in render_python
    with patch(
        "stonecharts.verify.cli.render_python",
        side_effect=ResourceLimitError("LIMIT.SPEC_BYTES", "$", 1000, 2000),
    ):
        valid_spec = tmp_path / "valid.json"
        valid_spec.write_text(
            json.dumps({"type": "line", "title": "T", "xAxis": {"categories": ["A"]}, "series": [{"data": [1]}]}),
            encoding="utf-8",
        )
        monkeypatch.setattr(sys, "argv", ["stoneverify", str(valid_spec), "--evidence", str(ev), "--runtime", "python"])
        assert cli.main() == cli.EXIT_RESOURCE_LIMIT

    # SpecError in render_python
    with patch(
        "stonecharts.verify.cli.render_python",
        side_effect=SpecError(["invalid render"]),
    ):
        monkeypatch.setattr(sys, "argv", ["stoneverify", str(valid_spec), "--evidence", str(ev), "--runtime", "python"])
        assert cli.main() == cli.EXIT_INVALID_SPEC

    # Go renderer ResourceLimitError in main
    with patch(
        "stonecharts.verify.cli.render_go",
        side_effect=ResourceLimitError("LIMIT.RENDER_TIMEOUT", "$.render.go", 10000, 15000),
    ):
        monkeypatch.setattr(sys, "argv", ["stoneverify", str(valid_spec), "--evidence", str(ev), "--runtime", "go"])
        assert cli.main() == cli.EXIT_RESOURCE_LIMIT

    # Go renderer RuntimeError in main
    with patch(
        "stonecharts.verify.cli.render_go",
        side_effect=RuntimeError("Go adapter crashed"),
    ):
        monkeypatch.setattr(sys, "argv", ["stoneverify", str(valid_spec), "--evidence", str(ev), "--runtime", "go"])
        assert cli.main() == cli.EXIT_ADAPTER

    # Spec exceeds MAX_SPEC_BYTES
    large_spec = tmp_path / "large_spec.json"
    large_spec.write_bytes(b" " * (cli.MAX_SPEC_BYTES + 10))
    monkeypatch.setattr(sys, "argv", ["stoneverify", str(large_spec), "--evidence", str(ev)])
    assert cli.main() == cli.EXIT_RESOURCE_LIMIT

    # Assurance tier mismatch
    with patch("stonecharts.verify.cli.capabilities", return_value={"chartTypes": {"line": {"tier": "candidate"}}}):
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "stoneverify",
                str(valid_spec),
                "--evidence",
                str(ev),
                "--runtime",
                "python",
                "--profile",
                "certified",
            ],
        )
        assert cli.main() == cli.EXIT_ASSURANCE_TIER


def test_cli_main_dual_axis_and_drift(tmp_path, monkeypatch, capsys):
    dual_spec = tmp_path / "dual.json"
    dual_spec.write_text(
        json.dumps(
            {
                "type": "combo",
                "title": "Dual Axis Chart",
                "xAxis": {"categories": ["Jan", "Feb"]},
                "series": [
                    {"name": "Throughput", "type": "column", "data": [100, 200]},
                    {"name": "Latency", "type": "line", "data": [15, 25]},
                ],
                "secondaryYAxis": {"title": {"text": "Latency (ms)"}},
            }
        ),
        encoding="utf-8",
    )
    ev_dir = tmp_path / "dual_ev"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "stoneverify",
            str(dual_spec),
            "--evidence",
            str(ev_dir),
            "--runtime",
            "python",
            "--demo-drift",
            "text",
            "--profile",
            "evaluation",
            "--output-format",
            "json",
        ],
    )
    exit_code = cli.main()
    assert exit_code == 0
    manifest = json.loads((ev_dir / "manifest.json").read_text(encoding="utf-8"))
    assert "presentationAdvisories" in manifest
    assert manifest["presentationAdvisories"][0]["code"] == "ADV-DUAL-AXIS"


def test_junit_and_github_actions_output(tmp_path, monkeypatch):
    summary_file = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))

    manifest = {
        "baseline": {
            "status": "fail",
            "inputEqual": False,
            "baselineInputSha256": "1" * 64,
            "currentInputSha256": "2" * 64,
            "runtimes": [
                {
                    "runtime": "python",
                    "equal": False,
                    "reason": "mismatch",
                    "findings": [
                        cli.build_finding(
                            code="VERIFY.TEST",
                            category="rendering",
                            message="test failure",
                            equality="unknown",
                            confidence="high",
                            basis=["diff 1"],
                        )
                    ],
                }
            ],
        }
    }
    comparison = {"status": "fail", "message": "Baseline failed"}

    cases = cli.junit_testcases(manifest, comparison)
    assert len(cases) == 1
    assert cases[0]["passed"] is False

    junit_file = tmp_path / "junit.xml"
    cli.write_junit_report(junit_file, manifest, comparison)
    cli.validate_junit_report(junit_file)
    assert junit_file.exists()

    cli.emit_github_actions_output(manifest, comparison, summary_path=summary_file)
    assert summary_file.exists()
    summary_text = summary_file.read_text(encoding="utf-8")
    assert "StoneVerify" in summary_text
    assert "FAIL" in summary_text

    # Test passing emission
    passing_comparison = {
        "status": "pass",
        "message": "All passed",
        "pairs": [{"left": "python", "right": "go", "equal": True}],
    }
    cli.emit_github_actions_output(None, passing_comparison, summary_path=summary_file)


def test_render_go_from_source_live(tmp_path):
    spec_file = tmp_path / "small_spec.json"
    spec_file.write_text(
        json.dumps(
            {
                "type": "line",
                "title": "Small Line",
                "xAxis": {"categories": ["Q1", "Q2"]},
                "series": [{"name": "Rev", "data": [10.0, 20.0]}],
            }
        ),
        encoding="utf-8",
    )
    svg, metadata = cli.render_go(spec_file, from_source=True)
    assert b"<svg" in svg
    assert metadata["runtime"] == "go"
    assert metadata["goAdapterVersion"] == "source-fallback"


def test_validate_junit_report_failures(tmp_path):
    not_testsuite = tmp_path / "not_ts.xml"
    not_testsuite.write_text("<root></root>", encoding="utf-8")
    with pytest.raises(ValueError, match="JUnit report root must be testsuite"):
        cli.validate_junit_report(not_testsuite)

    mismatch_tests = tmp_path / "mismatch_tests.xml"
    mismatch_tests.write_text('<testsuite tests="5" failures="0"><testcase name="c1"/></testsuite>', encoding="utf-8")
    with pytest.raises(ValueError, match="JUnit report tests count does not match testcase elements"):
        cli.validate_junit_report(mismatch_tests)

    mismatch_failures = tmp_path / "mismatch_failures.xml"
    mismatch_failures.write_text(
        '<testsuite tests="1" failures="5"><testcase name="c1"><failure>err</failure></testcase></testsuite>',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="JUnit report failures count does not match failure elements"):
        cli.validate_junit_report(mismatch_failures)


def test_cli_main_check_evidence_errors(tmp_path, monkeypatch, capsys):
    bad_ev = tmp_path / "bad_ev"
    bad_ev.mkdir()
    # Missing checksums and bad manifest
    (bad_ev / "manifest.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["stoneverify", "--check-evidence", str(bad_ev)])
    exit_code = cli.main()
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "StoneVerify evidence FAIL" in captured.out
    assert "missing:" in captured.out


def test_cli_main_single_spec_with_junit(tmp_path, monkeypatch, capsys):
    spec_file = tmp_path / "spec_junit.json"
    spec_file.write_text(
        json.dumps(
            {
                "type": "line",
                "title": "T",
                "xAxis": {"categories": ["A"]},
                "series": [{"name": "S", "data": [1]}],
            }
        ),
        encoding="utf-8",
    )
    ev_dir = tmp_path / "spec_junit_ev"
    junit_path = tmp_path / "spec_junit_out.xml"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "stoneverify",
            str(spec_file),
            "--evidence",
            str(ev_dir),
            "--runtime",
            "python",
            "--junit-report",
            str(junit_path),
        ],
    )
    exit_code = cli.main()
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "junit:" in captured.out
    assert junit_path.exists()
