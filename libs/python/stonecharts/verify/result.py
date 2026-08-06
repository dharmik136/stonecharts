"""Canonical result envelope for StoneVerify (WORK-VERIFY-014A / REQ-VERIFY-002)."""

from __future__ import annotations

import json
import locale
import pathlib
import platform
import time
from typing import Any

SCHEMA_VERSION = 1
SCHEMA_VERSION_MIN = 1
SCHEMA_VERSION_MAX = 1
RESULT_SCHEMA_URI = "https://stonecharts.dev/schemas/stoneverify-result.schema.json"

_SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[4] / "spec" / "stoneverify-result.schema.json"

_VALID_EQUALITY = {"byte", "structural", "semantic", "unknown"}
_VALID_CONFIDENCE = {"high", "medium", "low"}


def digest(algorithm: str, value: str) -> dict[str, str]:
    return {"algorithm": algorithm, "value": value}


def sha256_digest(value: str) -> dict[str, str]:
    return digest("sha-256", value)


def capture_environment(
    *,
    stonecharts_version: str,
    stoneverify_version: str,
    go_version: str | None = None,
) -> dict[str, Any]:
    try:
        current_locale = locale.getlocale()[0] or "C"
    except (ValueError, TypeError):
        current_locale = "C"
    return {
        "os": platform.system(),
        "arch": platform.machine(),
        "pythonVersion": platform.python_version(),
        "goVersion": go_version,
        "stonechartsVersion": stonecharts_version,
        "stoneverifyVersion": stoneverify_version,
        "schemaVersion": SCHEMA_VERSION,
        "locale": current_locale,
        "timezone": time.strftime("%z") or "+0000",
    }


def build_finding(
    *,
    code: str,
    category: str,
    message: str,
    equality: str = "unknown",
    confidence: str = "low",
    basis: list[str] | None = None,
) -> dict[str, Any]:
    if equality not in _VALID_EQUALITY:
        raise ValueError(f"unsupported equality level: {equality!r}")
    if confidence not in _VALID_CONFIDENCE:
        raise ValueError(f"unsupported confidence level: {confidence!r}")
    return {
        "code": code,
        "category": category,
        "message": message,
        "equality": equality,
        "confidence": confidence,
        "basis": list(basis or []),
    }


def build_verification_result(
    *,
    status: str,
    comparison_mode: str,
    baseline: dict[str, Any] | None = None,
    candidate: dict[str, Any] | None = None,
    inputs: dict[str, Any] | None = None,
    runtime_coverage: dict[str, Any] | None = None,
    findings: list[dict[str, Any]] | None = None,
    evidence: dict[str, Any] | None = None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in {"pass", "fail", "not-checked"}:
        raise ValueError(f"unsupported status: {status!r}")
    if comparison_mode not in {"cross-runtime", "baseline", "bundle-compare"}:
        raise ValueError(f"unsupported comparison mode: {comparison_mode!r}")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "resultSchema": RESULT_SCHEMA_URI,
        "status": status,
        "comparisonMode": comparison_mode,
        "baseline": baseline,
        "candidate": candidate,
        "inputs": dict(inputs or {}),
        "runtimeCoverage": dict(runtime_coverage or {}),
        "findings": list(findings or []),
        "evidence": dict(evidence or {}),
        "environment": environment,
    }


def check_schema_version(version: Any) -> str | None:
    """Return ``None`` if *version* is supported, or an error string otherwise."""
    if not isinstance(version, int):
        return f"schema version must be an integer, got {type(version).__name__}"
    if version < SCHEMA_VERSION_MIN:
        return f"schema version {version} is below minimum supported ({SCHEMA_VERSION_MIN})"
    if version > SCHEMA_VERSION_MAX:
        return f"schema version {version} is above maximum supported ({SCHEMA_VERSION_MAX})"
    return None


def validate_against_schema(result: dict[str, Any]) -> list[str]:
    """Validate *result* against the canonical JSON Schema.

    Returns a list of human-readable error strings (empty means valid).
    If *jsonschema* is not installed the function returns an empty list
    silently so that validation remains a dev-only concern.
    """
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return []

    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(result)]
