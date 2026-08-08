#!/usr/bin/env python3
"""Generate a StoneVerify-style conformance evidence bundle for one chart spec."""

from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import hashlib
import html
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

from stonecharts import ChartSpec
from stonecharts import __version__ as PY_STONECHARTS_VERSION
from stonecharts.capabilities import CapabilityError
from stonecharts.limits import MAX_SPEC_BYTES, ResourceLimitError
from stonecharts.render import render_svg
from stonecharts.validate import SpecError
from stonecharts.verify.result import (
    SCHEMA_VERSION,
    build_finding,
    build_verification_result,
    capture_environment,
    check_schema_version,
    sha256_digest,
)

EXIT_PASS = 0
EXIT_DIFFERENCES = 1
EXIT_USAGE = 2
EXIT_INVALID_SPEC = 3
EXIT_ADAPTER = 4
EXIT_RESOURCE_LIMIT = 5
EXIT_INTERNAL = 70
STONEVERIFY_VERSION = "1.0.0"
GO_BINARY_ENV = "STONEVERIFY_GO_BINARY"
GO_BINARY_NAME = "stoneverify-go-render"
SOURCE_GO_DIR = pathlib.Path(__file__).resolve().parents[4] / "libs" / "go"
GENERATED_AT_ENV = "STONEVERIFY_GENERATED_AT"
MAX_EVIDENCE_BUNDLE_BYTES = 10_000_000
MAX_FINDINGS = 100
RENDER_TIMEOUT_ENV = "STONEVERIFY_RENDER_TIMEOUT"
COMPARISON_TIMEOUT_ENV = "STONEVERIFY_COMPARISON_TIMEOUT"


def _timeout_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        val = float(raw)
        return val if val > 0 else default
    except ValueError:
        return default


RENDER_TIMEOUT_SECONDS = _timeout_env(RENDER_TIMEOUT_ENV, 10.0)
COMPARISON_TIMEOUT_SECONDS = _timeout_env(COMPARISON_TIMEOUT_ENV, 10.0)


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


def evidence_bundle_size(evidence: pathlib.Path) -> int:
    total = 0
    if not evidence.exists():
        return total
    for path in evidence.rglob("*"):
        if path.is_file():
            total += path.stat().st_size
            if total > MAX_EVIDENCE_BUNDLE_BYTES:
                raise ResourceLimitError("LIMIT.EVIDENCE_BUNDLE_BYTES", str(evidence), MAX_EVIDENCE_BUNDLE_BYTES, total)
    return total


def comparison_deadline() -> float:
    return time.monotonic() + COMPARISON_TIMEOUT_SECONDS


def check_comparison_deadline(deadline: float) -> None:
    if time.monotonic() > deadline:
        raise ResourceLimitError(
            "LIMIT.COMPARISON_TIMEOUT",
            "$.comparison",
            int(COMPARISON_TIMEOUT_SECONDS * 1000),
            int(COMPARISON_TIMEOUT_SECONDS * 1000) + 1,
        )


def enforce_finding_limit(count: int) -> None:
    if count > MAX_FINDINGS:
        raise ResourceLimitError("LIMIT.FINDING_COUNT", "$.findings", MAX_FINDINGS, count)


def commit_evidence_bundle(staging: pathlib.Path, evidence: pathlib.Path) -> None:
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    for child in evidence.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in staging.iterdir():
        target = evidence / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)


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
    version_error = check_schema_version(manifest.get("schemaVersion"))
    if version_error:
        errors.append(f"manifest.schemaVersion: {version_error}")
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
        if not isinstance(input_info.get("sha256"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", input_info.get("sha256", "")
        ):
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
            if not isinstance(runtime.get("sha256"), str) or not re.fullmatch(
                r"[0-9a-f]{64}", runtime.get("sha256", "")
            ):
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
    bundle_size = evidence_bundle_size(evidence)
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
        "message": "Evidence bundle is internally consistent."
        if status == "pass"
        else "Evidence bundle validation failed.",
        "evidence": str(evidence),
        "missing": sorted(set(missing)),
        "manifestErrors": manifest_errors,
        "checksumErrors": checksum_errors,
        "checkedFiles": sorted(name for name in checksum_map if (evidence / name).exists()),
        "manifestStatus": None if manifest is None else manifest.get("status"),
        "bundleBytes": bundle_size,
    }


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def generated_at() -> str:
    return os.environ.get(GENERATED_AT_ENV) or datetime.now(timezone.utc).isoformat()


def _render_python_inner(spec_data: dict[str, Any], *, raw_size_hint: int | None = None) -> bytes:
    return render_svg(ChartSpec.from_dict(spec_data, raw_size_hint=raw_size_hint)).encode("utf-8")


def render_python(spec_data: dict[str, Any], *, raw_size_hint: int | None = None) -> tuple[bytes, dict[str, Any]]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_render_python_inner, spec_data, raw_size_hint=raw_size_hint)
        try:
            svg = future.result(timeout=RENDER_TIMEOUT_SECONDS)
        except concurrent.futures.TimeoutError as exc:
            raise ResourceLimitError(
                "LIMIT.RENDER_TIMEOUT",
                "$.render",
                int(RENDER_TIMEOUT_SECONDS * 1000),
                int(RENDER_TIMEOUT_SECONDS * 1000) + 1,
            ) from exc
    metadata = {
        "runtime": "python",
        "stonechartsVersion": PY_STONECHARTS_VERSION,
        "pythonVersion": platform.python_version(),
        "implementation": platform.python_implementation(),
    }
    return svg, metadata


