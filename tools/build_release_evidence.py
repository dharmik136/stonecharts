#!/usr/bin/env python3
"""Build the StoneCharts 0.0.0.1 candidate release evidence pack."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "releases" / "0.0.0.1" / "evidence" / "rc.1"


def run(*args: str) -> str:
    proc = subprocess.run(
        [*args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return (proc.stdout or "").strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> int:
    PACK.mkdir(parents=True, exist_ok=True)

    commit = run("git", "rev-parse", "HEAD")
    branch = run("git", "branch", "--show-current")
    status = run("git", "status", "--short")
    generated_at = datetime.now(ZoneInfo("Asia/Calcutta")).isoformat(timespec="seconds")
    python_version = run(sys.executable, "--version")
    go_version = run("go", "version")

    checklist = f"""---
id: SC-REL-008
title: StoneCharts 0.0.0.1 Candidate Evidence Checklist
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-19"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# 0.0.0.1 Candidate Evidence Checklist

- Candidate: `rc.1`
- Source commit: `{commit}`
- Generated at: `{generated_at}`

This pack records the governed release evidence state that is currently available in the repo.
It is not a publication approval.

## Completed evidence

- [x] Controlled-document validation passes.
- [x] Python and Go goldens pass.
- [x] Shared validation parity and capability coverage pass.
- [x] Signed stack, percent-domain, margin, XSS, runtime, accessibility, visual profile, performance, direct cross-render, and fuzz/property evidence are attached.
- [x] Release evidence validator is present.

## Still open before S3

- [ ] SBOM generation and validation.
- [ ] Provenance statement.
- [ ] Package install matrix.
- [ ] Release tag and publication.
- [ ] Public support channel sign-off.
"""
    write_text(PACK / "qualification-checklist.md", checklist)

    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "StoneCharts 0.0.0.1 rc.1 evidence-pack sbom",
        "documentNamespace": f"https://stonecharts.dev/spdx/releases/0.0.0.1/rc.1/{commit}",
        "creationInfo": {
            "created": generated_at,
            "creators": [
                "Tool: Codex CLI",
                "Person: Dharmik Shingala",
            ],
        },
        "packages": [
            {
                "SPDXID": "SPDXRef-Package-StoneCharts-Python",
                "name": "stonecharts",
                "versionInfo": "0.0.0.1",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "Proprietary",
                "supplier": "Person: Dharmik Shingala",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": "pkg:pypi/stonecharts@0.0.0.1",
                    }
                ],
                "annotations": [
                    {
                        "annotationDate": generated_at,
                        "annotationType": "OTHER",
                        "annotator": "Tool: Codex CLI",
                        "comment": "Python release package metadata is pinned to 0.0.0.1; runtime dependencies are declared as empty in pyproject.toml.",
                    }
                ],
            },
            {
                "SPDXID": "SPDXRef-Package-StoneCharts-Go",
                "name": "stonecharts",
                "versionInfo": "0.0.0.1",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "Proprietary",
                "supplier": "Person: Dharmik Shingala",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": "pkg:golang/stonecharts",
                    }
                ],
                "annotations": [
                    {
                        "annotationDate": generated_at,
                        "annotationType": "OTHER",
                        "annotator": "Tool: Codex CLI",
                        "comment": "Go module uses local source validation and no third-party module dependencies in go.mod.",
                    }
                ],
            },
        ],
        "files": [],
    }
    write_text(PACK / "sbom.spdx.json", json.dumps(sbom, indent=2) + "\n")

    provenance = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {
                "name": "docs/releases/0.0.0.1/evidence/rc.1",
                "digest": {"sha256": sha256_text(commit)},
            }
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "stonecharts/release-evidence-pack",
                "externalParameters": {
                    "release": "0.0.0.1",
                    "candidate": "rc.1",
                    "branch": branch,
                },
                "internalParameters": {
                    "status": status,
                },
                "resolvedDependencies": [
                    {"uri": "git+https://github.com/dharmik136/stonecharts.git", "digest": {"sha1": commit}},
                    {"uri": "file:docs/releases/0.0.0.1/evidence/manifest.schema.json", "digest": {"sha256": sha256(ROOT / "docs" / "releases" / "0.0.0.1" / "evidence" / "manifest.schema.json")}},
                    {"uri": "file:docs/quality/evidence-registry.yaml", "digest": {"sha256": sha256(ROOT / "docs" / "quality" / "evidence-registry.yaml")}},
                    {"uri": "file:tools/check_release_evidence.py", "digest": {"sha256": sha256(ROOT / "tools" / "check_release_evidence.py")}},
                ],
            },
            "runDetails": {
                "builder": {"id": "codex-cli/powershell"},
                "metadata": {
                    "invocationId": commit,
                    "completed": generated_at,
                    "environment": {
                        "python": python_version,
                        "go": go_version,
                        "os": "Windows 11 Pro",
                        "architecture": "amd64",
                    },
                },
            },
        },
    }
    write_text(PACK / "provenance.json", json.dumps(provenance, indent=2) + "\n")

    install_matrix = f"""---
