---
id: SC-REL-012
title: StoneCharts 0.0.0.1 Release Findings
status: approved
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-REL-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-26"
review_due: "2026-08-26"
supersedes: null
superseded_by: null
---

# 0.0.0.1 Release Findings

## Scope

This records the findings from actually qualifying and releasing 0.0.0.1 - Stage 0
through Stage 4 - and how they were incorporated, satisfying `GATE-S5`'s first
acceptance criterion ("release findings are reviewed and incorporated") before any
post-0.0.0.1 expansion work begins.

## Risk register: 12 of 14 risks closed

Every risk in `docs/governance/risk-register.yaml` linked to a now-`Done` requirement
was individually re-verified against real evidence (not just the requirement's `Done`
status) and closed: `RISK-001` through `RISK-012`. Two new risks were opened and
immediately `accepted` (not closed - they are real, ongoing, and not fully within this
project's control): `RISK-013` (no branch-protection gate; this repository's tier
doesn't support it) and `RISK-014` (no GitHub-native private vulnerability reporting;
same root cause). Both have a working procedural or documented fallback recorded in
their mitigation.

## Finding patterns

Five recurring patterns surfaced during qualification. Each is incorporated into
`docs/architecture/chart-admission-checklist.md` (`SC-ARCH-011`) so future expansion
work doesn't repeat them.

### 1. Scope claims drift independently across documents

The same scope fact ("is `bar` in 0.0.0.1?") was stated four different ways across
four separate documents - `positioning-and-scope.md`, `README.md`,
`backlog.yaml`'s `DEC-002` title, and the release plan's Objective line - three of
them stale, one (the decision register itself) correct. No single document was
deliberately wrong; each was edited independently over time and never cross-checked.
**Incorporated as:** checklist phase 9 requires updating every scope-stating document
in the same change, not just the "obvious" one.

### 2. "Evidence exists" is not the same as "evidence was re-verified"

`docs/quality/evidence-registry.yaml` marked several evidence types `implemented`
while the actual GitHub issue acceptance-criteria checkboxes for the corresponding
requirements were still unchecked - the tooling existed, but nobody had run it against
the current commit and recorded a pass. The cross-render sweep tool's `ACTIVE` corpus
silently excluded `area` even though `area` was in ratified scope, so `REQ-DET-001`
could not honestly have been called qualified until that gap was closed. **Incorporated
as:** every checklist phase requires re-running the actual check, not inferring status
from an adjacent field.

### 3. A benchmark or check can pass while testing the wrong thing

`libs/python/benchmark.py` and its Go equivalent ran cleanly and produced real
numbers, but measured a dimension (point-count x layout-style, fixed at 2 series)
that had nothing to do with the approved `Small`/`Business`/`Dense`/`Stress` workload
matrix in `benchmark-spec.md`. A passing, green check told a misleading story until the
harness itself was compared against its own governing spec. **Incorporated as:**
checklist phase 8 requires the benchmark update to be checked against the approved
workload matrix, not merely "a benchmark exists and runs."

### 4. Generator-tool templates drift from reality

`tools/build_release_evidence.py`'s hardcoded checklist template still listed SBOM
generation, provenance, and the install matrix as "still open" long after the same
script had been generating all three. Generated files inherit whatever the template
last said, so a stale template silently understates real progress every time it runs.
**Incorporated as:** checklist phase 10 requires regenerating evidence against the
final commit, and reviewing the generator's own template text, not just its output.

### 5. Platform/tier limitations are real risks, not embarrassments to hide

No branch protection, no native private vulnerability reporting - both are structural
limitations of this repository's current GitHub tier, not defects in the product.
Recording them plainly as `accepted` risks with a working fallback is more honest than
either ignoring them or blocking release on something outside the project's control.
**Incorporated as:** `RISK-013`/`RISK-014` above, and the same disclosure pattern is
expected for any future tier-driven gap.

## What this does not cover

This findings review does not itself decide an expansion order or next release
target - `GATE-S5`'s remaining two acceptance criteria are substantive product
decisions and are out of scope for this document.
