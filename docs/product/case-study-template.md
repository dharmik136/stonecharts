---
id: SC-PROD-008
title: Pilot Case-Study Template
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4 and later
requirements: []
evidence: []
last_reviewed: "2026-07-29"
review_due: "2026-08-29"
supersedes: null
superseded_by: null
---

# Pilot Case-Study Template

An empty template. Do not fill in placeholder or hypothetical numbers here — every
bracketed field below is filled in only after a real pilot produces the fact it asks
for, following [`SC-PROD-003`](visual-integrity-strategy.md)'s rule to distinguish
measured facts from hypotheses. An unfilled template committed with invented figures
would violate the same rule this document exists to support.

## Customer context

- Organization type: `[insurance reporting / actuarial platform / other, per DEC-017's segment]`
- What they render today and in what languages/services: `[fill in from the discovery interview, SC-PROD-006]`
- The recurring problem they named, in their own words: `[quote from the interview]`
- The quantified cost they named (per `SC-PROD-003`'s key interview question — "what
  did this problem cost your organization during the past 12 months?"): `[hours / dollars / a specific audit or filing incident]`

## What was piloted

- Chart type(s) and real fixture(s) used: `[names, not descriptions - link to the actual anonymized spec if permitted]`
- Languages/runtimes verified: `[Python / Go / both]`
- StoneVerify workflow used: `[normal run / baseline comparison / CI integration - see SC-QUAL-004]`
- Pilot duration: `[start date] to [end date]`

## What was measured during the pilot

Only real, pilot-specific measurements belong here — do not copy numbers from
`SC-QUAL-003` (that document is StoneCharts' own vendor-run benchmark against public
alternatives, not this customer's result).

- Conformance result: `[pass/fail, and what StoneVerify's evidence bundle showed]`
- Any drift found, and whether it was real (a renderer bug) or a false positive (e.g.
  the Highcharts-style non-determinism `SC-QUAL-003` documents) is only relevant if
  the pilot customer was migrating from a system with that property: `[describe]`
- Customer-reported time or cost saved: `[only if the customer measured and stated
  this themselves - attribute it to them, do not compute it on their behalf]`

## Outcome

- Did the pilot convert to a paid engagement? `[yes/no/pending]`
- Quote from the customer (only with their explicit permission to publish): `["..."]`
- What would need to be true for this to generalize to other prospects in the same
  segment: `[fill in honestly, including reasons it might not generalize]`

## Review

- Reviewed by: `[name]`
- Date: `[date]`
- This case study is approved for external use only after the customer has explicitly
  agreed to being referenced, per the licensing and publication boundary in `DEC-018`.
