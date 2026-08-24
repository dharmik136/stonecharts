#!/usr/bin/env python3
"""Validate a StoneCharts release evidence manifest and its candidate archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover - bootstrap path
    print(
        f'missing release evidence dependency: {exc.name}; install with `python -m pip install -e "libs/python[dev]"`',
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs" / "releases" / "0.0.0.1" / "evidence" / "rc.1" / "manifest.json"
EVIDENCE_REGISTRY = ROOT / "docs" / "quality" / "evidence-registry.yaml"
RISK_REGISTRY = ROOT / "docs" / "governance" / "risk-register.yaml"


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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def repository_path(path_value: str, label: str) -> Path:
    target = (ROOT / path_value).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        error(f"{label}: path escapes the repository: {path_value}")
    return target


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


def source_blob(manifest: dict[str, Any], path_value: str) -> bytes | None:
    """Return canonical tagged bytes when the artifact existed in release source."""
    if manifest.get("release") != "0.0.0.34":
        return None
    commit = manifest.get("source", {}).get("commit")
    if not isinstance(commit, str) or not commit:
        return None
    try:
        process = subprocess.run(
            ["git", "show", f"{commit}:{path_value}"],
            cwd=ROOT,
            capture_output=True,
        )
    except OSError:
        return None
    return process.stdout if process.returncode == 0 else None


def artifact_digest_and_size(manifest: dict[str, Any], path_value: str, path: Path) -> tuple[str, int]:
    blob = source_blob(manifest, path_value)
    if blob is not None:
        return sha256_bytes(blob), len(blob)
    return sha256(path), path.stat().st_size


def validate_artifact(manifest: dict[str, Any], path_value: str, path: Path, expected_sha: str | None = None) -> int:
    if not path.exists():
        error(f"missing artifact: {rel(path)}")
    actual_sha, actual_size = artifact_digest_and_size(manifest, path_value, path)
    if expected_sha is not None and actual_sha != expected_sha:
        error(f"sha256 mismatch for {rel(path)}")
    return actual_size


def validate_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    implemented = {item["id"] for item in load_yaml(EVIDENCE_REGISTRY)["evidence"] if item["status"] == "implemented"}

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
            target = repository_path(path_value, evidence_id)
            if not target.exists():
                error(f"{evidence_id}: missing evidence file {path_value}")
            actual_sha, _ = artifact_digest_and_size(manifest, path_value, target)
            if actual_sha != sha_value:
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
        target = repository_path(path_value, "artifact")
        actual_size = validate_artifact(manifest, path_value, target, artifact["sha256"])
        if actual_size != artifact["bytes"]:
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

    if manifest["release"] == "0.0.0.34":
        validate_0034(manifest, artifact_paths)


def validate_0034(manifest: dict[str, Any], artifact_paths: set[str]) -> None:
    """Enforce the hardened release contract introduced in 0.0.0.34."""
    if manifest["source"]["treeClean"] is not True:
        error("0.0.0.34 source must have been qualified from a clean tree")
    if any(entry["status"] != "passed" for entry in manifest["evidence"]):
        error("0.0.0.34 requires every implemented evidence item to pass")

    qualification_paths = [path for path in artifact_paths if path.endswith("/qualification-results.json")]
    if len(qualification_paths) != 1:
        error("0.0.0.34 must declare exactly one qualification-results.json artifact")
    qualification = load_json(repository_path(qualification_paths[0], "qualification results"))
    commands = qualification.get("commands", [])
    if qualification.get("status") != "pass" or not commands:
        error("0.0.0.34 qualification results are not passing")
    failed_commands = [item.get("id", "<unknown>") for item in commands if item.get("status") != "pass"]
    if failed_commands:
        error(f"0.0.0.34 has failed qualification commands: {', '.join(failed_commands)}")
    if qualification.get("sourceCommit") != manifest["source"]["commit"]:
        error("qualification source commit differs from manifest source commit")

    provenance_paths = [path for path in artifact_paths if path.endswith("/provenance.json")]
    if len(provenance_paths) != 1:
        error("0.0.0.34 must declare exactly one provenance.json artifact")
    provenance = load_json(repository_path(provenance_paths[0], "provenance"))
    expected_provenance = {
        "release": manifest["release"],
        "candidate": manifest["candidate"],
        "repository": manifest["source"]["repository"],
        "commit": manifest["source"]["commit"],
        "tag": manifest["source"]["tag"],
        "treeCleanAtStart": True,
    }
    for key, expected in expected_provenance.items():
        if provenance.get(key) != expected:
            error(f"provenance.{key} differs from the release manifest")

    if not any(path.endswith(".whl") for path in artifact_paths):
        error("0.0.0.34 is missing a qualified Python wheel artifact")
    if not any(path.endswith(".tar.gz") for path in artifact_paths):
        error("0.0.0.34 is missing a qualified Python source artifact")

    risk_rows = load_yaml(RISK_REGISTRY)["risks"]
    expected_risks = {row["id"]: row for row in risk_rows}
    actual_risks = {row["id"]: row for row in manifest["risks"]}
    if set(actual_risks) != set(expected_risks):
        error("0.0.0.34 risk dispositions do not cover the complete governed risk register")
    for risk_id, governed in expected_risks.items():
        expected_disposition = governed["status"] if governed["status"] in {"closed", "accepted"} else "not-applicable"
        actual = actual_risks[risk_id]
        if actual["disposition"] != expected_disposition:
            error(f"{risk_id}: disposition differs from the governed risk register")
        rationale = actual.get("rationale") or ""
        if governed["title"] not in rationale or governed["mitigation"] not in rationale:
            error(f"{risk_id}: rationale must include its specific title and mitigation")


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
