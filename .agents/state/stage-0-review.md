# Stage 0 Baseline Review Package

- Generated at: 2026-07-18 15:34:01 +0530
- Commit: ac916bdbc6c8f43bf2147856f7820528b52bf021
- Branch: main
- Working tree: dirty

## Working tree status

M .agents/state/stage-0-review.md
 M tools/build_stage0_review.py

## Verification

- `python tools/check_docs.py`: PASS

```
documentation control PASS: 42 documents, 15 requirements, 14 evidence definitions, 12 risks, 35 project items
```

- `python tools/check_github_project.py`: PASS

```
GitHub Project conformance PASS: 35 governed items, 8 statuses, 11 governed fields, 6 saved views
```

## Open decisions

- DEC-005: What compatibility promise begins at 0.0.0.1? -> Permit documented pre-release breaks now; after 0.0.0.1, require migration notes and a deprecation window for public spec/API/DOM changes (decide before S3 release candidate)
- DEC-008: What is the supported runtime and platform matrix? -> Pin explicit Python, Go, browser, OS, and exporter profiles from CI evidence rather than broad untested claims (decide before S2 qualification plan)
- DEC-009: What performance and artifact-size budgets block release? -> Establish measured budgets for 10, 100, 1,000, and stress-point profiles before optimizing implementation details (decide before S2 benchmark gate)
- DEC-010: What is the certified visual profile for 0.0.0.1? -> Guarantee semantic SVG under the host-font profile; treat embedded font plus pinned exporter as a separate certified profile (decide before S2 visual qualification)
- DEC-011: When and where are packages and source made public? -> Keep the repository and registries private until S3 evidence is complete; publish only channels with an explicit support policy (decide before S3 distribution plan)
- DEC-012: Is the StoneCharts name cleared for public commercial use? -> Complete repository, package-index, domain, and trademark due diligence before public announcement; technical adoption is not legal clearance (decide before Public branding or registration)
- DEC-013: What commercial license, contribution terms, and support model apply? -> Keep the current proprietary boundary until a written business model and contributor agreement are approved (decide before External access or contributions)

## Open risks

- RISK-001 (open): Released schema overstates renderer support -> Restrict the active schema to released types and add explicit renderer capability validation.
- RISK-002 (open): Schema and handwritten validators disagree -> Ratify one rule set, encode it in all three validators, and add shared accept-and-reject fixtures.
- RISK-003 (open): Accepted input can panic or throw during dispatch -> Make render entry points return canonical typed errors for every user-controlled failure.
- RISK-004 (open): Mixed-sign normal stacking has an invalid domain -> Use separate positive and negative accumulators in both the domain and mark transforms.
- RISK-005 (open): Percent stacking has ambiguous signed semantics -> Restrict 0.0.0.1 percent stacking to finite non-negative values and define all-zero categories explicitly.
- RISK-006 (open): Unicode legend geometry differs by language -> Define one Unicode length model and lock it with cross-language fixtures.
- RISK-007 (open): Fixed margins can clip real-world labels -> Add validated manual margins and publish the no-auto-fit 0.0.0.1 limitation.
- RISK-008 (open): Runtime interaction and accessibility gaps -> Ratify runtime semantics and add automated browser plus manual accessibility qualification.
- RISK-009 (open): Package version conflicts with planned release -> Adopt ecosystem-specific version mappings and verify every emitted package before tagging.
- RISK-010 (open): Short category arrays can break generated HTML -> Define category-length semantics, validate or pad deterministically, and add shared HTML tests.
- RISK-011 (mitigating): Byte identity may be misrepresented as pixel identity -> Publish separate canonical, embedded-font, and certified-export guarantee profiles.
- RISK-012 (open): Release provenance is not yet reproducible -> Build the 0.0.0.1 evidence pack and supply-chain workflow before public distribution.

## Stage 0 blockers

- WORK-S0-001 (Done): Review and approve the Stage 0 controlled foundation baseline -> depends on DEC-001, DEC-002, DEC-003, DEC-004, DEC-006, DEC-007, REQ-PROD-001
- GATE-S0 (Done): Pass Stage 0 product-foundation gate -> depends on DEC-001, DEC-002, DEC-003, DEC-004, DEC-006, DEC-007, WORK-S0-001, REQ-PROD-001

## Review note

Stage 0 is closed; the baseline has been reviewed and the governed gate is complete.
