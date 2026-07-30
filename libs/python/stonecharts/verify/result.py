"""Canonical result envelope for StoneVerify (WORK-VERIFY-014A / REQ-VERIFY-002)."""

from __future__ import annotations

import locale
import platform
import time
from typing import Any

SCHEMA_VERSION = 1
RESULT_SCHEMA_URI = "https://stonecharts.dev/schemas/stoneverify-result.schema.json"

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
