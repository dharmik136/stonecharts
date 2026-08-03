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
last_reviewed: "2026-07-29"
review_due: "2026-08-29"
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
  --from-source \
  --evidence .tmp-stoneverify
```

Deliberate-drift demonstration:

```bash
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --runtime python \
  --runtime go \
  --from-source \
  --demo-drift text \
  --evidence .tmp-stoneverify-drift
```

Baseline comparison:

```bash
python tools/stonecharts_verify.py charts/bubble/examples/basic.json \
  --runtime python \
  --runtime go \
  --from-source \
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

## Market segment fit judgment

The segments below are ranked by strategic judgment, not measured market data - no
interview or sales evidence yet supports any of these hypotheses. They exist to guide
where to look after the insurance validation segment, not to expand scope now;
`DEC-017`'s freeze and the validation gate below still govern what gets built. An
earlier draft scored these segments with precise decimals (for example "8-8.5/10");
those numbers are retired here for the same reason the platform-completion table's
were - see that section below - and kept, unaltered, in the internal research
appendix of
[`decision-briefs/dec-017-visual-integrity.md`](../project/decision-briefs/dec-017-visual-integrity.md).

| Segment | Fit hypothesis | Evidence confidence |
|---|---|---|
| Insurance reporting and actuarial platforms (current) | Strong potential fit | Low-medium |
| Financial-risk and regulatory reporting | Strong adjacent fit | Low |
| Pharmaceutical and clinical reporting | Plausible but domain-intensive | Low |
| Government, defense, air-gapped reporting | Plausible but procurement-heavy | Low |
| Embedded reporting and document-generation vendors | Promising operational fit | Low |

Poor fit - do not pursue without a specific reason to revisit:

| Segment | Fit hypothesis | Evidence confidence |
|---|---|---|
| Front-end interactive dashboards | Poor fit | Medium |
| Exploratory data science | Poor fit | Medium |
| Small-business/email chart generation | Poor fit | Medium |
| General open-source developer adoption | Poor fit under the current license | Medium |

## Land-and-expand model

If the validation gate is met and a segment converts, the expected sales motion is
sequential, not a single sale:

```text
one report workflow -> one paid StoneVerify pilot -> one reporting platform ->
all reports in that business unit -> central policy and baseline management ->
additional runtimes and business units
```

StoneVerify is the initial sale. StoneVault and StonePolicy are the expansion
products once a customer already trusts StoneVerify's evidence. StoneMigrate is the
adoption accelerator that lowers the cost of bringing a customer's existing chart
configurations under the governed contract. This ordering is a judgment about
sequencing, not a commitment to build Vault, Policy, or Migrate - each still requires
its own `DEC` and `REQ` under the expansion rule once, and if, a paying workflow asks
for it.

## Platform completion judgment (deferred)

This section records a strategic judgment about what completing the full platform
direction - StoneSpec, StoneRender, StoneVerify, StoneVault, StonePolicy, and
StoneMigrate, plus broader chart-family coverage - could be worth, and what it could
not prove by itself. It does not authorize any of that work; `DEC-017`'s freeze and
the expansion rule still govern what actually gets built, and StoneVault, StonePolicy,
and StoneMigrate remain later product surfaces per Product direction above.

| State | Market-fit hypothesis | Evidence confidence |
|---|---|---|
| Current product | Early technical wedge; market demand unproven | Low |
| Full chart breadth only | Better eligibility, limited differentiation | Medium |
| Complete Verify/Policy/Vault/Migrate platform | Strong specialized-enterprise potential | Low-medium |
| Report-wide integrity | Larger long-term category hypothesis | Low |

"Evidence confidence" describes how much this document's own reasoning (competitive
comparison, segment characteristics, structural argument) supports the hypothesis in
each row - it is not a market-research or customer-validation score, and none of
these rows should be read as measured. "Full chart breadth only" is rated ahead of
the current product on eligibility but is explicitly the weakest differentiator:
mainstream libraries (Highcharts 40+ types, Plotly 70+, ECharts 20+) already win on
catalog size, and StoneCharts cannot out-catalog them. The differentiated position is
the integrated system - spec, certified renderers, semantic verification, policy
evaluation, baseline approval, evidence retention, migration and release history -
not any single component.

A prior draft of this section carried precise decimal scores (for example, "4.5/10
today" and "7.5-8/10 potential"). Those numbers are retired from the normative
judgment above because their precision implied measurement this document does not
have; the underlying reasoning is preserved, unaltered, in the internal research
appendix of
[`decision-briefs/dec-017-visual-integrity.md`](../project/decision-briefs/dec-017-visual-integrity.md),
not restated here as approved figures.

A further-out hypothesis, explicitly not part of any current scope: the ceiling could
rise substantially if the category eventually widens from chart integrity to
report-wide integrity (charts, tables, document sections, versioned calculations,
approval workflows, evidence packages). This is a future hypothesis, not a
validation-gate target.

Three assumptions the validation gate below must still resolve before any of this
judgment can be acted on:

1. Do customers experience costly, recurring visual drift, not a one-off annoyance?
2. Is chart-aware semantic verification materially better than the visual-regression
   tools they could already use, such as Chromatic, Applitools, or a manual
   screenshot review?
3. Will the economic buyer fund a dedicated platform, or absorb the problem inside
   existing QA and reporting tooling?

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
