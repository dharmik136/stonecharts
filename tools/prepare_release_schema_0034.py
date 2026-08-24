#!/usr/bin/env python3
"""Prepare or verify the immutable 0.0.0.34 schema snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "0.0.0.34"
RELEASE_DIR = ROOT / "spec" / "released" / RELEASE
CURRENT = ROOT / "spec" / "released" / "current.json"
SCHEMAS = {
    "chartSpec": ROOT / "spec" / "chart-spec.schema.json",
    "stoneverifyResult": ROOT / "spec" / "stoneverify-result.schema.json",
}
FILENAMES = {
    "chartSpec": "chart-spec.schema.json",
    "stoneverifyResult": "stoneverify-result.schema.json",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def expected(source_commit: str) -> tuple[dict[str, bytes], str]:
    snapshots = {FILENAMES[key]: path.read_bytes() for key, path in SCHEMAS.items()}
    current = {
        "release": RELEASE,
        "sourceCommit": source_commit,
        "schemas": {
            key: {
                "path": f"{RELEASE}/{FILENAMES[key]}",
                "sha256": sha256_bytes(snapshots[FILENAMES[key]]),
            }
            for key in ("chartSpec", "stoneverifyResult")
        },
    }
    return snapshots, json.dumps(current, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--source-commit", help="Commit that supplied the active schema bytes")
    args = parser.parse_args()

    if args.generate:
        source_commit = args.source_commit or head()
    elif CURRENT.exists():
        source_commit = json.loads(CURRENT.read_text(encoding="utf-8")).get("sourceCommit", "")
    else:
        source_commit = args.source_commit or ""
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        print("source commit must be a full 40-character Git object id", file=sys.stderr)
        return 1

    snapshots, current = expected(source_commit)
    if args.generate:
        RELEASE_DIR.mkdir(parents=True, exist_ok=True)
        for name, content in snapshots.items():
            (RELEASE_DIR / name).write_bytes(content)
        CURRENT.write_text(current, encoding="utf-8")
        print(f"prepared spec/released/{RELEASE} from {source_commit}")

    if args.check or not args.generate:
        failures = []
        expected_names = set(snapshots)
        actual_names = {path.name for path in RELEASE_DIR.iterdir()} if RELEASE_DIR.exists() else set()
        if actual_names != expected_names:
            failures.append(f"snapshot file set differs: expected {sorted(expected_names)}, got {sorted(actual_names)}")
        for name, content in snapshots.items():
            path = RELEASE_DIR / name
            if not path.exists() or path.read_bytes() != content:
                failures.append(f"{path.relative_to(ROOT).as_posix()} differs from the active schema")
        if not CURRENT.exists() or CURRENT.read_text(encoding="utf-8") != current:
            failures.append("spec/released/current.json is stale")
        if failures:
            print("release schema snapshot FAILED", file=sys.stderr)
            for failure in failures:
                print(f"- {failure}", file=sys.stderr)
            return 1
        print(f"release schema snapshot PASS: {RELEASE} ({source_commit})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