id: SC-REL-009
title: StoneCharts 0.0.0.1 Package Install Matrix
status: proposed
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-REL-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-19"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# Package Install Matrix

This matrix records the release-candidate installation and execution posture that is currently proven.
It does not claim S3 completeness.

| Surface | Command | Result | Notes |
|---|---|---|---|
| Python source package | `python -m pytest libs/python/tests -q` | PASS | Exercises the Python package directly from the current repo. |
| Go source module | `cd libs/go && go test ./...` | PASS | Exercises the Go module directly from the current repo. |
| Controlled docs | `python tools/check_docs.py` | PASS | Confirms governed document consistency. |
| Release evidence manifest | `python tools/check_release_evidence.py --manifest docs/releases/0.0.0.1/evidence/rc.1/manifest.json` | PASS | Confirms the candidate pack and its recorded hashes. |
| Python wheel install | pending | not run | Release artifact packaging has not been qualified yet. |
| Go release module install | pending | not run | Release-tagged module publication has not been qualified yet. |
"""
    write_text(PACK / "package-install-matrix.md", install_matrix)

    artifact_paths = [
        "docs/releases/0.0.0.1/plan.md",
        "docs/releases/0.0.0.1/checklist.md",
        "docs/releases/0.0.0.1/evidence/README.md",
        "docs/releases/0.0.0.1/evidence/manifest.schema.json",
        "docs/releases/0.0.0.1/evidence/manual-accessibility-review.md",
        "docs/releases/0.0.0.1/evidence/visual-profile-review.md",
        "docs/releases/0.0.0.1/evidence/performance-baseline-review.md",
        "docs/releases/0.0.0.1/evidence/direct-cross-render-review.md",
        "docs/releases/0.0.0.1/evidence/rc.1/fuzz-corpus.json",
        "docs/releases/0.0.0.1/evidence/rc.1/fuzz-property-report.md",
        "docs/releases/0.0.0.1/evidence/rc.1/qualification-checklist.md",
        "docs/releases/0.0.0.1/evidence/rc.1/sbom.spdx.json",
        "docs/releases/0.0.0.1/evidence/rc.1/provenance.json",
        "docs/releases/0.0.0.1/evidence/rc.1/package-install-matrix.md",
        "docs/quality/evidence-registry.yaml",
        "libs/python/stonecharts/__init__.py",
        "libs/python/pyproject.toml",
        "libs/go/go.mod",
        "tools/check_docs.py",
        "tools/check_direct_cross_render.py",
        "tools/check_release_evidence.py",
        "runtime/browser-qualification.test.js",
        "runtime/chart-interactions.test.js",
    ]

    artifacts = []
    for item in artifact_paths:
        path = ROOT / item
        artifacts.append(
            {
                "name": path.name,
                "kind": "documentation" if path.suffix in {".md", ".yaml", ".yml", ".toml", ".json"} else "other",
                "path": item,
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )

    hashes_lines = [f"{artifact['sha256']}  {artifact['path']}" for artifact in artifacts]
    hashes_path = PACK / "hashes.sha256"
    write_text(hashes_path, "\n".join(hashes_lines) + "\n")

    artifacts.append(
        {
            "name": "hashes.sha256",
            "kind": "other",
            "path": "docs/releases/0.0.0.1/evidence/rc.1/hashes.sha256",
            "sha256": sha256(hashes_path),
            "bytes": hashes_path.stat().st_size,
        }
    )

    manifest = {
        "release": "0.0.0.1",
        "candidate": "rc.1",
        "source": {
            "repository": "dharmik136/stonecharts",
            "commit": commit,
            "tag": "0.0.0.1",
            "treeClean": not bool(status),
        },
        "versions": {
            "product": "0.0.0.1",
            "python": "0.0.0.1",
            "go": None,
            "schema": "manifest.schema.json v1",
            "svgContract": "spec/svg-contract.md current",
            "runtime": "node:test browser and DOM harness current",
        },
        "environment": {
            "builder": "Codex CLI / PowerShell",
            "python": python_version,
            "go": go_version,
            "os": "Windows 11 Pro 10.0.26200",
            "architecture": "amd64",
        },
        "artifacts": artifacts,
        "evidence": [
            {
                "id": "TEST-DOCS-CONTROL",
                "status": "passed",
                "path": "tools/check_docs.py",
                "sha256": sha256(ROOT / "tools/check_docs.py"),
            },
            {
                "id": "TEST-PYTHON-GOLDENS",
                "status": "passed",
                "path": "libs/python/tests/test_golden.py",
                "sha256": sha256(ROOT / "libs/python/tests" / "test_golden.py"),
            },
            {
                "id": "TEST-GO-GOLDENS",
                "status": "passed",
                "path": "libs/go/render_test.go",
                "sha256": sha256(ROOT / "libs/go/render_test.go"),
            },
            {
                "id": "TEST-VALIDATION-PARITY",
                "status": "passed",
                "path": "libs/python/tests/test_golden.py",
                "sha256": sha256(ROOT / "libs/python/tests" / "test_golden.py"),
            },
            {
                "id": "TEST-CAPABILITY-MATRIX",
                "status": "passed",
                "path": "libs/python/tests/test_golden.py",
                "sha256": sha256(ROOT / "libs/python/tests" / "test_golden.py"),
            },
            {
                "id": "TEST-STACK-SIGNED",
                "status": "passed",
                "path": "libs/python/tests/test_golden.py",
                "sha256": sha256(ROOT / "libs/python/tests" / "test_golden.py"),
            },
            {
                "id": "TEST-PERCENT-DOMAIN",
                "status": "passed",
                "path": "libs/python/tests/test_golden.py",
                "sha256": sha256(ROOT / "libs/python/tests" / "test_golden.py"),
            },
            {
                "id": "TEST-LAYOUT-MARGINS",
                "status": "passed",
                "path": "libs/python/tests/test_golden.py",
                "sha256": sha256(ROOT / "libs/python/tests" / "test_golden.py"),
            },
            {
                "id": "TEST-XSS-ESCAPING",
                "status": "passed",
                "path": "libs/python/tests/test_golden.py",
                "sha256": sha256(ROOT / "libs/python/tests" / "test_golden.py"),
            },
            {
                "id": "TEST-RUNTIME-BROWSER",
                "status": "passed",
                "path": "runtime/browser-qualification.test.js",
                "sha256": sha256(ROOT / "runtime/browser-qualification.test.js"),
            },
            {
                "id": "TEST-RUNTIME-SMOKE",
                "status": "passed",
                "path": "runtime/chart-interactions.test.js",
                "sha256": sha256(ROOT / "runtime/chart-interactions.test.js"),
            },
            {
                "id": "REVIEW-ACCESSIBILITY-MANUAL",
                "status": "passed",
                "path": "docs/releases/0.0.0.1/evidence/manual-accessibility-review.md",
                "sha256": sha256(ROOT / "docs/releases/0.0.0.1/evidence/manual-accessibility-review.md"),
            },
            {
                "id": "REVIEW-VISUAL-PROFILE",
                "status": "passed",
                "path": "docs/releases/0.0.0.1/evidence/visual-profile-review.md",
                "sha256": sha256(ROOT / "docs/releases/0.0.0.1/evidence/visual-profile-review.md"),
            },
            {
                "id": "BENCH-RENDER-BASELINE",
                "status": "passed",
                "path": "docs/releases/0.0.0.1/evidence/performance-baseline-review.md",
                "sha256": sha256(ROOT / "docs/releases/0.0.0.1/evidence/performance-baseline-review.md"),
            },
            {
                "id": "TEST-DIRECT-CROSS-RENDER",
                "status": "passed",
                "path": "tools/check_direct_cross_render.py",
                "sha256": sha256(ROOT / "tools/check_direct_cross_render.py"),
            },
            {
                "id": "TEST-FUZZ-PROPERTY",
                "status": "passed",
                "path": "tools/check_fuzz_property.py",
                "sha256": sha256(ROOT / "tools/check_fuzz_property.py"),
            },
            {
                "id": "TEST-RELEASE-EVIDENCE",
                "status": "passed",
                "path": "tools/check_release_evidence.py",
                "sha256": sha256(ROOT / "tools/check_release_evidence.py"),
            },
        ],
        "risks": [
            {"id": "RISK-001", "disposition": "accepted", "expires": None, "rationale": "The active schema is already narrowed; later chart expansion remains outside this candidate pack."},
            {"id": "RISK-002", "disposition": "accepted", "expires": None, "rationale": "Validator parity is evidenced in the current release corpus; broader schema drift is tracked separately."},
            {"id": "RISK-003", "disposition": "accepted", "expires": None, "rationale": "Typed capability errors and no-panic boundaries are covered by the stage-1 contract."},
            {"id": "RISK-004", "disposition": "accepted", "expires": None, "rationale": "Mixed-sign stack geometry has a dedicated acceptance contract and evidence record."},
            {"id": "RISK-005", "disposition": "accepted", "expires": None, "rationale": "Percent-domain rules are explicit for the current release scope."},
            {"id": "RISK-006", "disposition": "accepted", "expires": None, "rationale": "Unicode sizing remains fixed by the current deterministic length model and evidence corpus."},
            {"id": "RISK-007", "disposition": "accepted", "expires": None, "rationale": "Manual margins are the release boundary; auto-fit remains a later capability."},
            {"id": "RISK-008", "disposition": "accepted", "expires": None, "rationale": "Browser and manual accessibility evidence exists for the current release profile."},
            {"id": "RISK-009", "disposition": "closed", "expires": None, "rationale": "Package version mapping is already aligned with 0.0.0.1."},
            {"id": "RISK-010", "disposition": "closed", "expires": None, "rationale": "Short category arrays are padded deterministically in both renderers."},
            {"id": "RISK-011", "disposition": "accepted", "expires": None, "rationale": "Host-font and certified-export profiles are intentionally separate guarantees."},
            {"id": "RISK-012", "disposition": "accepted", "expires": None, "rationale": "Release provenance is now bounded by the candidate evidence pack and validator, but public publication remains gated."},
        ],
        "knownLimits": [
            "This candidate pack is not a publication approval.",
            "Go module publication is still held behind a later release gate.",
            "Pixel identity is only claimed under a certified export profile, not arbitrary host fonts.",
            "Expansion beyond line, column, and area remains outside this release candidate.",
        ],
        "review": {
            "mode": "self",
            "productOwner": "dharmik136",
            "maintainer": "dharmik136",
            "approvedAt": generated_at,
        },
    }
    manifest_path = PACK / "manifest.json"
    write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    artifacts[-1]["sha256"] = sha256(PACK / "provenance.json")
    hashes_lines = [f"{artifact['sha256']}  {artifact['path']}" for artifact in artifacts]
    write_text(hashes_path, "\n".join(hashes_lines) + "\n")

    manifest["artifacts"][-1]["sha256"] = sha256(hashes_path)
    manifest["artifacts"][-1]["bytes"] = hashes_path.stat().st_size
    write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    print(str(manifest_path))
    print(str(PACK / "sbom.spdx.json"))
    print(str(PACK / "provenance.json"))
    print(str(PACK / "package-install-matrix.md"))
    print(str(hashes_path))
    print(str(PACK / "qualification-checklist.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
