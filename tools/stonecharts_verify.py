#!/usr/bin/env python3
"""Generate a StoneVerify-style conformance evidence bundle for one chart spec."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import html
import json
import os
import pathlib
import platform
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
PY_LIB = ROOT / "libs" / "python"
GO_DIR = ROOT / "libs" / "go"
sys.path.insert(0, str(PY_LIB))

from stonecharts import ChartSpec, __version__ as PY_STONECHARTS_VERSION  # noqa: E402
from stonecharts.render import render_svg  # noqa: E402
from stonecharts.verify.result import SCHEMA_VERSION, capture_environment, sha256_digest  # noqa: E402


GO_HELPER = """package main

import (
    "fmt"
    "os"

    stonecharts "stonecharts"
)

func main() {
    if len(os.Args) != 2 {
        fmt.Fprintln(os.Stderr, "usage: stoneverify-go <spec.json>")
        os.Exit(2)
    }
    b, err := os.ReadFile(os.Args[1])
    if err != nil {
        panic(err)
    }
    spec, err := stonecharts.FromJSON(b)
    if err != nil {
        panic(err)
    }
    svg, err := stonecharts.RenderSVG(spec)
    if err != nil {
        panic(err)
    }
    fmt.Print(svg)
}
"""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_checksums(path: pathlib.Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        parts = raw.split(None, 1)
        if len(parts) != 2:
            raise ValueError(f"{path}:{line_no}: expected '<sha256>  <path>'")
        digest, name = parts
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"{path}:{line_no}: invalid SHA-256 digest")
        values[name.strip()] = digest
    return values


def validate_manifest_shape(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("tool") != "stonecharts_verify":
        errors.append("manifest.tool must be stonecharts_verify")
    if not isinstance(manifest.get("toolVersion"), int):
        errors.append("manifest.toolVersion must be an integer")
    if manifest.get("status") not in {"pass", "fail"}:
        errors.append("manifest.status must be pass or fail")
    if not isinstance(manifest.get("generatedAt"), str) or not manifest.get("generatedAt"):
        errors.append("manifest.generatedAt must be a non-empty string")
    if not isinstance(manifest.get("comparison"), str):
        errors.append("manifest.comparison must name comparison.json")
    if not isinstance(manifest.get("report"), str):
        errors.append("manifest.report must name report.html")

    input_info = manifest.get("input")
    if not isinstance(input_info, dict):
        errors.append("manifest.input must be an object")
    else:
        if not isinstance(input_info.get("file"), str):
            errors.append("manifest.input.file must name input-spec.json")
        if not isinstance(input_info.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", input_info.get("sha256", "")):
            errors.append("manifest.input.sha256 must be a lowercase SHA-256 digest")
        if not isinstance(input_info.get("bytes"), int) or input_info.get("bytes", -1) < 0:
            errors.append("manifest.input.bytes must be a non-negative integer")

    runtimes = manifest.get("runtimes")
    if not isinstance(runtimes, list) or not runtimes:
        errors.append("manifest.runtimes must be a non-empty array")
    else:
        seen: set[str] = set()
        for index, runtime in enumerate(runtimes):
            where = f"manifest.runtimes[{index}]"
            if not isinstance(runtime, dict):
                errors.append(f"{where} must be an object")
                continue
            name = runtime.get("runtime")
            if name not in {"python", "go"}:
                errors.append(f"{where}.runtime must be python or go")
            elif name in seen:
                errors.append(f"{where}.runtime duplicates {name}")
            else:
                seen.add(name)
            if not isinstance(runtime.get("output"), str) or not runtime.get("output", "").endswith(".svg"):
                errors.append(f"{where}.output must name an SVG artifact")
            if not isinstance(runtime.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", runtime.get("sha256", "")):
                errors.append(f"{where}.sha256 must be a lowercase SHA-256 digest")
            if not isinstance(runtime.get("bytes"), int) or runtime.get("bytes", -1) < 0:
                errors.append(f"{where}.bytes must be a non-negative integer")
            if runtime.get("demoDriftApplied") not in {"none", "text", "attribute"}:
                errors.append(f"{where}.demoDriftApplied must be none, text, or attribute")

    baseline = manifest.get("baseline")
    if baseline is not None:
        if not isinstance(baseline, dict):
            errors.append("manifest.baseline must be an object")
        elif baseline.get("status") not in {"pass", "fail", "not-checked"}:
            errors.append("manifest.baseline.status must be pass, fail, or not-checked")
    return errors


def check_evidence_bundle(evidence: pathlib.Path) -> dict[str, Any]:
    required = {
        "manifest.json",
        "input-spec.json",
        "comparison.json",
        "report.html",
        "checksums.txt",
    }
    missing = sorted(name for name in required if not (evidence / name).exists())
    manifest_path = evidence / "manifest.json"
    manifest: dict[str, Any] | None = None
    manifest_errors: list[str] = []
    runtime_outputs: list[str] = []
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            manifest_errors.append("manifest.json must contain a JSON object")
            manifest = {}
        else:
            manifest_errors.extend(validate_manifest_shape(manifest))
        runtime_outputs = [
            item["output"]
            for item in manifest.get("runtimes", [])
            if isinstance(item, dict) and isinstance(item.get("output"), str)
        ]
        missing.extend(name for name in runtime_outputs if not (evidence / name).exists())

    checksum_errors = []
    if not (evidence / "checksums.txt").exists():
        checksum_errors.append("checksums.txt is missing")
        checksum_map: dict[str, str] = {}
    else:
        checksum_map = parse_checksums(evidence / "checksums.txt")
        expected_checksum_entries = sorted((required - {"checksums.txt"}) | set(runtime_outputs))
        for name in expected_checksum_entries:
            path = evidence / name
            recorded = checksum_map.get(name)
            if recorded is None:
                checksum_errors.append(f"checksums.txt missing entry for {name}")
            elif path.exists():
                actual = sha256_file(path)
                if actual != recorded:
                    checksum_errors.append(f"checksum mismatch for {name}")

    status = "pass" if not missing and not checksum_errors and not manifest_errors else "fail"
    return {
        "status": status,
        "message": "Evidence bundle is internally consistent." if status == "pass" else "Evidence bundle validation failed.",
        "evidence": str(evidence),
        "missing": sorted(set(missing)),
        "manifestErrors": manifest_errors,
        "checksumErrors": checksum_errors,
        "checkedFiles": sorted(name for name in checksum_map if (evidence / name).exists()),
        "manifestStatus": None if manifest is None else manifest.get("status"),
    }


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def render_python(spec_data: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    svg = render_svg(ChartSpec.from_dict(spec_data)).encode("utf-8")
    metadata = {
        "runtime": "python",
        "stonechartsVersion": PY_STONECHARTS_VERSION,
        "pythonVersion": platform.python_version(),
        "implementation": platform.python_implementation(),
    }
    return svg, metadata


def render_go(spec_path: pathlib.Path) -> tuple[bytes, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as tmpdir:
        helper = pathlib.Path(tmpdir) / "stoneverify_go.go"
        helper.write_text(GO_HELPER, encoding="utf-8")
        proc = subprocess.run(
            ["go", "run", str(helper), str(spec_path)],
            cwd=GO_DIR,
            capture_output=True,
        )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr.decode("utf-8", errors="replace"))
        raise SystemExit(proc.returncode)
    version = subprocess.run(["go", "version"], cwd=GO_DIR, capture_output=True, text=True)
    metadata = {
        "runtime": "go",
        "stonechartsVersion": "0.0.0.4",
        "goVersion": version.stdout.strip() if version.returncode == 0 else "unknown",
        "module": "stonecharts",
    }
    return proc.stdout, metadata


def tag_counts(svg: bytes) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in re.finditer(rb"<\s*/?\s*([a-zA-Z][a-zA-Z0-9:-]*)", svg):
        tag = match.group(1).decode("ascii", errors="ignore").lower()
        counts[tag] = counts.get(tag, 0) + 1
    return dict(sorted(counts.items()))


def first_difference(left: bytes, right: bytes) -> dict[str, Any] | None:
    limit = min(len(left), len(right))
    for index in range(limit):
        if left[index] != right[index]:
            return {
                "byteOffset": index,
                "leftByte": left[index],
                "rightByte": right[index],
                "leftContext": left[max(0, index - 40) : index + 40].decode("utf-8", errors="replace"),
                "rightContext": right[max(0, index - 40) : index + 40].decode("utf-8", errors="replace"),
            }
    if len(left) != len(right):
        return {
            "byteOffset": limit,
            "leftByte": None if len(left) == limit else left[limit],
            "rightByte": None if len(right) == limit else right[limit],
            "leftContext": left[max(0, limit - 40) : limit + 40].decode("utf-8", errors="replace"),
            "rightContext": right[max(0, limit - 40) : limit + 40].decode("utf-8", errors="replace"),
        }
    return None


def classify_difference(
    left: bytes,
    right: bytes,
    left_label: str,
    right_label: str,
    diff_limit: int = 80,
) -> dict[str, Any]:
    """Describe how two SVG payloads differ using one shared diagnostic vocabulary.

    Both the cross-runtime comparison and the bundle-to-bundle comparison call this
    so a reviewer reads the same wording no matter which command produced the report.
    """
    equal = left == right
    left_tags = tag_counts(left)
    right_tags = tag_counts(right)
    structural_equal = left_tags == right_tags
    line_diff: list[str] = []
    if equal:
        likely_cause = "none"
    elif not structural_equal:
        likely_cause = "structural renderer drift: SVG element inventory differs"
    elif left.strip() == right.strip():
        likely_cause = "serialization drift: surrounding whitespace differs"
    else:
        likely_cause = "attribute, numeric formatting, ordering, or text-content drift"
        line_diff = list(
            difflib.unified_diff(
                left.decode("utf-8", errors="replace").splitlines(),
                right.decode("utf-8", errors="replace").splitlines(),
                fromfile=left_label,
                tofile=right_label,
                lineterm="",
                n=2,
            )
        )[:diff_limit]
    return {
        "equal": equal,
        "leftBytes": len(left),
        "rightBytes": len(right),
        "structural": {
            "equalTagInventory": structural_equal,
            "leftTagCounts": left_tags,
            "rightTagCounts": right_tags,
        },
        "firstDifference": None if equal else first_difference(left, right),
        "lineDiff": line_diff,
        "likelyCause": likely_cause,
    }


def compare_outputs(outputs: dict[str, bytes]) -> dict[str, Any]:
    names = sorted(outputs)
    if len(names) < 2:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "pass",
            "equal": True,
            "message": "Only one runtime was requested; no cross-runtime comparison was performed.",
            "pairs": [],
        }

    pairs = []
    overall_equal = True
    for left_name, right_name in zip(names, names[1:]):
        left = outputs[left_name]
        right = outputs[right_name]
        difference = classify_difference(
            left,
            right,
            f"{left_name}-output.svg",
            f"{right_name}-output.svg",
        )
        equal = difference["equal"]
        overall_equal = overall_equal and equal
        pairs.append(
            {
                "left": left_name,
                "right": right_name,
                "leftSha256": sha256_bytes(left),
                "rightSha256": sha256_bytes(right),
                "visual": {
                    "status": "not-computed" if not equal else "equivalent-by-byte-identity",
                    "reason": "First StoneVerify proof compares canonical SVG bytes and structure; raster visual diff is deferred.",
                },
                **difference,
            }
        )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "pass" if overall_equal else "fail",
        "equal": overall_equal,
        "message": "All requested runtime outputs are byte-identical." if overall_equal else "Runtime outputs differ.",
        "pairs": pairs,
    }


def load_baseline(baseline_dir: pathlib.Path) -> dict[str, Any]:
    manifest_path = baseline_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"baseline evidence is missing manifest.json: {baseline_dir}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("baseline manifest must be a JSON object")
    return manifest


def compare_baseline(
    current_manifest: dict[str, Any],
    current_outputs: dict[str, bytes],
    baseline_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    if baseline_manifest is None:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "not-checked",
            "message": "No baseline evidence directory was provided.",
            "inputEqual": None,
            "runtimes": [],
        }

    baseline_runtimes = {
        item.get("runtime"): item
        for item in baseline_manifest.get("runtimes", [])
        if isinstance(item, dict) and isinstance(item.get("runtime"), str)
    }
    runtime_results = []
    all_equal = True
    for runtime in sorted(current_outputs):
        current = next(item for item in current_manifest["runtimes"] if item["runtime"] == runtime)
        baseline = baseline_runtimes.get(runtime)
        if baseline is None:
            equal = False
            reason = "runtime missing from baseline evidence"
            baseline_sha = None
        else:
            baseline_sha = baseline.get("sha256")
            equal = current["sha256"] == baseline_sha
            reason = "hash match" if equal else "output hash changed from baseline"
        all_equal = all_equal and equal
        runtime_results.append(
            {
                "runtime": runtime,
                "equal": equal,
                "currentSha256": current["sha256"],
                "baselineSha256": baseline_sha,
                "reason": reason,
            }
        )

    current_input_sha = current_manifest["input"]["sha256"]
    baseline_input_sha = (baseline_manifest.get("input") or {}).get("sha256")
    input_equal = current_input_sha == baseline_input_sha
    all_equal = all_equal and input_equal

    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "pass" if all_equal else "fail",
        "message": "Current evidence matches baseline." if all_equal else "Current evidence differs from baseline.",
        "inputEqual": input_equal,
        "currentInputSha256": current_input_sha,
        "baselineInputSha256": baseline_input_sha,
        "runtimes": runtime_results,
    }


def compare_evidence_bundles(left_evidence: pathlib.Path, right_evidence: pathlib.Path) -> dict[str, Any]:
    left = check_evidence_bundle(left_evidence)
    right = check_evidence_bundle(right_evidence)

    def load_manifest(evidence: pathlib.Path) -> dict[str, Any]:
        return json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))

    left_manifest = load_manifest(left_evidence)
    right_manifest = load_manifest(right_evidence)

    left_outputs = {item["runtime"]: (left_evidence / item["output"]).read_bytes() for item in left_manifest.get("runtimes", [])}
    right_outputs = {item["runtime"]: (right_evidence / item["output"]).read_bytes() for item in right_manifest.get("runtimes", [])}

    # A runtime present on only one side is a real mismatch, not something to skip:
    # comparing the intersection alone would let bundles covering different runtimes
    # report a clean match.
    only_left = sorted(set(left_outputs) - set(right_outputs))
    only_right = sorted(set(right_outputs) - set(left_outputs))
    shared = sorted(set(left_outputs) & set(right_outputs))

    all_equal = left["status"] == "pass" and right["status"] == "pass"
    all_equal = all_equal and not only_left and not only_right

    # Distinguish "the chart spec changed" from "the same spec rendered differently".
    # Only the second is renderer drift, and that is the distinction an auditor needs.
    left_input_sha = (left_manifest.get("input") or {}).get("sha256")
    right_input_sha = (right_manifest.get("input") or {}).get("sha256")
    input_equal = left_input_sha == right_input_sha
    all_equal = all_equal and input_equal

    runtime_results = []
    for runtime in shared:
        left_bytes = left_outputs[runtime]
        right_bytes = right_outputs[runtime]
        difference = classify_difference(
            left_bytes,
            right_bytes,
            f"left/{runtime}-output.svg",
            f"right/{runtime}-output.svg",
        )
        equal = difference["equal"]
        all_equal = all_equal and equal
        if equal:
            reason = "hash match"
        elif input_equal:
            reason = "same input spec rendered differently: " + difference["likelyCause"]
        else:
            reason = "input spec differs between bundles; output difference is expected"
        runtime_results.append(
            {
                "runtime": runtime,
                "leftSha256": sha256_bytes(left_bytes),
                "rightSha256": sha256_bytes(right_bytes),
                "reason": reason,
                **difference,
            }
        )
    for runtime in only_left:
        runtime_results.append(
            {
                "runtime": runtime,
                "equal": False,
                "leftSha256": sha256_bytes(left_outputs[runtime]),
                "rightSha256": None,
                "reason": "runtime present in left bundle only",
                "likelyCause": "runtime coverage differs between bundles",
                "lineDiff": [],
                "firstDifference": None,
            }
        )
    for runtime in only_right:
        runtime_results.append(
            {
                "runtime": runtime,
                "equal": False,
                "leftSha256": None,
                "rightSha256": sha256_bytes(right_outputs[runtime]),
                "reason": "runtime present in right bundle only",
                "likelyCause": "runtime coverage differs between bundles",
                "lineDiff": [],
                "firstDifference": None,
            }
        )

    if all_equal:
        message = "Evidence bundles match."
    elif only_left or only_right:
        message = "Evidence bundles differ: runtime coverage is not the same."
    elif not input_equal:
        message = "Evidence bundles differ: they were produced from different input specs."
    else:
        message = "Evidence bundles differ: the same input spec produced different output."

    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "pass" if all_equal else "fail",
        "message": message,
        "left": {
            "evidence": str(left_evidence),
            "status": left["status"],
            "manifestStatus": left["manifestStatus"],
        },
        "right": {
            "evidence": str(right_evidence),
            "status": right["status"],
            "manifestStatus": right["manifestStatus"],
        },
        "input": {
            "equal": input_equal,
            "leftSha256": left_input_sha,
            "rightSha256": right_input_sha,
        },
        "runtimeCoverage": {
            "shared": shared,
            "onlyLeft": only_left,
            "onlyRight": only_right,
        },
        "runtimes": runtime_results,
    }


def apply_demo_drift(svg: bytes, mode: str) -> bytes:
    """Apply an explicit demo-only mutation to prove failing evidence behavior."""
    if mode == "none":
        return svg
    if mode == "text":
        return svg.replace(b"</svg>", b"<text x=\"8\" y=\"16\">demo drift</text></svg>", 1)
    if mode == "attribute":
        return svg.replace(b'role="img"', b'role="figure"', 1)
    raise ValueError(f"unsupported demo drift mode: {mode}")


def write_report(path: pathlib.Path, manifest: dict[str, Any], comparison: dict[str, Any]) -> None:
    status = comparison["status"].upper()
    rows = []
    for runtime in manifest["runtimes"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(runtime['runtime'])}</td>"
            f"<td><code>{html.escape(runtime['output'])}</code></td>"
            f"<td><code>{html.escape(runtime['sha256'])}</code></td>"
            f"<td>{runtime['bytes']}</td>"
            "</tr>"
        )
    diff_blocks = []
    for pair in comparison["pairs"]:
        diff = "\n".join(pair.get("lineDiff", [])) or pair["likelyCause"]
        diff_blocks.append(
            f"<h2>{html.escape(pair['left'])} vs {html.escape(pair['right'])}</h2>"
            f"<p>Status: <strong>{'PASS' if pair['equal'] else 'FAIL'}</strong></p>"
            f"<p>Likely cause: {html.escape(pair['likelyCause'])}</p>"
            f"<pre>{html.escape(diff)}</pre>"
        )
    baseline = manifest.get("baseline", {})
    baseline_rows = []
    for runtime in baseline.get("runtimes", []):
        baseline_rows.append(
            "<tr>"
            f"<td>{html.escape(runtime['runtime'])}</td>"
            f"<td>{'PASS' if runtime['equal'] else 'FAIL'}</td>"
            f"<td><code>{html.escape(str(runtime.get('baselineSha256')))}</code></td>"
            f"<td><code>{html.escape(runtime['currentSha256'])}</code></td>"
            f"<td>{html.escape(runtime['reason'])}</td>"
            "</tr>"
        )
    baseline_block = ""
    if baseline.get("status") != "not-checked":
        baseline_block = (
            "<h2>Baseline</h2>"
            f"<p>Status: <strong>{html.escape(str(baseline.get('status', 'unknown')).upper())}</strong></p>"
            f"<p>{html.escape(str(baseline.get('message', '')))}</p>"
            f"<p>Input match: <strong>{'PASS' if baseline.get('inputEqual') else 'FAIL'}</strong></p>"
            "<table><thead><tr><th>Runtime</th><th>Status</th><th>Baseline SHA-256</th>"
            "<th>Current SHA-256</th><th>Reason</th></tr></thead>"
            f"<tbody>{''.join(baseline_rows)}</tbody></table>"
        )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>StoneVerify Report</title>
  <style>
    body {{ font: 14px/1.45 Segoe UI, Arial, sans-serif; margin: 32px; color: #202124; }}
    code, pre {{ font-family: Consolas, monospace; }}
    pre {{ background: #f6f8fa; padding: 12px; overflow: auto; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; }}
  </style>
</head>
<body>
  <h1>StoneVerify Report: {status}</h1>
  <p>{html.escape(comparison['message'])}</p>
  <p>Demo drift: <code>{html.escape(manifest.get('demoDrift', 'none'))}</code></p>
  <p>Spec hash: <code>{html.escape(manifest['input']['sha256'])}</code></p>
  <table>
    <thead><tr><th>Runtime</th><th>Output</th><th>SHA-256</th><th>Bytes</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  {baseline_block}
  {''.join(diff_blocks)}
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")


REPORT_STYLE = """
    body { font: 14px/1.45 Segoe UI, Arial, sans-serif; margin: 32px; color: #202124; }
    code, pre { font-family: Consolas, monospace; }
    pre { background: #f6f8fa; padding: 12px; overflow: auto; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #d0d7de; padding: 8px; text-align: left; }
"""


def write_compare_report(path: pathlib.Path, comparison: dict[str, Any]) -> None:
    """Render the bundle-to-bundle comparison as a standalone reviewable report."""
    status = comparison["status"].upper()
    rows = []
    for runtime in comparison["runtimes"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(runtime['runtime'])}</td>"
            f"<td>{'PASS' if runtime['equal'] else 'FAIL'}</td>"
            f"<td><code>{html.escape(str(runtime.get('leftSha256')))}</code></td>"
            f"<td><code>{html.escape(str(runtime.get('rightSha256')))}</code></td>"
            f"<td>{html.escape(str(runtime.get('reason', '')))}</td>"
            "</tr>"
        )

    detail_blocks = []
    for runtime in comparison["runtimes"]:
        if runtime["equal"]:
            continue
        structural = runtime.get("structural") or {}
        detail = ""
        if structural:
            detail += (
                "<p>Element inventory match: "
                f"<strong>{'YES' if structural.get('equalTagInventory') else 'NO'}</strong></p>"
            )
        first = runtime.get("firstDifference")
        if first:
            detail += f"<p>First difference at byte offset <code>{first['byteOffset']}</code>.</p>"
            detail += (
                "<pre>left : "
                f"{html.escape(str(first.get('leftContext', '')))}\n"
                "right: "
                f"{html.escape(str(first.get('rightContext', '')))}</pre>"
            )
        line_diff = "\n".join(runtime.get("lineDiff") or [])
        if line_diff:
            detail += f"<pre>{html.escape(line_diff)}</pre>"
        detail_blocks.append(
            f"<h2>{html.escape(runtime['runtime'])}</h2>"
            f"<p>Likely cause: {html.escape(str(runtime.get('likelyCause', '')))}</p>"
            f"{detail}"
        )

    input_info = comparison.get("input") or {}
    coverage = comparison.get("runtimeCoverage") or {}
    coverage_note = ""
    if coverage.get("onlyLeft") or coverage.get("onlyRight"):
        coverage_note = (
            "<p>Runtime coverage differs. Left only: "
            f"<code>{html.escape(', '.join(coverage.get('onlyLeft') or []) or 'none')}</code>. "
            "Right only: "
            f"<code>{html.escape(', '.join(coverage.get('onlyRight') or []) or 'none')}</code>.</p>"
        )

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>StoneVerify Compare Report</title>
  <style>{REPORT_STYLE}</style>
</head>
<body>
  <h1>StoneVerify Compare: {status}</h1>
  <p>{html.escape(comparison['message'])}</p>
  <p>Left bundle: <code>{html.escape(comparison['left']['evidence'])}</code></p>
  <p>Right bundle: <code>{html.escape(comparison['right']['evidence'])}</code></p>
  <p>Input spec match: <strong>{'PASS' if input_info.get('equal') else 'FAIL'}</strong></p>
  {coverage_note}
  <table>
    <thead><tr><th>Runtime</th><th>Status</th><th>Left SHA-256</th>
    <th>Right SHA-256</th><th>Reason</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  {''.join(detail_blocks)}
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=pathlib.Path, nargs="?", help="Chart specification JSON")
    parser.add_argument(
        "--runtime",
        action="append",
        choices=["python", "go"],
        default=None,
        help="Runtime to verify; repeat for multiple runtimes. Defaults to python and go.",
    )
    parser.add_argument("--evidence", type=pathlib.Path, help="Evidence output directory")
    parser.add_argument(
        "--demo-drift",
        choices=["none", "text", "attribute"],
        default="none",
        help="Apply an explicit demo-only mutation to the last runtime output to prove failing evidence behavior.",
    )
    parser.add_argument(
        "--baseline-evidence",
        type=pathlib.Path,
        help="Existing StoneVerify evidence directory to compare against as an approved baseline.",
    )
    parser.add_argument(
        "--check-evidence",
        type=pathlib.Path,
        help="Validate an existing StoneVerify evidence bundle and exit without rendering.",
    )
    parser.add_argument(
        "--compare-evidence",
        nargs=2,
        metavar=("LEFT", "RIGHT"),
        type=pathlib.Path,
        help="Compare two existing StoneVerify evidence bundles without rendering.",
    )
    parser.add_argument(
        "--compare-report",
        type=pathlib.Path,
        help="Write the --compare-evidence result to an HTML report at this path.",
    )
    args = parser.parse_args()

    if args.compare_report and not args.compare_evidence:
        parser.error("--compare-report requires --compare-evidence")

    if args.check_evidence:
        result = check_evidence_bundle(args.check_evidence.resolve())
        print(f"StoneVerify evidence {result['status'].upper()}: {result['message']}")
        print(f"evidence: {result['evidence']}")
        if result["missing"]:
            print("missing: " + ", ".join(result["missing"]))
        if result["manifestErrors"]:
            print("manifest errors: " + "; ".join(result["manifestErrors"]))
        if result["checksumErrors"]:
            print("checksum errors: " + "; ".join(result["checksumErrors"]))
        return 0 if result["status"] == "pass" else 1

    if args.compare_evidence:
        left_path, right_path = (path.resolve() for path in args.compare_evidence)
        result = compare_evidence_bundles(left_path, right_path)
        print(f"StoneVerify compare {result['status'].upper()}: {result['message']}")
        print(f"left: {result['left']['evidence']}")
        print(f"right: {result['right']['evidence']}")
        print(f"input spec: {'match' if result['input']['equal'] else 'differs'}")
        for runtime in result["runtimes"]:
            state = "PASS" if runtime["equal"] else "FAIL"
            print(f"  {runtime['runtime']}: {state} - {runtime['reason']}")
        if args.compare_report:
            report_path = args.compare_report.resolve()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            write_compare_report(report_path, result)
            print(f"report: {report_path}")
        return 0 if result["status"] == "pass" else 1

    if args.spec is None:
        parser.error("spec is required unless --check-evidence or --compare-evidence is used")
    if args.evidence is None:
        parser.error("--evidence is required unless --check-evidence or --compare-evidence is used")

    spec_path = args.spec.resolve()
    evidence = args.evidence.resolve()
    runtimes = args.runtime or ["python", "go"]
    spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
    spec_bytes = canonical_json_bytes(spec_data)

    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "input-spec.json").write_bytes(spec_bytes)

    outputs: dict[str, bytes] = {}
    runtime_metadata = []
    for index, runtime in enumerate(runtimes):
        if runtime == "python":
            svg, metadata = render_python(spec_data)
        else:
            svg, metadata = render_go(spec_path)
        drift_applied = args.demo_drift if args.demo_drift != "none" and index == len(runtimes) - 1 else "none"
        svg = apply_demo_drift(svg, drift_applied)
        output_name = f"{runtime}-output.svg"
        (evidence / output_name).write_bytes(svg)
        metadata.update(
            {
                "output": output_name,
                "sha256": sha256_bytes(svg),
                "bytes": len(svg),
                "demoDriftApplied": drift_applied,
            }
        )
        outputs[runtime] = svg
        runtime_metadata.append(metadata)

    go_version = next(
        (item.get("goVersion") for item in runtime_metadata if item.get("runtime") == "go"),
        None,
    )
    comparison = compare_outputs(outputs)
    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "tool": "stonecharts_verify",
        "toolVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": comparison["status"],
        "demoDrift": args.demo_drift,
        "input": {
            "source": str(spec_path),
            "file": "input-spec.json",
            "sha256": sha256_bytes(spec_bytes),
            "bytes": len(spec_bytes),
        },
        "runtimes": runtime_metadata,
        "comparison": "comparison.json",
        "report": "report.html",
        "environment": capture_environment(
            stonecharts_version=PY_STONECHARTS_VERSION,
            stoneverify_version="1.0.0",
            go_version=go_version,
        ),
    }
    baseline_manifest = load_baseline(args.baseline_evidence.resolve()) if args.baseline_evidence else None
    baseline = compare_baseline(manifest, outputs, baseline_manifest)
    if baseline["status"] == "fail":
        comparison = {
            **comparison,
            "status": "fail",
            "message": comparison["message"] + " Baseline comparison failed.",
        }
    manifest["status"] = comparison["status"]
    manifest["baseline"] = baseline

    (evidence / "comparison.json").write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(evidence / "report.html", manifest, comparison)

    manifest["evidence"] = {
        "inputSpec": sha256_digest(manifest["input"]["sha256"]),
        "artifacts": {
            runtime["output"]: sha256_digest(runtime["sha256"]) for runtime in runtime_metadata
        },
    }
    (evidence / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checksum_paths = ["manifest.json", "input-spec.json", "comparison.json", "report.html"]
    checksum_paths.extend(runtime["output"] for runtime in runtime_metadata)
    checksums = [f"{sha256_file(evidence / name)}  {name}" for name in sorted(checksum_paths)]
    (evidence / "checksums.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")

    print(f"StoneVerify {comparison['status'].upper()}: {comparison['message']}")
    print(f"evidence: {evidence}")
    return 0 if comparison["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