def _parse_go_adapter_version(output: str) -> dict[str, str]:
    metadata = {
        "stonechartsVersion": "unknown",
        "goAdapterVersion": "unknown",
        "module": "unknown",
    }
    for part in output.strip().split():
        if part.startswith("stonecharts="):
            metadata["stonechartsVersion"] = part.split("=", 1)[1]
        elif part.startswith("adapter="):
            metadata["goAdapterVersion"] = part.split("=", 1)[1]
        elif part.startswith("module="):
            metadata["module"] = part.split("=", 1)[1]
    return metadata


def _go_version(cwd: pathlib.Path | None = None) -> str:
    try:
        version = subprocess.run(["go", "version"], cwd=cwd, capture_output=True, text=True)
    except OSError:
        return "unknown"
    return version.stdout.strip() if version.returncode == 0 else "unknown"


def resolve_go_binary(go_binary: pathlib.Path | None = None) -> pathlib.Path:
    if go_binary is not None:
        return go_binary
    env_path = os.environ.get(GO_BINARY_ENV)
    if env_path:
        return pathlib.Path(env_path)
    resolved = shutil.which(GO_BINARY_NAME)
    if resolved:
        return pathlib.Path(resolved)
    raise RuntimeError(
        f"{GO_BINARY_NAME} was not found; provide --go-binary, set {GO_BINARY_ENV}, "
        "or pass --from-source in a development checkout"
    )


