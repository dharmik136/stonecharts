#!/usr/bin/env python3
"""Run all local quality checks in sequence. Exit non-zero on first failure."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS: list[tuple[str, list[str]]] = [
    ("ruff check", [sys.executable, "-m", "ruff", "check", "libs/python/", "tools/"]),
    ("ruff format", [sys.executable, "-m", "ruff", "format", "--check", "libs/python/", "tools/"]),
    ("pytest", [sys.executable, "-m", "pytest", "libs/python/tests", "-q"]),
    ("doc checks", [sys.executable, "tools/check_docs.py"]),
    ("cross-language parity", [sys.executable, "tools/check_cross_language_parity.py"]),
    (
        "schema compat (identity)",
        [
            sys.executable,
            "tools/check_schema_compat.py",
            "spec/chart-spec.schema.json",
            "spec/chart-spec.schema.json",
        ],
    ),
    (
        "chart admission (certified)",
        [
            sys.executable,
            "tools/check_chart_admission.py",
            "line-basic",
            "column",
            "area",
            "bar",
            "scatter",
            "bubble",
        ],
    ),
]

CHECKS_REQUIRING_GO: list[tuple[str, list[str]]] = [
    ("fuzz property", [sys.executable, "tools/check_fuzz_property.py"]),
]


def main() -> int:
    all_checks = list(CHECKS)
    if shutil.which("go"):
        all_checks.extend(CHECKS_REQUIRING_GO)
    else:
        print("  SKIP  fuzz property (Go not installed)\n")

    passed = 0
    failed = 0
    for name, cmd in all_checks:
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if result.returncode == 0:
            passed += 1
            print(f"  PASS  {name}")
        else:
            failed += 1
            print(f"  FAIL  {name}")
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines()[-5:]:
                    print(f"        {line}")
            if result.stderr.strip():
                for line in result.stderr.strip().splitlines()[-5:]:
                    print(f"        {line}")

    print(f"\n{passed + failed} checks: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
