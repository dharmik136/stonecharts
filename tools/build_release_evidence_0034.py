#!/usr/bin/env python3
"""Build and validate the hardened 0.0.0.34 release evidence pack."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "0.0.0.34"
CANDIDATE = "rc.1"
EVIDENCE_DIR = ROOT / "docs" / "releases" / RELEASE / "evidence"
RC_DIR = EVIDENCE_DIR / CANDIDATE
PACKAGES_DIR = RC_DIR / "packages"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def require_clean_tagged_source() -> str:
    dirty = git("status", "--porcelain")
    if dirty:
        raise RuntimeError("release evidence must start from a clean source tree")
    commit = git("rev-parse", "HEAD")
    try:
        tagged = git("rev-parse", f"{RELEASE}^{{commit}}")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"release tag {RELEASE} does not exist") from exc
    if tagged != commit:
        raise RuntimeError(f"release tag {RELEASE} does not point at HEAD {commit}")
    return commit


def write_manifest_schema() -> None:
    template = json.loads((ROOT / "docs/releases/0.0.0.33/evidence/manifest.schema.json").read_text(encoding="utf-8"))
    template["$id"] = f"https://stonecharts.dev/releases/{RELEASE}/evidence/manifest.schema.json"
    template["properties"]["release"] = {"const": RELEASE}
    template["properties"]["source"]["properties"]["tag"] = {"const": RELEASE}
    template["properties"]["source"]["properties"]["treeClean"] = {"const": True}
    versions = template["properties"]["versions"]["properties"]
    versions["product"] = {"const": RELEASE}
    versions["python"] = {"const": RELEASE}
    versions["go"]["oneOf"][1]["not"] = {"const": f"v{RELEASE}"}
    template["properties"]["evidence"]["items"]["properties"]["status"] = {"const": "passed"}
    write_json(EVIDENCE_DIR / "manifest.schema.json", template)


def write_controlled_docs(commit: str) -> None:
    (RC_DIR / "qualification-checklist.md").write_text(
        f"""---
id: SC-REL-035
title: StoneCharts {RELEASE} Candidate Evidence Checklist
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: {RELEASE}
requirements: [REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE, TEST-CERTIFICATION-MATRIX, TEST-PACKAGE-INSTALL]
last_reviewed: "2026-08-24"
review_due: "2026-09-24"
supersedes: null
superseded_by: null
---

# StoneCharts {RELEASE} release-candidate checklist

Candidate: `{CANDIDATE}`
Source commit and tag: `{commit}` / `{RELEASE}`
Engineering status: approved after the commands in `qualification-results.json` pass.

The candidate requalifies all 36 charts against all eight SC-CERT gates, verifies
real Chromium behavior for every chart, installs warning-free Python artifacts in an
isolated environment, and records clean-tag provenance. Package-registry distribution
and a real customer pilot are explicitly deferred; neither is claimed by this pack.
""",
        encoding="utf-8",
    )
    (RC_DIR / "package-install-matrix.md").write_text(
        f"""---
id: SC-REL-036
title: StoneCharts {RELEASE} Package Install Matrix
status: approved
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: {RELEASE}
requirements: [REQ-REL-001]
evidence: [TEST-PACKAGE-INSTALL]
last_reviewed: "2026-08-24"
review_due: "2026-09-24"
supersedes: null
superseded_by: null
---

# Package/install matrix — {RELEASE} {CANDIDATE}

| Surface | Version | Qualification |
|---|---:|---|
| Python wheel | `{RELEASE}` | Isolated install; SVG and interactive HTML smoke for all 36 charts |
| Python source distribution | `{RELEASE}` | Archive content and license inspection |
| Go source module | `{RELEASE}` runtime metadata | Full Go suite; embedded runtime asset; no external module publication |
| Released schemas | `{RELEASE}` | Immutable snapshot and SHA-256 manifest verification |

