---
id: SC-PROD-003
title: Visual Integrity Strategy
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: independent
applies_to: 0.0.0.4 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-28"
review_due: "2026-08-28"
supersedes: null
superseded_by: null
---

# Visual Integrity Strategy

StoneCharts has a credible technical wedge, but it does not yet have demonstrated
product-market fit. The next product phase validates a narrower market claim before
admitting another broad chart-expansion cycle.

## Category hypothesis

StoneCharts should test the category **Visual Integrity Infrastructure**:

> Visual Integrity Infrastructure ensures that charts and reporting visuals are
> reproducible, policy-compliant, explainable, and verifiable across systems,
> languages, and software releases.

This places StoneCharts outside the crowded "general charting library" frame. The
highest-value product is not a larger chart catalog; it is a governed visual artifact
system for teams that must prove why a chart can be trusted.

## Initial validation segment

The first validation segment is **insurance reporting and actuarial platforms**.
This segment has recurring controlled reports, audit sensitivity, backend rendering
workflows, and a procurement path that is likely more reachable than broader
financial, clinical, government, or defense reporting.

Initial message:

> StoneCharts helps insurance reporting teams prove that charts remain consistent
> across Python and Go services, dependency upgrades, and controlled report releases.

Adjacent segments remain candidates only after the insurance workflow is tested:
financial risk and regulatory reporting, pharmaceutical or clinical reporting, and
government or defense reporting.

## Competitive frame

Mainstream chart systems already cover general-purpose visualization well. StoneCharts
should not compete primarily on chart count, visual flexibility, or exploratory
analytics.

The useful competitive contrast is narrower:

- browser or export-service based rendering can be operationally expensive to run in
  controlled environments;
- hosted chart APIs reduce implementation work but may be disqualified by privacy,
  air-gap, provenance, or support boundaries;
- broad visualization grammars are powerful, but they do not primarily sell signed
  cross-runtime conformance evidence and governed release history.

Any public competitor comparison must distinguish measured facts from hypotheses.
Performance targets, security claims, and cost-savings claims are not sales claims
until they are measured against reproducible competitor configurations.

## Product direction

The proposed platform shape is:

- **StoneSpec**: a stable, versioned, language-neutral reporting visualization
  specification.
- **StoneRender**: certified runtime implementations for selected languages, currently
  Python and Go.
- **StoneVerify**: the flagship conformance product: cross-runtime comparison,
  semantic/cosmetic diff classification, CI output, and evidence generation.
- **StoneVault**: immutable approved visual baselines and render metadata. This is a
  later product surface, not a first pilot dependency.
- **StonePolicy**: organization-level rules for approved chart types, colors,
  accessibility, formats, locales, and export restrictions.
- **StoneMigrate**: selective migration assessment for common reporting patterns from
  existing chart configurations.

The next implementation proof is `StoneVerify`. It should dramatize conformance:

1. Load one shared chart specification.
2. Render it in Python and Go.
3. Verify the artifacts.
4. Introduce deliberate drift.
5. Fail the conformance check in CI.
6. Generate a human-readable and machine-readable evidence report.

Initial command shape:

```bash
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --runtime python \
  --runtime go \
  --evidence .tmp-stoneverify
```

Deliberate-drift demonstration:

```bash
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --runtime python \
  --runtime go \
  --demo-drift text \
  --evidence .tmp-stoneverify-drift
```

Baseline comparison:

```bash
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --runtime python \
  --runtime go \
  --baseline-evidence .tmp-stoneverify-bubble \
  --evidence .tmp-stoneverify-baseline-check
```

Evidence bundle self-check:

```bash
python tools/stonecharts_verify.py --check-evidence .tmp-stoneverify-bubble
```

The first pilot should produce an evidence bundle that customers can store in their
existing repository or artifact system:

```text
evidence/
├── manifest.json
├── input-spec.json
├── python-output.svg
├── go-output.svg
├── comparison.json
├── report.html
└── checksums.txt
```

Hosted storage, approval workflows, identity, retention controls, and audit logs are
explicitly deferred until customer demand proves StoneVault should be built.

## Positioning

Preferred one-sentence pitch:

> StoneCharts helps regulated software teams generate, verify, and audit consistent
> charts across backend languages without relying on browser-based rendering
> infrastructure.

Preferred homepage headline:

> Every chart change should be provable.

Supporting proof points:

1. One contract: a shared versioned chart specification.
2. Verified runtimes: qualified output across supported languages.
3. Audit evidence: conformance results for every release.

Avoid leading with "another charting library", "interactive chart library", "many
chart types", or "native chart renderer". Lead with intentional, testable, and
attributable report changes.

## Validation gate

Do not significantly expand engineering breadth until StoneCharts has:

- 20 qualified interviews in one tightly defined segment;
- at least 10 recurring rendering, audit, or export-infrastructure problems;
- at least 6 quantified engineering, compliance, or release-review costs;
- at least 4 real production fixtures supplied for evaluation;
- at least 3 completed technical proofs of value;
- at least 2 paid pilots;
- at least 1 annual conversion;
- a clearly identified economic buyer and budget source.

The strongest interview question is:

> What did this problem cost your organization during the past 12 months?

If prospects cannot identify a recurring cost, the problem is likely accepted as
manageable and StoneCharts should not scale engineering investment yet.

## Licensing boundary

The current repository license is proprietary and grants no commercial or
non-commercial use without a separate written agreement. Public specification,
open-core distribution, public fixture corpora, or community runtime access are
licensing options for a future decision, not current permissions or commitments.

Recommended future licensing hypothesis:

- public specification and conformance manifest format;
- public limited fixture corpus;
- commercial certified renderers, verification tooling, LTS, support, policy packs,
  and redistribution rights.

No document may describe StoneCharts as open source or open core until the license
and publication policy actually permit it.

## Next-work rule

Until the validation gate is met, prioritize evidence before breadth:

- freeze new chart-family admissions unless a paying validation workflow requires one;
- build StoneVerify-style conformance and evidence workflows around existing certified
  charts;
- replace hypothetical benchmark claims with measured, reproducible comparisons;
- resolve the public specification versus commercial runtime business model;
- remove generic pilot/onboarding material that does not demonstrate StoneCharts'
  actual chart-conformance workflow.

Formal decision statement:

> StoneCharts will pause broad chart-family expansion after version 0.0.0.4. The
> next product phase will focus on validating Visual Integrity Infrastructure within
> insurance reporting and delivering a working StoneVerify conformance workflow. New
> chart types, languages, hosted services, and document-generation capabilities
> require either paid customer evidence or explicit approval as necessary validation
> infrastructure.
