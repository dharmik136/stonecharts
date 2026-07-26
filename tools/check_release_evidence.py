#!/usr/bin/env python3
"""Validate a StoneCharts release evidence manifest and its candidate archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover - bootstrap path
    print(
        "missing release evidence dependency: "
        f"{exc.name}; install with `python -m pip install -e \"libs/python[dev]\"`",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs" / "releases" / "0.0.0.1" / "evidence" / "rc.1" / "manifest.json"
EVIDENCE_REGISTRY = ROOT / "docs" / "quality" / "evidence-registry.yaml"


def schema_for(manifest_path: Path) -> Path:
    # docs/releases/<release>/evidence/<candidate>/manifest.json -> .../evidence/manifest.schema.json
    return manifest_path.parent.parent / "manifest.schema.json"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{rel(path)}: expected a YAML mapping")
    return value


def error(message: str) -> None:
    print(f"release evidence validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_schema(manifest: dict[str, Any], schema_path: Path) -> None:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    issues = sorted(validator.iter_errors(manifest), key=lambda item: list(item.path))
    if issues:
        lines = []
        for issue in issues:
            where = ".".join(str(part) for part in issue.absolute_path) or "$"
            lines.append(f"{where}: {issue.message}")
        error("; ".join(lines))


def parse_hashes(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            error(f"{rel(path)}: malformed sha256 line: {raw_line!r}")
        digest = parts[0].lower()
        file_path = " ".join(parts[1:])
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            error(f"{rel(path)}: invalid sha256 digest for {file_path}")
        if file_path in entries:
            error(f"{rel(path)}: duplicate hash entry for {file_path}")
        entries[file_path] = digest
    return entries


def validate_artifact(path: Path, expected_sha: str | None = None) -> None:
    if not path.exists():
        error(f"missing artifact: {rel(path)}")
    actual_sha = sha256(path)
    if expected_sha is not None and actual_sha != expected_sha:
        error(f"sha256 mismatch for {rel(path)}")


def validate_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    implemented = {
        item["id"]
        for item in load_yaml(EVIDENCE_REGISTRY)["evidence"]
        if item["status"] == "implemented"
    }

    evidence_ids: set[str] = set()
    for entry in manifest["evidence"]:
        evidence_id = entry["id"]
        if evidence_id in evidence_ids:
            error(f"duplicate evidence id: {evidence_id}")
        evidence_ids.add(evidence_id)
        if evidence_id not in implemented and evidence_id != "TEST-RELEASE-EVIDENCE":
            error(f"unknown evidence id in manifest: {evidence_id}")
        status = entry["status"]
        path_value = entry["path"]
        sha_value = entry["sha256"]
        if status == "passed":
            if path_value is None or sha_value is None:
                error(f"{evidence_id}: passed evidence must include path and sha256")
            target = (ROOT / path_value).resolve()
            if not target.exists():
                error(f"{evidence_id}: missing evidence file {path_value}")
            if sha256(target) != sha_value:
                error(f"{evidence_id}: sha256 mismatch for {path_value}")
        else:
            if path_value is not None or sha_value is not None:
                error(f"{evidence_id}: non-passed evidence must not include a path or sha256")

    missing = sorted(implemented - evidence_ids)
    if missing:
        error(f"manifest does not enumerate implemented evidence ids: {', '.join(missing)}")

    artifact_paths: set[str] = set()
    for artifact in manifest["artifacts"]:
        path_value = artifact["path"]
        if path_value in artifact_paths:
            error(f"duplicate artifact path: {path_value}")
        artifact_paths.add(path_value)
        target = (ROOT / path_value).resolve()
        validate_artifact(target, artifact["sha256"])
        if target.stat().st_size != artifact["bytes"]:
            error(f"byte count mismatch for {path_value}")

    hashes_entry = next((a for a in manifest["artifacts"] if a["path"].endswith("hashes.sha256")), None)
    if hashes_entry is None:
        error("manifest does not declare hashes.sha256 as an artifact")

    hashes_path = ROOT / hashes_entry["path"]
    hash_map = parse_hashes(hashes_path)
    for artifact in manifest["artifacts"]:
        if artifact["path"] == hashes_entry["path"]:
            continue
        expected = artifact["sha256"]
        actual = hash_map.get(artifact["path"])
        if actual is None:
            error(f"hash file missing entry for {artifact['path']}")
        if actual != expected:
            error(f"hash file mismatch for {artifact['path']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    if not manifest_path.exists():
        error(f"missing manifest: {rel(manifest_path)}")

    manifest = load_json(manifest_path)
    schema_path = schema_for(manifest_path)
    if not schema_path.exists():
        error(f"missing schema: {rel(schema_path)}")
    validate_schema(manifest, schema_path)
    validate_manifest(manifest_path, manifest)
    print(f"release evidence PASS: {rel(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
