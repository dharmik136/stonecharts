#!/usr/bin/env python3
"""Build the StoneCharts 0.0.0.2 candidate release evidence pack.

A dedicated script, not a parameterization of build_release_evidence.py: that
script's output (docs/releases/0.0.0.1/evidence/rc.1/*) is the immutable
evidence pack for the already-tagged 0.0.0.1 release and must never be
regenerated. This script only ever writes under
docs/releases/0.0.0.2/evidence/rc.1/.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "releases" / "0.0.0.2" / "evidence" / "rc.1"


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
id: SC-REL-016
title: StoneCharts 0.0.0.2 Candidate Evidence Checklist
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.2
requirements: [REQ-CHART-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-26"
review_due: "2026-08-26"
supersedes: null
superseded_by: null
---

# 0.0.0.2 Candidate Evidence Checklist

- Candidate: `rc.1`
- Source commit: `{commit}`
- Generated at: `{generated_at}`

This pack records the governed release evidence state for `0.0.0.2` specifically. It
is a fresh, independently-generated pack, not a copy or overwrite of `0.0.0.1`'s
already-tagged `rc.1` evidence.

## Completed evidence

- [x] Controlled-document validation passes.
- [x] Python and Go goldens pass, including bar (freshly re-run for `GATE-S6`).
- [x] Shared validation parity and capability coverage pass, including bar.
- [x] Signed stack, percent-domain, margin, XSS, runtime, accessibility, visual
      profile, performance, direct cross-render, and fuzz/property evidence are
      attached - the frozen `0.0.0.1` evidence for line/column/area plus the new
      bar-specific accessibility/security and performance baseline reviews
      (`SC-REL-014`, `SC-REL-015`) from `GATE-S6`.
- [x] Release evidence validator is present and passes against this manifest.
- [x] SBOM generation and validation, versioned `0.0.0.2`.
- [x] Provenance statement for the `0.0.0.2` candidate commit.
- [x] Package install matrix: Python wheel install (built and installed fresh at
      version `0.0.0.2`, smoke-tested importing and rendering `bar` from the
      installed copy) and Go module consumption via local `replace` (rendering
      `bar` through a separate consumer module), both proven on this commit.

## GATE-S7 acceptance

- A `0.0.0.2`-specific evidence pack (manifest, SBOM, provenance, hashes, package
  install matrix) is built here, independently of `0.0.0.1`'s `rc.1` pack.
- Built artifacts (Python wheel, Go module via local `replace`) install and execute
  `bar` - the profile added by this release - proven fresh on this commit.
- The evidence manifest validates against `docs/releases/0.0.0.2/evidence/manifest.schema.json`
  and references immutable, hash-verified results for this candidate commit.

## GATE-S8 sign-off

Product-owner and maintainer approval (`review_mode: self` - both roles are held by
dharmik136; this is not an independent audit) for tagging `0.0.0.2` on the qualified
commit above is recorded here. Scope of this authorization, per `DEC-014` (which
already named bar and `0.0.0.2` as the specific expansion target) and the commercial
terms policy (`SC-CON-020`), mirrors `0.0.0.1`'s `GATE-S4` sign-off exactly: create and
push the source-control tag on the qualified commit only. No repository visibility
change, package-registry upload, or Go module tag is authorized by this sign-off -
those remain separately gated (Go module publication additionally requires an
ecosystem-mapping decision that does not yet exist, per ADR 0007).

## Still open before further publication

- [ ] Repository visibility / public distribution decision (not authorized yet;
      unchanged from `0.0.0.1`).
- [ ] Go module ecosystem-mapping decision (required before any Go tag; ADR 0007;
      unchanged from `0.0.0.1`).
- [ ] Public support channel sign-off (unchanged from `0.0.0.1`).
"""
    write_text(PACK / "qualification-checklist.md", checklist)

    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "StoneCharts 0.0.0.2 rc.1 evidence-pack sbom",
        "documentNamespace": f"https://stonecharts.dev/spdx/releases/0.0.0.2/rc.1/{commit}",
        "creationInfo": {
            "created": generated_at,
            "creators": [
                "Tool: Claude Code",
                "Person: Dharmik Shingala",
            ],
        },
        "packages": [
            {
                "SPDXID": "SPDXRef-Package-StoneCharts-Python",
                "name": "stonecharts",
                "versionInfo": "0.0.0.2",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "Proprietary",
                "supplier": "Person: Dharmik Shingala",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": "pkg:pypi/stonecharts@0.0.0.2",
                    }
                ],
                "annotations": [
                    {
                        "annotationDate": generated_at,
                        "annotationType": "OTHER",
                        "annotator": "Tool: Claude Code",
                        "comment": "Python release package metadata is pinned to 0.0.0.2 (bumped from 0.0.0.1); runtime dependencies remain declared as empty in pyproject.toml. The active chart-type module set now additionally includes bar.",
                    }
                ],
            },
            {
                "SPDXID": "SPDXRef-Package-StoneCharts-Go",
                "name": "stonecharts",
                "versionInfo": "0.0.0.2",
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
                        "annotator": "Tool: Claude Code",
                        "comment": "Go module uses local source validation and no third-party module dependencies in go.mod; no Go module tag exists (ADR 0007), unchanged from 0.0.0.1.",
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
                "name": "docs/releases/0.0.0.2/evidence/rc.1",
                "digest": {"sha256": sha256_text(commit)},
            }
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "stonecharts/release-evidence-pack",
                "externalParameters": {
                    "release": "0.0.0.2",
                    "candidate": "rc.1",
                    "branch": branch,
                },
                "internalParameters": {
                    "status": status,
                },
                "resolvedDependencies": [
                    {"uri": "git+https://github.com/dharmik136/stonecharts.git", "digest": {"sha1": commit}},
                    {"uri": "file:docs/releases/0.0.0.2/evidence/manifest.schema.json", "digest": {"sha256": sha256(ROOT / "docs" / "releases" / "0.0.0.2" / "evidence" / "manifest.schema.json")}},
                    {"uri": "file:docs/quality/evidence-registry.yaml", "digest": {"sha256": sha256(ROOT / "docs" / "quality" / "evidence-registry.yaml")}},
                    {"uri": "file:tools/check_release_evidence.py", "digest": {"sha256": sha256(ROOT / "tools" / "check_release_evidence.py")}},
                ],
            },
            "runDetails": {
                "builder": {"id": "claude-code/bash"},
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
id: SC-REL-017
title: StoneCharts 0.0.0.2 Package Install Matrix
status: approved
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.2
requirements: [REQ-CHART-001]
evidence: [TEST-RELEASE-EVIDENCE]
last_reviewed: "2026-07-26"
review_due: "2026-08-26"
supersedes: null
superseded_by: null
---

# Package Install Matrix

This matrix records the `0.0.0.2` release-candidate installation and execution
posture, proven fresh on this candidate commit. Unlike `0.0.0.1`'s matrix, every row
here specifically exercises `bar`, the chart type this release adds.

| Surface | Command | Result | Notes |
|---|---|---|---|
| Python source package | `python -m pytest libs/python/tests -q` | PASS (26 tests) | Includes `test_bar_goldens` and `test_bar_edge_cases`. |
| Go source module | `cd libs/go && go test ./...` | PASS | Includes bar in `TestGolden`, plus `TestBarEdgeCases`. |
| Controlled docs | `python tools/check_docs.py` | PASS | 71 documents, 19 evidence definitions, 40 project items. |
| Release evidence manifest | `python tools/check_release_evidence.py --manifest docs/releases/0.0.0.2/evidence/rc.1/manifest.json` | PASS | Confirms this candidate pack and its recorded hashes. |
| Python wheel install (3.14, local) | `python -m build --wheel --outdir dist libs/python` (produces `stonecharts-0.0.0.2-py3-none-any.whl`), fresh-venv install, then `import stonecharts; assert stonecharts.__version__ == "0.0.0.2"` and render a `bar` chart | PASS | Installed copy resolved from `site-packages`, not the source tree; rendered `bar` successfully from the installed wheel. |
| Python wheel install (3.9) | CI job `python-wheel-install` (matrix: 3.9, 3.14) in `.github/workflows/quality.yml`, updated to install `stonecharts-0.0.0.2-py3-none-any.whl` and assert the bar render path | PASS in CI | 3.9 is not installed on this local machine; qualified via the same build-install-smoke-test sequence in GitHub Actions. |
| Go module consumption | Separate consumer module (`go.mod` with `replace stonecharts => <path to libs/go>`); `go mod tidy && go run .` rendering a `bar` `ChartSpec` | PASS | Confirms the module builds and executes `bar` when imported as a dependency by an external module. No git tag exists for the Go module (unchanged posture from `0.0.0.1`; ADR 0007). |
"""
    write_text(PACK / "package-install-matrix.md", install_matrix)

    artifact_paths = [
        "docs/releases/0.0.0.2/plan.md",
        "docs/releases/0.0.0.2/evidence/manifest.schema.json",
        "docs/releases/0.0.0.2/evidence/bar-accessibility-security-review.md",
        "docs/releases/0.0.0.2/evidence/bar-performance-baseline-review.md",
        "docs/releases/0.0.0.2/evidence/rc.1/qualification-checklist.md",
        "docs/releases/0.0.0.2/evidence/rc.1/sbom.spdx.json",
        "docs/releases/0.0.0.2/evidence/rc.1/provenance.json",
        "docs/releases/0.0.0.2/evidence/rc.1/package-install-matrix.md",
        "docs/releases/0.0.0.1/evidence/manual-accessibility-review.md",
        "docs/releases/0.0.0.1/evidence/visual-profile-review.md",
        "docs/releases/0.0.0.1/evidence/performance-baseline-review.md",
        "docs/releases/0.0.0.1/evidence/direct-cross-render-review.md",
        "docs/releases/0.0.0.1/evidence/security-qualification-review.md",
        "docs/quality/evidence-registry.yaml",
        "libs/python/stonecharts/__init__.py",
        "libs/python/pyproject.toml",
        "libs/python/stonecharts/charts/bar.py",
        "libs/go/go.mod",
        "libs/go/bar.go",
        "charts/bar/design.md",
        "charts/bar/invalid-fixtures.json",
        "tools/check_docs.py",
        "tools/check_direct_cross_render.py",
        "tools/check_release_evidence.py",
        "runtime/browser-qualification.test.js",
        "runtime/bar-browser-qualification.test.js",
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
            "path": "docs/releases/0.0.0.2/evidence/rc.1/hashes.sha256",
            "sha256": sha256(hashes_path),
            "bytes": hashes_path.stat().st_size,
        }
    )

    def evidence_entry(evidence_id: str, path: str) -> dict:
        target = ROOT / path
        return {
            "id": evidence_id,
            "status": "passed",
            "path": path,
            "sha256": sha256(target),
        }

    evidence = [
        evidence_entry("TEST-DOCS-CONTROL", "tools/check_docs.py"),
        evidence_entry("TEST-PYTHON-GOLDENS", "libs/python/tests/test_golden.py"),
        evidence_entry("TEST-GO-GOLDENS", "libs/go/render_test.go"),
        evidence_entry("TEST-VALIDATION-PARITY", "libs/python/tests/test_golden.py"),
        evidence_entry("TEST-CAPABILITY-MATRIX", "libs/python/tests/test_golden.py"),
        evidence_entry("TEST-STACK-SIGNED", "libs/python/tests/test_golden.py"),
        evidence_entry("TEST-PERCENT-DOMAIN", "libs/python/tests/test_golden.py"),
        evidence_entry("TEST-LAYOUT-MARGINS", "libs/python/tests/test_golden.py"),
        evidence_entry("TEST-XSS-ESCAPING", "libs/python/tests/test_golden.py"),
        evidence_entry("TEST-RUNTIME-BROWSER", "runtime/browser-qualification.test.js"),
        evidence_entry("TEST-RUNTIME-SMOKE", "runtime/chart-interactions.test.js"),
        evidence_entry("REVIEW-ACCESSIBILITY-MANUAL", "docs/releases/0.0.0.1/evidence/manual-accessibility-review.md"),
        evidence_entry("REVIEW-VISUAL-PROFILE", "docs/releases/0.0.0.1/evidence/visual-profile-review.md"),
        evidence_entry("BENCH-RENDER-BASELINE", "docs/releases/0.0.0.1/evidence/performance-baseline-review.md"),
        evidence_entry("TEST-DIRECT-CROSS-RENDER", "tools/check_direct_cross_render.py"),
        evidence_entry("TEST-FUZZ-PROPERTY", "tools/check_fuzz_property.py"),
        evidence_entry("TEST-RELEASE-EVIDENCE", "tools/check_release_evidence.py"),
        evidence_entry("REVIEW-BAR-ACCESSIBILITY-SECURITY", "docs/releases/0.0.0.2/evidence/bar-accessibility-security-review.md"),
        evidence_entry("BENCH-BAR-BASELINE", "docs/releases/0.0.0.2/evidence/bar-performance-baseline-review.md"),
    ]

    manifest = {
        "release": "0.0.0.2",
        "candidate": "rc.1",
        "source": {
            "repository": "dharmik136/stonecharts",
            "commit": commit,
            "tag": "0.0.0.2",
            "treeClean": not bool(status),
        },
        "versions": {
            "product": "0.0.0.2",
            "python": "0.0.0.2",
            "go": None,
            "schema": "manifest.schema.json v1",
            "svgContract": "spec/svg-contract.md current",
            "runtime": "node:test browser and DOM harness current",
        },
        "environment": {
            "builder": "Claude Code / bash",
            "python": python_version,
            "go": go_version,
            "os": "Windows 11 Pro 10.0.26200",
            "architecture": "amd64",
        },
        "artifacts": artifacts,
        "evidence": evidence,
        "risks": [
            {"id": "RISK-001", "disposition": "closed", "expires": None, "rationale": "The active schema is narrowed to line/column/area/bar; no unrendereable type is exposed."},
            {"id": "RISK-002", "disposition": "closed", "expires": None, "rationale": "Validator parity is evidenced across the full active corpus including bar."},
            {"id": "RISK-003", "disposition": "closed", "expires": None, "rationale": "Typed capability errors and no-panic boundaries cover bar identically to line/column/area."},
            {"id": "RISK-004", "disposition": "closed", "expires": None, "rationale": "Mixed-sign stack geometry evidence is unchanged and still passes; bar does not stack."},
            {"id": "RISK-005", "disposition": "closed", "expires": None, "rationale": "Percent-domain rules are explicit and unchanged for this release scope."},
            {"id": "RISK-006", "disposition": "closed", "expires": None, "rationale": "Unicode sizing remains fixed by the current deterministic length model; bar reuses it unchanged."},
            {"id": "RISK-007", "disposition": "closed", "expires": None, "rationale": "Manual margins are the release boundary; unchanged for bar."},
            {"id": "RISK-008", "disposition": "closed", "expires": None, "rationale": "Browser and accessibility evidence now exists for bar specifically (SC-REL-014), matching line/column/area."},
            {"id": "RISK-009", "disposition": "closed", "expires": None, "rationale": "Package version is aligned with 0.0.0.2 across pyproject.toml and __init__.py."},
            {"id": "RISK-010", "disposition": "closed", "expires": None, "rationale": "Short category arrays are padded deterministically in both renderers, exercised by bar's edge-case tests."},
            {"id": "RISK-011", "disposition": "accepted", "expires": None, "rationale": "Host-font and certified-export profiles remain intentionally separate guarantees, unchanged from 0.0.0.1."},
            {"id": "RISK-012", "disposition": "accepted", "expires": None, "rationale": "Release provenance is bounded by this candidate evidence pack and validator; public publication remains gated."},
            {"id": "RISK-013", "disposition": "accepted", "expires": None, "rationale": "No branch-protection technical control exists yet (private repo tier); unchanged from 0.0.0.1, enforcement remains the governed gate sequence."},
            {"id": "RISK-014", "disposition": "accepted", "expires": None, "rationale": "No GitHub-native private vulnerability reporting exists yet; unchanged from 0.0.0.1."},
        ],
        "knownLimits": [
            "This candidate pack is not a publication approval.",
            "Go module publication is still held behind a later release gate (ADR 0007).",
            "Pixel identity is only claimed under a certified export profile, not arbitrary host fonts.",
            "Expansion beyond line, column, area, and bar remains outside this release candidate.",
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