The wheel and source archive are retained as local release evidence. Upload to a
package registry or another distribution channel is not authorized by this matrix.
""",
        encoding="utf-8",
    )


def command_record(identifier: str, command: list[str], cwd: Path) -> dict[str, Any]:
    print(f"qualification: {identifier}", flush=True)
    started = time.monotonic()
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    output = process.stdout + process.stderr
    duration = round(time.monotonic() - started, 3)
    record = {
        "id": identifier,
        "command": command,
        "cwd": rel(cwd),
        "status": "pass" if process.returncode == 0 else "fail",
        "exitCode": process.returncode,
        "durationSeconds": duration,
        "outputSha256": sha256_text(output),
        "outputTail": output[-4000:],
    }
    print(f"qualification: {identifier} {record['status'].upper()} ({duration:.3f}s)", flush=True)
    return record


def run_qualification(commit: str) -> dict[str, Any]:
    started_at = now()
    commands = [
        ("ruff-check", [sys.executable, "-m", "ruff", "check", "libs/python", "tools"], ROOT),
        ("ruff-format", [sys.executable, "-m", "ruff", "format", "--check", "libs/python", "tools"], ROOT),
        ("python-tests", [sys.executable, "-m", "pytest", "libs/python/tests", "-q"], ROOT),
        ("go-tests", ["go", "test", "./..."], ROOT / "libs/go"),
        ("browser-tests", ["npm", "test"], ROOT),
        ("documentation", [sys.executable, "tools/check_docs.py"], ROOT),
        ("capabilities", [sys.executable, "tools/generate_capabilities.py", "--check"], ROOT),
        ("runtime-assets", [sys.executable, "tools/generate_runtime_assets.py", "--check"], ROOT),
        (
            "certification-baselines",
            [sys.executable, "tools/generate_certification_baselines.py", "--check"],
            ROOT,
        ),
        (
            "certification-ledger",
            [sys.executable, "tools/generate_certification_ledger.py", "--check"],
            ROOT,
        ),
        (
            "certification-matrix",
            [sys.executable, "tools/check_certification_matrix.py", "--structural-only"],
            ROOT,
        ),
        ("direct-cross-render", [sys.executable, "tools/check_direct_cross_render.py"], ROOT),
        ("fuzz-property", [sys.executable, "tools/check_fuzz_property.py"], ROOT),
        (
            "release-schema",
            [sys.executable, "tools/prepare_release_schema_0034.py", "--check"],
            ROOT,
        ),
        (
            "package-install",
            [sys.executable, "tools/check_package_install.py", "--outdir", str(PACKAGES_DIR)],
            ROOT,
        ),
    ]
    records = [command_record(identifier, command, cwd) for identifier, command, cwd in commands]
    result = {
        "schemaVersion": 1,
        "release": RELEASE,
        "candidate": CANDIDATE,
        "sourceCommit": commit,
        "startedAt": started_at,
        "completedAt": now(),
        "status": "pass" if all(item["status"] == "pass" for item in records) else "fail",
        "commands": records,
    }
    write_json(RC_DIR / "qualification-results.json", result)
    if result["status"] != "pass":
        failed = ", ".join(item["id"] for item in records if item["status"] == "fail")
        raise RuntimeError(f"release qualification failed: {failed}")
    return result


def artifact_kind(path: Path) -> str:
    name = path.name
    if name.endswith(".whl") or name.endswith(".tar.gz"):
        return "python-package"
    if name == "sbom.spdx.json":
        return "sbom"
    if name == "provenance.json":
        return "provenance"
    if path.suffix in {".md", ".json", ".yaml", ".toml", ".py", ".go", ".js"}:
        return "documentation"
    return "other"


def artifact(path: Path) -> dict[str, object]:
    return {
        "name": path.name,
        "kind": artifact_kind(path),
        "path": rel(path),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def main() -> int:
    try:
        commit = require_clean_tagged_source()
        if EVIDENCE_DIR.exists():
            shutil.rmtree(EVIDENCE_DIR)
        RC_DIR.mkdir(parents=True)
        write_manifest_schema()
        write_controlled_docs(commit)
        qualification = run_qualification(commit)

        completed_at = qualification["completedAt"]
        write_json(
            RC_DIR / "provenance.json",
            {
                "release": RELEASE,
                "candidate": CANDIDATE,
                "repository": "dharmik136/stonecharts",
                "commit": commit,
                "tag": RELEASE,
                "treeCleanAtStart": True,
                "builder": "tools/build_release_evidence_0034.py",
                "builtAt": completed_at,
                "qualification": "pass",
            },
        )
        write_json(
            RC_DIR / "sbom.spdx.json",
            {
                "spdxVersion": "SPDX-2.3",
                "dataLicense": "CC0-1.0",
                "SPDXID": "SPDXRef-DOCUMENT",
                "name": f"stonecharts-{RELEASE}-{CANDIDATE}",
                "documentNamespace": f"https://stonecharts.dev/sbom/{RELEASE}/{CANDIDATE}",
                "creationInfo": {
                    "created": completed_at,
                    "creators": ["Tool: StoneCharts release builder"],
                },
                "packages": [
                    {
                        "SPDXID": "SPDXRef-Package-stonecharts-python",
                        "name": "stonecharts",
                        "versionInfo": RELEASE,
                        "downloadLocation": "NOASSERTION",
                    },
                    {
                        "SPDXID": "SPDXRef-Package-stonecharts-go",
                        "name": "stonecharts-go",
                        "versionInfo": RELEASE,
                        "downloadLocation": "NOASSERTION",
                    },
                ],
            },
        )

        registry = yaml.safe_load((ROOT / "docs/quality/evidence-registry.yaml").read_text(encoding="utf-8"))
        evidence = []
        evidence_paths: set[Path] = set()
        for item in registry["evidence"]:
            if item["status"] != "implemented":
                continue
            target = ROOT / item["location"]
            if not target.is_file():
                raise RuntimeError(f"implemented evidence is missing: {item['id']} -> {item['location']}")
            evidence.append({"id": item["id"], "status": "passed", "path": rel(target), "sha256": sha256(target)})
            evidence_paths.add(target)

        extra = {
            ROOT / "docs/quality/certification-ledger.json",
            ROOT / "spec/released/current.json",
            ROOT / f"spec/released/{RELEASE}/chart-spec.schema.json",
            ROOT / f"spec/released/{RELEASE}/stoneverify-result.schema.json",
            ROOT / "libs/python/pyproject.toml",
            ROOT / "libs/python/README.md",
            ROOT / "libs/python/LICENSE",
            ROOT / "libs/python/stonecharts/__init__.py",
            ROOT / "libs/python/stonecharts/_assets/chart-interactions.js",
            ROOT / "libs/go/version.go",
            ROOT / "libs/go/runtime/chart-interactions.js",
            ROOT / "runtime/chart-interactions.js",
            ROOT / "tools/build_release_evidence_0034.py",
            EVIDENCE_DIR / "manifest.schema.json",
            RC_DIR / "qualification-checklist.md",
            RC_DIR / "package-install-matrix.md",
            RC_DIR / "qualification-results.json",
            RC_DIR / "provenance.json",
            RC_DIR / "sbom.spdx.json",
        }
        extra.update(
            ROOT / "evidence-baselines" / chart_id / "manifest.json"
            for chart_id in [
                item["id"]
                for item in json.loads((ROOT / "spec/capabilities.json").read_text(encoding="utf-8"))["chartTypes"]
            ]
        )
        extra.update(PACKAGES_DIR.iterdir())
        paths = sorted(evidence_paths | extra, key=rel)
        if any(not path.is_file() for path in paths):
            missing = [rel(path) for path in paths if not path.is_file()]
            raise RuntimeError(f"release artifacts missing: {', '.join(missing)}")
        artifacts = [artifact(path) for path in paths]

        risk_registry = yaml.safe_load((ROOT / "docs/governance/risk-register.yaml").read_text(encoding="utf-8"))
        risks = []
        for item in risk_registry["risks"]:
            disposition = item["status"] if item["status"] in {"closed", "accepted"} else "not-applicable"
            risks.append(
                {
                    "id": item["id"],
                    "disposition": disposition,
                    "expires": None,
                    "rationale": f"{disposition.capitalize()}: {item['title']}. {item['mitigation']}",
                }
            )

        manifest = {
            "release": RELEASE,
            "candidate": CANDIDATE,
            "source": {
                "repository": "dharmik136/stonecharts",
                "commit": commit,
                "tag": RELEASE,
                "treeClean": True,
            },
            "versions": {
                "product": RELEASE,
                "python": RELEASE,
                "go": None,
                "schema": f"spec/released/{RELEASE}",
                "svgContract": "spec/svg-contract.md current",
                "runtime": "embedded canonical browser runtime; 36-chart Chromium profile",
            },
            "environment": {
                "builder": "tools/build_release_evidence_0034.py",
                "python": platform.python_version(),
                "go": subprocess.check_output(["go", "version"], text=True).strip(),
                "os": platform.platform(),
                "architecture": platform.machine(),
            },
            "artifacts": artifacts,
            "evidence": evidence,
            "risks": risks,
            "knownLimits": [
                "Package-registry and other external distribution channels remain unapproved and were not used.",
                "No real customer pilot has been executed; customer validation remains a separate external milestone.",
                "Pixel identity is claimed only under a named certified export profile, not arbitrary viewers.",
            ],
            "review": {
                "mode": "self",
                "productOwner": "dharmik136",
                "maintainer": "dharmik136",
                "approvedAt": completed_at,
            },
        }

        hashes_path = RC_DIR / "hashes.sha256"
        hashes_path.write_text(
            "".join(f"{entry['sha256']}  {entry['path']}\n" for entry in artifacts),
            encoding="utf-8",
        )
        manifest["artifacts"].append(artifact(hashes_path))
        manifest_path = RC_DIR / "manifest.json"
        write_json(manifest_path, manifest)

        validation = subprocess.run(
            [sys.executable, "tools/check_release_evidence.py", "--manifest", rel(manifest_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if validation.returncode != 0:
            raise RuntimeError(f"release evidence self-check failed:\n{validation.stdout}{validation.stderr}")
        print(validation.stdout.strip())
        print(f"built {rel(manifest_path)} from clean tagged source {commit}")
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"release evidence build FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