def _render_go_from_source(spec_path: pathlib.Path) -> tuple[bytes, dict[str, Any]]:
    if not SOURCE_GO_DIR.exists():
        raise RuntimeError(f"Go source fallback is unavailable; expected {SOURCE_GO_DIR}")
    with tempfile.TemporaryDirectory() as tmpdir:
        helper = pathlib.Path(tmpdir) / "stoneverify_go.go"
        helper.write_text(GO_HELPER, encoding="utf-8")
        try:
            proc = subprocess.run(
                ["go", "run", str(helper), str(spec_path)],
                cwd=SOURCE_GO_DIR,
                capture_output=True,
                timeout=RENDER_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise ResourceLimitError(
                "LIMIT.RENDER_TIMEOUT", "$.render.go", int(RENDER_TIMEOUT_SECONDS * 1000), int(exc.timeout * 1000)
            ) from exc
        except OSError as exc:
            raise RuntimeError(f"Go renderer adapter could not be executed: {exc}") from exc
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Go renderer adapter failed with exit code {proc.returncode}: {stderr}")
    metadata = {
        "runtime": "go",
        "stonechartsVersion": PY_STONECHARTS_VERSION,
        "goVersion": _go_version(SOURCE_GO_DIR),
        "goAdapterVersion": "source-fallback",
        "module": "stonecharts",
    }
    return proc.stdout, metadata


def render_go(
    spec_path: pathlib.Path,
    *,
    go_binary: pathlib.Path | None = None,
    from_source: bool = False,
) -> tuple[bytes, dict[str, Any]]:
    if from_source:
        return _render_go_from_source(spec_path)

    binary = resolve_go_binary(go_binary)
    try:
        proc = subprocess.run([str(binary), str(spec_path)], capture_output=True, timeout=RENDER_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        raise ResourceLimitError(
            "LIMIT.RENDER_TIMEOUT", "$.render.go", int(RENDER_TIMEOUT_SECONDS * 1000), int(exc.timeout * 1000)
        ) from exc
    except OSError as exc:
        raise RuntimeError(f"Go renderer adapter could not be executed: {exc}") from exc
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Go renderer adapter failed with exit code {proc.returncode}: {stderr}")

    version_metadata = {
        "stonechartsVersion": "unknown",
        "goAdapterVersion": "unknown",
        "module": "stonecharts",
    }
    try:
        version_proc = subprocess.run([str(binary), "--version"], capture_output=True, text=True)
    except OSError:
        version_proc = None
    if version_proc is not None and version_proc.returncode == 0:
        version_metadata.update(_parse_go_adapter_version(version_proc.stdout))

    metadata = {
        "runtime": "go",
        **version_metadata,
        "goVersion": _go_version(),
        "goBinary": str(binary),
    }
    return proc.stdout, metadata


def tag_counts(svg: bytes) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in re.finditer(rb"<\s*/?\s*([a-zA-Z][a-zA-Z0-9:-]*)", svg):
        tag = match.group(1).decode("ascii", errors="ignore").lower()
        counts[tag] = counts.get(tag, 0) + 1
    return dict(sorted(counts.items()))


_GEOMETRY_ATTRS = {"d", "cx", "cy", "r", "x", "y", "x1", "y1", "x2", "y2", "points", "transform", "width", "height"}
_THEME_ATTRS = {
    "fill",
    "stroke",
    "stroke-width",
    "stroke-dasharray",
    "opacity",
    "class",
    "style",
    "font-size",
    "font-weight",
}
_ACCESSIBILITY_ATTRS = {"role", "aria-hidden", "aria-label", "aria-labelledby", "aria-describedby", "scope"}
_INPUT_DATA_ATTRS = {"data-x", "data-y", "data-z", "data-r"}
_FINDING_CODES = {
    "input-data": "VERIFY.INPUT.DATA_CHANGED",
    "geometry": "VERIFY.GEOMETRY.CHANGED",
    "scale-domain": "VERIFY.SCALE.DOMAIN_CHANGED",
    "label-text": "VERIFY.LABEL.TEXT_CHANGED",
    "theme-style": "VERIFY.THEME.STYLE_CHANGED",
    "accessibility-metadata": "VERIFY.ACCESSIBILITY.METADATA_CHANGED",
    "serialization-only": "VERIFY.SERIALIZATION.ONLY",
    "chart-type-capability": "VERIFY.CAPABILITY.CHART_TYPE_CHANGED",
    "unknown-structural": "VERIFY.STRUCTURE.UNKNOWN_CHANGED",
}


def _walk_svg(elem: ET.Element) -> list[ET.Element]:
    result = [elem]
    for child in elem:
        result.extend(_walk_svg(child))
    return result


def _classes(elem: ET.Element) -> set[str]:
    return set((elem.attrib.get("class") or "").split())


def _walk_svg_context(elem: ET.Element, inherited_classes: set[str] | None = None) -> list[tuple[ET.Element, set[str]]]:
    classes = set(inherited_classes or set()) | _classes(elem)
    result = [(elem, classes)]
    for child in elem:
        result.extend(_walk_svg_context(child, classes))
    return result


def classify_semantic(left: bytes, right: bytes) -> dict[str, Any]:
    if left == right:
        return {
            "category": "unknown-structural",
            "equality": "byte",
            "confidence": "high",
            "basis": ["byte-identical"],
        }

    try:
        left_root = ET.fromstring(left)
        right_root = ET.fromstring(right)
    except ET.ParseError:
        return {
            "category": "unknown-structural",
            "equality": "unknown",
            "confidence": "low",
            "basis": ["one or both payloads did not parse as XML"],
        }

    left_elems = _walk_svg_context(left_root)
    right_elems = _walk_svg_context(right_root)
    if len(left_elems) != len(right_elems):
        return {
            "category": "chart-type-capability",
            "equality": "unknown",
            "confidence": "low",
            "basis": [f"element count differs: {len(left_elems)} vs {len(right_elems)}"],
        }

    geometry_hits: list[str] = []
    scale_hits: list[str] = []
    data_hits: list[str] = []
    theme_hits: list[str] = []
    accessibility_hits: list[str] = []
    text_hits: list[str] = []
    other_hits: list[str] = []

    for (left_elem, left_classes), (right_elem, right_classes) in zip(left_elems, right_elems):
        classes = left_classes | right_classes
        if left_elem.tag != right_elem.tag:
            other_hits.append(f"element changed: {left_elem.tag!r} -> {right_elem.tag!r}")
            continue
        for key in sorted(set(left_elem.attrib) | set(right_elem.attrib)):
            if left_elem.attrib.get(key) == right_elem.attrib.get(key):
                continue
            basis = f"{left_elem.tag}[{key}]: {left_elem.attrib.get(key)!r} -> {right_elem.attrib.get(key)!r}"
            if key in _INPUT_DATA_ATTRS:
                data_hits.append(basis)
            elif key == "data-series-name":
                text_hits.append(basis)
            elif key in _GEOMETRY_ATTRS:
                if (
                    "sc-axis" in classes
                    or "sc-gridline" in classes
                    or "sc-axis-line" in classes
                    or "sc-point" in classes
                ):
                    scale_hits.append(basis)
                else:
                    geometry_hits.append(basis)
            elif key in _THEME_ATTRS:
                theme_hits.append(basis)
            elif key in _ACCESSIBILITY_ATTRS or key.startswith("aria-"):
                accessibility_hits.append(basis)
            else:
                other_hits.append(basis)
        left_text = (left_elem.text or "").strip()
        right_text = (right_elem.text or "").strip()
        if left_text != right_text:
            basis = f"{left_elem.tag} text: {left_text!r} -> {right_text!r}"
            if "sc-axis" in classes:
                scale_hits.append(basis)
            else:
                text_hits.append(basis)

    if data_hits:
        return {"category": "input-data", "equality": "unknown", "confidence": "high", "basis": data_hits}
    if scale_hits and not geometry_hits:
        return {"category": "scale-domain", "equality": "unknown", "confidence": "medium", "basis": scale_hits}
    if geometry_hits:
        return {"category": "geometry", "equality": "unknown", "confidence": "high", "basis": geometry_hits}
    if text_hits:
        return {"category": "label-text", "equality": "unknown", "confidence": "high", "basis": text_hits}
    if accessibility_hits:
        return {
            "category": "accessibility-metadata",
            "equality": "semantic",
            "confidence": "high",
            "basis": accessibility_hits,
        }
    if theme_hits:
        return {"category": "theme-style", "equality": "semantic", "confidence": "high", "basis": theme_hits}
    if other_hits:
        return {"category": "unknown-structural", "equality": "unknown", "confidence": "medium", "basis": other_hits}
    return {
        "category": "serialization-only",
        "equality": "structural",
        "confidence": "high",
        "basis": ["no element, attribute, or text difference found; byte difference is serialization-only"],
    }


def finding_code(category: str) -> str:
    return _FINDING_CODES.get(category, "VERIFY.STRUCTURE.UNKNOWN_CHANGED")


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
    semantic = classify_semantic(left, right)
    findings = []
    if not equal:
        findings.append(
            build_finding(
                code=finding_code(semantic["category"]),
                category=semantic["category"],
                message=likely_cause,
                equality=semantic["equality"],
                confidence=semantic["confidence"],
                basis=semantic["basis"],
            )
        )
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
        "category": semantic["category"],
        "equality": semantic["equality"],
        "confidence": semantic["confidence"],
        "basis": semantic["basis"],
        "findings": findings,
    }


def compare_outputs(outputs: dict[str, bytes]) -> dict[str, Any]:
    deadline = comparison_deadline()
    names = sorted(outputs)
    if len(names) < 2:
        result = build_verification_result(
            status="pass",
            comparison_mode="cross-runtime",
            candidate={"runtimes": names},
            runtime_coverage={"shared": names, "onlyLeft": [], "onlyRight": []},
            findings=[],
        )
        return {
            "schemaVersion": result["schemaVersion"],
            "status": result["status"],
            "equal": True,
            "message": "Only one runtime was requested; no cross-runtime comparison was performed.",
            "pairs": [],
        }

    pairs: list[dict] = []
    overall_equal = True
    for left_name, right_name in zip(names, names[1:]):
        check_comparison_deadline(deadline)
        left = outputs[left_name]
        right = outputs[right_name]
        difference = classify_difference(
            left,
            right,
            f"{left_name}-output.svg",
            f"{right_name}-output.svg",
        )
        enforce_finding_limit(sum(len(pair.get("findings", [])) for pair in pairs))  # type: ignore[arg-type]
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
    result = build_verification_result(
        status="pass" if overall_equal else "fail",
        comparison_mode="cross-runtime",
        candidate={"runtimes": names},
        runtime_coverage={"shared": names, "onlyLeft": [], "onlyRight": []},
        findings=[finding for pair in pairs for finding in pair.get("findings", [])],
    )
    return {
        "schemaVersion": result["schemaVersion"],
        "status": result["status"],
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
    version_error = check_schema_version(manifest.get("schemaVersion"))
    if version_error:
        raise ValueError(f"baseline evidence: {version_error}")
    return manifest


def baseline_identity(baseline_dir: pathlib.Path | None, manifest: dict[str, Any] | None) -> dict[str, Any] | None:
    if baseline_dir is None or manifest is None:
        return None
    manifest_path = baseline_dir / "manifest.json"
    return {
        "evidence": str(baseline_dir),
        "manifestSha256": sha256_file(manifest_path) if manifest_path.exists() else None,
        "toolVersion": manifest.get("toolVersion"),
        "generatedAt": manifest.get("generatedAt"),
    }


def compare_baseline(
    current_manifest: dict[str, Any],
    current_outputs: dict[str, bytes],
    baseline_manifest: dict[str, Any] | None,
    *,
    baseline_dir: pathlib.Path | None = None,
    supersedes_baseline_dir: pathlib.Path | None = None,
    supersedes_baseline_manifest: dict[str, Any] | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    identity = baseline_identity(baseline_dir, baseline_manifest)
    supersedes_identity = baseline_identity(supersedes_baseline_dir, supersedes_baseline_manifest)
    if baseline_manifest is None:
        result = build_verification_result(
            status="not-checked",
            comparison_mode="baseline",
            baseline=None,
            candidate={"runtimes": sorted(current_outputs)},
            findings=[],
        )
        return {
            "schemaVersion": result["schemaVersion"],
            "status": result["status"],
            "message": "No baseline evidence directory was provided.",
            "inputEqual": None,
            "identity": None,
            "supersedes": supersedes_identity,
            "note": note,
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
        findings = []
        if not equal:
            findings.append(
                build_finding(
                    code="VERIFY.BASELINE.OUTPUT_CHANGED",
                    category="baseline",
                    message=reason,
                    equality="unknown",
                    confidence="high",
                    basis=[f"{runtime}: {reason}"],
                )
            )
        runtime_results.append(
            {
                "runtime": runtime,
                "equal": equal,
                "currentSha256": current["sha256"],
                "baselineSha256": baseline_sha,
                "reason": reason,
                "findings": findings,
            }
        )
        enforce_finding_limit(sum(len(item.get("findings", [])) for item in runtime_results))

    current_input_sha = current_manifest["input"]["sha256"]
    baseline_input_sha = (baseline_manifest.get("input") or {}).get("sha256")
    input_equal = current_input_sha == baseline_input_sha
    all_equal = all_equal and input_equal
    findings = [finding for runtime in runtime_results for finding in runtime.get("findings", [])]
    if not input_equal:
        findings.append(
            build_finding(
                code="VERIFY.BASELINE.INPUT_CHANGED",
                category="input-data",
                message="input spec hash changed from baseline",
                equality="unknown",
                confidence="high",
                basis=[f"input: {baseline_input_sha!r} -> {current_input_sha!r}"],
            )
        )
    enforce_finding_limit(len(findings))

    result = build_verification_result(
        status="pass" if all_equal else "fail",
        comparison_mode="baseline",
        baseline={
            "inputSha256": baseline_input_sha,
            "identity": identity,
            "supersedes": supersedes_identity,
            "note": note,
        },
        candidate={"inputSha256": current_input_sha, "runtimes": sorted(current_outputs)},
        inputs={"equal": input_equal, "leftSha256": baseline_input_sha, "rightSha256": current_input_sha},
        runtime_coverage={"shared": sorted(current_outputs), "onlyLeft": [], "onlyRight": []},
        findings=findings,
    )
    return {
        "schemaVersion": result["schemaVersion"],
        "status": result["status"],
        "message": "Current evidence matches baseline." if all_equal else "Current evidence differs from baseline.",
        "inputEqual": input_equal,
        "currentInputSha256": current_input_sha,
        "baselineInputSha256": baseline_input_sha,
        "identity": identity,
        "supersedes": supersedes_identity,
        "note": note,
        "runtimes": runtime_results,
    }


def compare_evidence_bundles(left_evidence: pathlib.Path, right_evidence: pathlib.Path) -> dict[str, Any]:
    deadline = comparison_deadline()
    left = check_evidence_bundle(left_evidence)
    right = check_evidence_bundle(right_evidence)

    def load_manifest(evidence: pathlib.Path) -> dict[str, Any]:
        result: dict[str, Any] = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))
        return result

    left_manifest = load_manifest(left_evidence)
    right_manifest = load_manifest(right_evidence)

    left_outputs = {
        item["runtime"]: (left_evidence / item["output"]).read_bytes() for item in left_manifest.get("runtimes", [])
    }
    right_outputs = {
        item["runtime"]: (right_evidence / item["output"]).read_bytes() for item in right_manifest.get("runtimes", [])
    }

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
        check_comparison_deadline(deadline)
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
        enforce_finding_limit(sum(len(item.get("findings", [])) for item in runtime_results))
    for runtime in only_left:
        check_comparison_deadline(deadline)
        findings = [
            build_finding(
                code="VERIFY.RUNTIME.COVERAGE_CHANGED",
                category="runtime-coverage",
                message="runtime present in left bundle only",
                equality="unknown",
                confidence="high",
                basis=[runtime],
            )
        ]
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
                "findings": findings,
            }
        )
        enforce_finding_limit(sum(len(item.get("findings", [])) for item in runtime_results))
    for runtime in only_right:
        check_comparison_deadline(deadline)
        findings = [
            build_finding(
                code="VERIFY.RUNTIME.COVERAGE_CHANGED",
                category="runtime-coverage",
                message="runtime present in right bundle only",
                equality="unknown",
                confidence="high",
                basis=[runtime],
            )
        ]
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
                "findings": findings,
            }
        )
        enforce_finding_limit(sum(len(item.get("findings", [])) for item in runtime_results))

    if all_equal:
        message = "Evidence bundles match."
    elif only_left or only_right:
        message = "Evidence bundles differ: runtime coverage is not the same."
    elif not input_equal:
        message = "Evidence bundles differ: they were produced from different input specs."
    else:
        message = "Evidence bundles differ: the same input spec produced different output."

    result = build_verification_result(
        status="pass" if all_equal else "fail",
        comparison_mode="bundle-compare",
        baseline={"evidence": str(left_evidence), "status": left["status"]},
        candidate={"evidence": str(right_evidence), "status": right["status"]},
        inputs={"equal": input_equal, "leftSha256": left_input_sha, "rightSha256": right_input_sha},
        runtime_coverage={"shared": shared, "onlyLeft": only_left, "onlyRight": only_right},
        findings=[finding for runtime in runtime_results for finding in runtime.get("findings", [])],
    )
    return {
        "schemaVersion": result["schemaVersion"],
        "status": result["status"],
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
        return svg.replace(b"</svg>", b'<text x="8" y="16">demo drift</text></svg>', 1)
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
            f"<p>Category: <strong>{html.escape(str(pair.get('category', 'unknown-structural')))}</strong>; "
            f"equality: <strong>{html.escape(str(pair.get('equality', 'unknown')))}</strong>; "
            f"confidence: <strong>{html.escape(str(pair.get('confidence', 'low')))}</strong></p>"
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
        identity = baseline.get("identity") or {}
        supersedes = baseline.get("supersedes") or {}
        identity_rows = ""
        if identity:
            identity_rows += (
                f"<p>Baseline: <code>{html.escape(str(identity.get('evidence')))}</code></p>"
                f"<p>Baseline manifest: <code>{html.escape(str(identity.get('manifestSha256')))}</code></p>"
                f"<p>Baseline tool version: <code>{html.escape(str(identity.get('toolVersion')))}</code>; "
                f"generated: <code>{html.escape(str(identity.get('generatedAt')))}</code></p>"
            )
        if supersedes:
            identity_rows += (
                f"<p>Supersedes: <code>{html.escape(str(supersedes.get('evidence')))}</code> "
                f"(<code>{html.escape(str(supersedes.get('manifestSha256')))}</code>)</p>"
            )
        if baseline.get("note"):
            identity_rows += f"<p>Baseline note: {html.escape(str(baseline.get('note')))}</p>"
        baseline_block = (
            "<h2>Baseline</h2>"
            f"<p>Status: <strong>{html.escape(str(baseline.get('status', 'unknown')).upper())}</strong></p>"
            f"<p>{html.escape(str(baseline.get('message', '')))}</p>"
            f"<p>Input match: <strong>{'PASS' if baseline.get('inputEqual') else 'FAIL'}</strong></p>"
            f"{identity_rows}"
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
  <p>{html.escape(comparison["message"])}</p>
  <p>Demo drift: <code>{html.escape(manifest.get("demoDrift", "none"))}</code></p>
  <p>Spec hash: <code>{html.escape(manifest["input"]["sha256"])}</code></p>
  <table>
    <thead><tr><th>Runtime</th><th>Output</th><th>SHA-256</th><th>Bytes</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
  {baseline_block}
  {"".join(diff_blocks)}
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")


def _junit_failure_text(findings: list[dict[str, Any]], fallback: str) -> str:
    if not findings:
        return fallback
    lines = []
    for finding in findings:
        lines.append(
            f"{finding.get('code', 'VERIFY.UNKNOWN')}: {finding.get('message', fallback)} "
            f"[category={finding.get('category', 'unknown')}, "
            f"equality={finding.get('equality', 'unknown')}, "
            f"confidence={finding.get('confidence', 'low')}]"
        )
        basis = finding.get("basis") or []
        if basis:
            lines.append("basis: " + "; ".join(str(item) for item in basis))
    return "\n".join(lines)


def junit_testcases(manifest: dict[str, Any] | None, comparison: dict[str, Any]) -> list[dict[str, Any]]:
    baseline = (manifest or {}).get("baseline") or {}
    if baseline.get("status") in {"pass", "fail"}:
        cases = []
        input_equal = baseline.get("inputEqual")
        input_finding = []
        if input_equal is False:
            input_finding = [
                build_finding(
                    code="VERIFY.BASELINE.INPUT_CHANGED",
                    category="input-data",
                    message="input spec hash changed from baseline",
                    equality="unknown",
                    confidence="high",
                    basis=[
                        f"baseline={baseline.get('baselineInputSha256')}",
                        f"current={baseline.get('currentInputSha256')}",
                    ],
                )
            ]
        for runtime in baseline.get("runtimes", []):
            findings = list(runtime.get("findings", [])) + input_finding
            cases.append(
                {
                    "name": f"baseline/{runtime.get('runtime', 'unknown')}",
                    "classname": "StoneVerify.baseline",
                    "passed": bool(runtime.get("equal")) and input_equal is not False,
                    "message": runtime.get("reason", baseline.get("message", "")),
                    "findings": findings,
                }
            )
        if not cases:
            cases.append(
                {
                    "name": "baseline/input",
                    "classname": "StoneVerify.baseline",
                    "passed": input_equal is not False,
                    "message": baseline.get("message", comparison.get("message", "")),
                    "findings": input_finding,
                }
            )
        return cases

    pairs = comparison.get("pairs")
    if isinstance(pairs, list):
        return [
            {
                "name": f"{pair.get('left', 'left')} vs {pair.get('right', 'right')}",
                "classname": "StoneVerify.cross-runtime",
                "passed": bool(pair.get("equal")),
                "message": pair.get("likelyCause", comparison.get("message", "")),
                "findings": list(pair.get("findings", [])),
            }
            for pair in pairs
        ] or [
            {
                "name": "cross-runtime/no-op",
                "classname": "StoneVerify.cross-runtime",
                "passed": comparison.get("status") == "pass",
                "message": comparison.get("message", ""),
                "findings": [],
            }
        ]

    runtimes = comparison.get("runtimes")
    if isinstance(runtimes, list):
        return [
            {
                "name": f"bundle/{runtime.get('runtime', 'unknown')}",
                "classname": "StoneVerify.bundle-compare",
                "passed": bool(runtime.get("equal")),
                "message": runtime.get("reason", comparison.get("message", "")),
                "findings": list(runtime.get("findings", [])),
            }
            for runtime in runtimes
        ]

    return [
        {
            "name": "evidence/check",
            "classname": "StoneVerify.evidence",
            "passed": comparison.get("status") == "pass",
            "message": comparison.get("message", ""),
            "findings": [],
        }
    ]


def write_junit_report(path: pathlib.Path, manifest: dict[str, Any] | None, comparison: dict[str, Any]) -> None:
    cases = junit_testcases(manifest, comparison)
    failures = sum(1 for case in cases if not case["passed"])
    suite = ET.Element(
        "testsuite",
        {
            "name": "StoneVerify",
            "tests": str(len(cases)),
            "failures": str(failures),
            "errors": "0",
            "skipped": "0",
        },
    )
    for case in cases:
        testcase = ET.SubElement(
            suite,
            "testcase",
            {
                "classname": str(case["classname"]),
                "name": str(case["name"]),
                "time": "0",
            },
        )
        if not case["passed"]:
            failure = ET.SubElement(
                testcase, "failure", {"message": str(case["message"]), "type": "StoneVerifyFailure"}
            )
            failure.text = _junit_failure_text(case["findings"], str(case["message"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(suite).write(path, encoding="utf-8", xml_declaration=True)


def validate_junit_report(path: pathlib.Path) -> None:
    root = ET.parse(path).getroot()
    if root.tag != "testsuite":
        raise ValueError("JUnit report root must be testsuite")
    tests = int(root.attrib.get("tests", "-1"))
    failures = int(root.attrib.get("failures", "-1"))
    cases = root.findall("testcase")
    failure_count = len(root.findall("testcase/failure"))
    if tests != len(cases):
        raise ValueError("JUnit report tests count does not match testcase elements")
    if failures != failure_count:
        raise ValueError("JUnit report failures count does not match failure elements")


def _github_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def emit_github_actions_output(
    manifest: dict[str, Any] | None,
    comparison: dict[str, Any],
    *,
    stdout: Any = None,
    summary_path: pathlib.Path | None = None,
) -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    output = stdout or sys.stdout
    cases = junit_testcases(manifest, comparison)
    failed = [case for case in cases if not case["passed"]]
    if failed:
        for case in failed:
            text = _junit_failure_text(case["findings"], str(case["message"]))
            print(
                f"::error title={_github_escape('StoneVerify ' + str(case['name']))}::{_github_escape(text)}",
                file=output,
            )
    else:
        print("::notice title=StoneVerify::Verification passed", file=output)

    summary = summary_path or (
        pathlib.Path(os.environ["GITHUB_STEP_SUMMARY"]) if os.environ.get("GITHUB_STEP_SUMMARY") else None
    )
    if summary:
        summary.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "## StoneVerify",
            "",
            f"- Status: **{str(comparison.get('status', 'unknown')).upper()}**",
            f"- Test cases: {len(cases)}",
            f"- Failures: {len(failed)}",
            "",
        ]
        for case in failed:
            lines.append(f"- `{case['name']}`: {case['message']}")
        with summary.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")


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
            f"<p>Category: <strong>{html.escape(str(runtime.get('category', 'unknown-structural')))}</strong>; "
            f"equality: <strong>{html.escape(str(runtime.get('equality', 'unknown')))}</strong>; "
            f"confidence: <strong>{html.escape(str(runtime.get('confidence', 'low')))}</strong></p>"
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
  <p>{html.escape(comparison["message"])}</p>
  <p>Left bundle: <code>{html.escape(comparison["left"]["evidence"])}</code></p>
  <p>Right bundle: <code>{html.escape(comparison["right"]["evidence"])}</code></p>
  <p>Input spec match: <strong>{"PASS" if input_info.get("equal") else "FAIL"}</strong></p>
  {coverage_note}
  <table>
    <thead><tr><th>Runtime</th><th>Status</th><th>Left SHA-256</th>
    <th>Right SHA-256</th><th>Reason</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
  {"".join(detail_blocks)}
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
        help="Runtime to verify; repeat for multiple runtimes. Defaults to python for baseline checks, otherwise python and go.",
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
        "--supersedes-baseline",
        type=pathlib.Path,
        help="Prior baseline evidence directory replaced by the --baseline-evidence bundle; recorded for review only.",
    )
    parser.add_argument(
        "--baseline-note",
        help="Free-text note recorded on the baseline result, such as an approval note or ticket reference.",
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
    parser.add_argument(
        "--junit-report",
        type=pathlib.Path,
        help="Write a JUnit-compatible XML report derived from the canonical StoneVerify result.",
    )
    parser.add_argument(
        "--go-binary",
        type=pathlib.Path,
        help=f"Path to the {GO_BINARY_NAME} adapter binary. Defaults to {GO_BINARY_ENV}, then PATH.",
    )
    parser.add_argument(
        "--from-source",
        action="store_true",
        help="Development fallback for --runtime go: run the Go adapter from this source checkout with go run.",
    )
    parser.add_argument(
        "--output-format",
        choices=["human", "json"],
        default="human",
        help="Output format. 'json' emits a single JSON object to stdout instead of human-readable text.",
    )
    args = parser.parse_args()

    if args.compare_report and not args.compare_evidence:
        parser.error("--compare-report requires --compare-evidence")
    if args.supersedes_baseline and not args.baseline_evidence:
        parser.error("--supersedes-baseline requires --baseline-evidence")

    if args.check_evidence:
        try:
            result = check_evidence_bundle(args.check_evidence.resolve())
        except ResourceLimitError as exc:
            print(f"StoneVerify RESOURCE_LIMIT: {exc}", file=sys.stderr)
            return EXIT_RESOURCE_LIMIT
        exit_code = 0 if result["status"] == "pass" else 1
        if args.output_format == "json":
            print(json.dumps({"status": result["status"], "message": result["message"], "exitCode": exit_code}))
        else:
            print(f"StoneVerify evidence {result['status'].upper()}: {result['message']}")
            print(f"evidence: {result['evidence']}")
            if result["missing"]:
                print("missing: " + ", ".join(result["missing"]))
            if result["manifestErrors"]:
                print("manifest errors: " + "; ".join(result["manifestErrors"]))
            if result["checksumErrors"]:
                print("checksum errors: " + "; ".join(result["checksumErrors"]))
        comparison = {
            "schemaVersion": SCHEMA_VERSION,
            "status": result["status"],
            "message": result["message"],
        }
        if args.junit_report:
            report_path = args.junit_report.resolve()
            write_junit_report(report_path, None, comparison)
            validate_junit_report(report_path)
            if args.output_format != "json":
                print(f"junit: {report_path}")
        emit_github_actions_output(None, comparison)
        return exit_code

    if args.compare_evidence:
        left_path, right_path = (path.resolve() for path in args.compare_evidence)
        try:
            result = compare_evidence_bundles(left_path, right_path)
        except ResourceLimitError as exc:
            print(f"StoneVerify RESOURCE_LIMIT: {exc}", file=sys.stderr)
            return EXIT_RESOURCE_LIMIT
        exit_code = 0 if result["status"] == "pass" else 1
        if args.output_format == "json":
            print(json.dumps({"status": result["status"], "message": result["message"], "exitCode": exit_code}))
        else:
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
            if args.output_format != "json":
                print(f"report: {report_path}")
        if args.junit_report:
            junit_path = args.junit_report.resolve()
            write_junit_report(junit_path, None, result)
            validate_junit_report(junit_path)
            if args.output_format != "json":
                print(f"junit: {junit_path}")
        emit_github_actions_output(None, result)
        return exit_code

    if args.spec is None:
        parser.error("spec is required unless --check-evidence or --compare-evidence is used")
    if args.evidence is None:
        parser.error("--evidence is required unless --check-evidence or --compare-evidence is used")

    spec_path = args.spec.resolve()
    evidence = args.evidence.resolve()
    runtimes = args.runtime or (["python"] if args.baseline_evidence else ["python", "go"])
    try:
        raw_spec_bytes = spec_path.read_bytes()
        if len(raw_spec_bytes) > MAX_SPEC_BYTES:
            raise ResourceLimitError("LIMIT.SPEC_BYTES", "$", MAX_SPEC_BYTES, len(raw_spec_bytes))
        spec_data = json.loads(raw_spec_bytes.decode("utf-8"))
        ChartSpec.from_dict(spec_data, raw_size_hint=len(raw_spec_bytes))
    except ResourceLimitError as exc:
        print(f"StoneVerify RESOURCE_LIMIT: {exc}", file=sys.stderr)
        return EXIT_RESOURCE_LIMIT
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, SpecError, CapabilityError) as exc:
        print(f"StoneVerify INVALID_SPEC: {exc}", file=sys.stderr)
        return EXIT_INVALID_SPEC
    spec_bytes = canonical_json_bytes(spec_data)

    evidence.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(dir=evidence.parent, prefix=f".{evidence.name}.tmp-") as tmpdir:
            staging = pathlib.Path(tmpdir)
            (staging / "input-spec.json").write_bytes(spec_bytes)

            outputs: dict[str, bytes] = {}
            runtime_metadata = []
            for index, runtime in enumerate(runtimes):
                if runtime == "python":
                    try:
                        svg, metadata = render_python(spec_data, raw_size_hint=len(raw_spec_bytes))
                    except ResourceLimitError as exc:
                        print(f"StoneVerify RESOURCE_LIMIT: {exc}", file=sys.stderr)
                        return EXIT_RESOURCE_LIMIT
                    except (SpecError, CapabilityError) as exc:
                        print(f"StoneVerify INVALID_SPEC: {exc}", file=sys.stderr)
                        return EXIT_INVALID_SPEC
                else:
                    try:
                        svg, metadata = render_go(spec_path, go_binary=args.go_binary, from_source=args.from_source)
                    except ResourceLimitError as exc:
                        print(f"StoneVerify RESOURCE_LIMIT: {exc}", file=sys.stderr)
                        return EXIT_RESOURCE_LIMIT
                    except RuntimeError as exc:
                        print(f"StoneVerify ADAPTER_FAILURE: {exc}", file=sys.stderr)
                        return EXIT_ADAPTER
                drift_applied = args.demo_drift if args.demo_drift != "none" and index == len(runtimes) - 1 else "none"
                svg = apply_demo_drift(svg, drift_applied)
                output_name = f"{runtime}-output.svg"
                (staging / output_name).write_bytes(svg)
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
                "generatedAt": generated_at(),
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
                    stoneverify_version=STONEVERIFY_VERSION,
                    go_version=go_version,
                ),
            }
            baseline_dir = args.baseline_evidence.resolve() if args.baseline_evidence else None
            baseline_manifest = load_baseline(baseline_dir) if baseline_dir else None
            supersedes_baseline_dir = args.supersedes_baseline.resolve() if args.supersedes_baseline else None
            supersedes_baseline_manifest = load_baseline(supersedes_baseline_dir) if supersedes_baseline_dir else None
            baseline = compare_baseline(
                manifest,
                outputs,
                baseline_manifest,
                baseline_dir=baseline_dir,
                supersedes_baseline_dir=supersedes_baseline_dir,
                supersedes_baseline_manifest=supersedes_baseline_manifest,
                note=args.baseline_note,
            )
            if baseline["status"] == "fail":
                comparison = {
                    **comparison,
                    "status": "fail",
                    "message": comparison["message"] + " Baseline comparison failed.",
                }
            manifest["status"] = comparison["status"]
            manifest["baseline"] = baseline

            (staging / "comparison.json").write_text(
                json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            write_report(staging / "report.html", manifest, comparison)

            manifest["evidence"] = {
                "inputSpec": sha256_digest(manifest["input"]["sha256"]),
                "artifacts": {runtime["output"]: sha256_digest(runtime["sha256"]) for runtime in runtime_metadata},
            }
            (staging / "manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )

            checksum_paths = ["manifest.json", "input-spec.json", "comparison.json", "report.html"]
            checksum_paths.extend(runtime["output"] for runtime in runtime_metadata)
            checksums = [f"{sha256_file(staging / name)}  {name}" for name in sorted(checksum_paths)]
            (staging / "checksums.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
            evidence_bundle_size(staging)
            commit_evidence_bundle(staging, evidence)
    except ResourceLimitError as exc:
        print(f"StoneVerify RESOURCE_LIMIT: {exc}", file=sys.stderr)
        return EXIT_RESOURCE_LIMIT

    if args.junit_report:
        junit_path = args.junit_report.resolve()
        write_junit_report(junit_path, manifest, comparison)
        validate_junit_report(junit_path)
    exit_code = EXIT_PASS if comparison["status"] == "pass" else EXIT_DIFFERENCES
    if args.output_format == "json":
        print(
            json.dumps(
                {
                    "status": comparison["status"],
                    "message": comparison["message"],
                    "exitCode": exit_code,
                    "evidence": str(evidence),
                }
            )
        )
    else:
        print(f"StoneVerify {comparison['status'].upper()}: {comparison['message']}")
        print(f"evidence: {evidence}")
        if args.junit_report:
            print(f"junit: {args.junit_report.resolve()}")
    emit_github_actions_output(manifest, comparison)
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"StoneVerify INTERNAL: {exc}", file=sys.stderr)
        raise SystemExit(EXIT_INTERNAL) from exc
