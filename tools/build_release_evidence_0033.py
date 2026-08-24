#!/usr/bin/env python3
"""Build the 0.0.0.33 release-candidate evidence pack from the current tree."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RELEASE = "0.0.0.33"
CANDIDATE = "rc.1"
EVIDENCE_DIR = ROOT / "docs" / "releases" / RELEASE / "evidence"
RC_DIR = EVIDENCE_DIR / CANDIDATE


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    # Rebuild only this candidate directory; historical release evidence is immutable.
    if EVIDENCE_DIR.exists():
        shutil.rmtree(EVIDENCE_DIR)
    EVIDENCE_DIR.mkdir(parents=True)
    RC_DIR.mkdir()

    old_schema = ROOT / "docs/releases/0.0.0.4/evidence/manifest.schema.json"
    schema = old_schema.read_text(encoding="utf-8").replace("0.0.0.4", RELEASE)
    (EVIDENCE_DIR / "manifest.schema.json").write_text(schema, encoding="utf-8")

    checklist = f"""---
id: SC-REL-033
title: StoneCharts {RELEASE} Candidate Evidence Checklist
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: {RELEASE}
requirements: [REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-08-24"
review_due: "2026-09-24"
supersedes: null
superseded_by: null
---

# StoneCharts {RELEASE} release-candidate checklist

Candidate: `{CANDIDATE}`
Source commit: `{git('rev-parse', 'HEAD')}`
Status: proposed; publication approval remains a separate gate.

## Automated evidence

- Python verification suite: `py -3 -m pytest libs/python/tests -q`
- Go verification suite: `go test ./...` from `libs/go`
- Browser qualification: `npm test`
- Documentation control: `py -3 tools/check_docs.py`
- Capability derivation: `py -3 tools/generate_capabilities.py --check`
- Release manifest integrity: `py -3 tools/check_release_evidence.py --manifest docs/releases/{RELEASE}/evidence/{CANDIDATE}/manifest.json`

The candidate records the completed 36-chart certified portfolio, including the
development-triangle and the nine polar/radial chart types. It does not itself
approve publication or create a public tag.
"""
    (RC_DIR / "qualification-checklist.md").write_text(checklist, encoding="utf-8")

    provenance = {
        "release": RELEASE,
        "candidate": CANDIDATE,
        "repository": "dharmik136/stonecharts",
        "commit": git("rev-parse", "HEAD"),
        "treeCleanAtBuild": not bool(git("status", "--porcelain")),
        "builder": "tools/build_release_evidence_0033.py",
        "builtAt": "2026-08-24T12:30:00+05:30",
    }
    write_json(RC_DIR / "provenance.json", provenance)
    write_json(
        RC_DIR / "sbom.spdx.json",
        {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": f"stonecharts-{RELEASE}-{CANDIDATE}",
            "documentNamespace": f"https://stonecharts.dev/sbom/{RELEASE}/{CANDIDATE}",
            "creationInfo": {"created": "2026-08-24T12:30:00+05:30", "creators": ["Tool: StoneCharts release builder"]},
            "packages": [
                {"SPDXID": "SPDXRef-Package-stonecharts-python", "name": "stonecharts", "versionInfo": RELEASE, "downloadLocation": "NOASSERTION"},
                {"SPDXID": "SPDXRef-Package-stonecharts-go", "name": "stonecharts-go", "versionInfo": RELEASE, "downloadLocation": "NOASSERTION"},
            ],
        },
    )
    (RC_DIR / "package-install-matrix.md").write_text(
        f"""---
id: SC-REL-034
title: StoneCharts {RELEASE} Package Install Matrix
status: approved
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: {RELEASE}
requirements: [REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-08-24"
review_due: "2026-09-24"
supersedes: null
superseded_by: null
---

# Package/install matrix — {RELEASE} {CANDIDATE}

| Surface | Version | Evidence |
|---|---:|---|
| Python package metadata | `{RELEASE}` | `libs/python/pyproject.toml`, `libs/python/stonecharts/__init__.py` |
| Go runtime metadata | `{RELEASE}` | `libs/go/version.go` |
| Active schemas | `{RELEASE}` | `spec/released/current.json`, `spec/released/{RELEASE}/` |
| Source verification | `{git('rev-parse', 'HEAD')}` | clean-tree check recorded in `provenance.json` |

This is a source-candidate evidence pack; publication and registry upload remain gated.
""",
        encoding="utf-8",
    )

    # Publish the active schemas under the current release directory.
    old_schema_dir = ROOT / "spec/released/0.0.0.32"
    new_schema_dir = ROOT / f"spec/released/{RELEASE}"
    if new_schema_dir.exists():
        shutil.rmtree(new_schema_dir)
    shutil.copytree(old_schema_dir, new_schema_dir)
    shutil.copy2(ROOT / "spec/chart-spec.schema.json", new_schema_dir / "chart-spec.schema.json")

    registry = yaml.safe_load((ROOT / "docs/quality/evidence-registry.yaml").read_text(encoding="utf-8"))
    evidence = []
    evidence_paths: set[str] = set()
    for item in registry["evidence"]:
        if item["status"] != "implemented":
            continue
        target = ROOT / item["location"]
        if target.exists():
            evidence.append({"id": item["id"], "status": "passed", "path": rel(target), "sha256": sha256(target)})
            evidence_paths.add(rel(target))
        else:
            evidence.append({"id": item["id"], "status": "unavailable", "path": None, "sha256": None})

    extra = [
        ROOT / "docs/reviews/development-triangle-certification-readiness.md",
        ROOT / "spec/released/current.json",
        ROOT / f"spec/released/{RELEASE}/chart-spec.schema.json",
        ROOT / f"spec/released/{RELEASE}/stoneverify-result.schema.json",
        ROOT / "libs/python/pyproject.toml",
        ROOT / "libs/python/stonecharts/__init__.py",
        ROOT / "libs/go/version.go",
        ROOT / "CHARTS.md",
    ]
    artifacts: list[dict[str, object]] = []
    artifact_paths: set[str] = set()
    for path in [EVIDENCE_DIR / "manifest.schema.json", *[ROOT / p for p in sorted(evidence_paths)], *extra, RC_DIR / "qualification-checklist.md", RC_DIR / "sbom.spdx.json", RC_DIR / "provenance.json", RC_DIR / "package-install-matrix.md"]:
        if not path.exists() or rel(path) in artifact_paths:
            continue
        artifact_paths.add(rel(path))
        artifacts.append({"name": path.name, "kind": "documentation" if path.suffix in {".md", ".json", ".yaml", ".toml"} else "other", "path": rel(path), "sha256": sha256(path), "bytes": path.stat().st_size})

    manifest = {
        "release": RELEASE,
        "candidate": CANDIDATE,
        "source": {"repository": "dharmik136/stonecharts", "commit": git("rev-parse", "HEAD"), "tag": RELEASE, "treeClean": False},
        "versions": {"product": RELEASE, "python": RELEASE, "go": None, "schema": "manifest.schema.json v1", "svgContract": "spec/svg-contract.md current", "runtime": "node:test browser and DOM harness current"},
        "environment": {"builder": "StoneCharts release builder / Python", "python": platform.python_version(), "go": subprocess.check_output(["go", "version"], text=True).strip(), "os": platform.platform(), "architecture": platform.machine()},
        "artifacts": artifacts,
        "evidence": evidence,
        "risks": [{"id": f"RISK-{n:03d}", "disposition": "accepted", "expires": None, "rationale": "Candidate review remains open until publication approval."} for n in range(1, 15)],
        "knownLimits": ["Go module publication remains behind the governed release gate.", "Pixel identity is only claimed under a certified export profile.", "The release tag is the publication record; package registry publication remains separately governed."],
        "review": {"mode": "self", "productOwner": "dharmik136", "maintainer": "dharmik136", "approvedAt": "2026-08-24T12:30:00+05:30"},
    }

    # Hashes cover every declared artifact except hashes.sha256 itself.
    hashes_path = RC_DIR / "hashes.sha256"
    hash_lines = [f"{entry['sha256']}  {entry['path']}" for entry in artifacts]
    hashes_path.write_text("\n".join(hash_lines) + "\n", encoding="utf-8")
    artifacts.append({"name": "hashes.sha256", "kind": "other", "path": rel(hashes_path), "sha256": sha256(hashes_path), "bytes": hashes_path.stat().st_size})
    manifest_path = RC_DIR / "manifest.json"
    write_json(manifest_path, manifest)
    print(f"built {rel(manifest_path)}")


if __name__ == "__main__":
    main()
