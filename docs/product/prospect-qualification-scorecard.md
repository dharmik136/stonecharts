---
id: SC-PROD-006
title: Prospect Qualification Scorecard and Interview Script
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-29"
review_due: "2026-08-29"
supersedes: null
superseded_by: null
---

# Prospect Qualification Scorecard and Interview Script

## Purpose

[`DEC-017`](../project/decisions.md)'s brief lists "build a prospect qualification
scorecard and interview script" as immediate work. This document operationalizes the
validation gate defined in [`SC-PROD-003`](visual-integrity-strategy.md) for the
initial validation segment: insurance reporting and actuarial platforms. It exists to
score real interviews consistently, not to record them — see
[Handling interview records](#handling-interview-records) below.

## Segment and target roles

Interviews are scoped to insurance reporting and actuarial platforms only, per
DEC-017. Do not spend interview capacity qualifying adjacent segments (financial risk,
clinical, government/defense reporting) until this segment's validation gate is met.

Target roles:

- **Platform or infrastructure engineering lead** — owns the services that render
  reports and charts today.
- **Audit, compliance, or actuarial reporting owner** — owns report accuracy, sign-off,
  and filing.
- **Reporting or BI product manager** — owns exports, white-labeling, and client- or
  regulator-facing report delivery.

## Interview script

Do not open by pitching StoneCharts. Open by asking about cost. The strongest
question, per `SC-PROD-003`:

> What did this problem cost your organization during the past 12 months?

Ask in this sequence:

1. How many independent chart- or report-rendering implementations does your team
   maintain across backend services, analysis notebooks, and client-facing exports?
2. Walk me through how a chart or figure gets from a data pipeline into an audited,
   filed, or client-delivered report today.
3. Has a chart or figure ever looked different between two systems, two releases, or
   two teams' tools in a way that caused a review question, a refiling, or a client
   complaint? What did resolving that cost — in hours, in a delayed filing, or in an
   audit finding?
4. Do you run headless-browser or Node-based rendering (Puppeteer, Playwright, an
   export server) in a controlled or air-gapped environment? Has that ever been
   flagged in a security or platform review?
5. When you upgrade a charting dependency or a report-rendering service, how do you
   verify nothing visually changed? What would an automatic pass/fail check for that
   be worth to you?
6. Could you share a real, anonymizable report or chart specification we could use as
   a conformance fixture?
7. Who owns the budget for reporting infrastructure or audit tooling here, and what
   does your approval path look like for a paid pilot?

Never ask "would you use this" — it produces false positives instead of evidence.

## Scoring rubric

Score every interview against the validation gate criteria in `SC-PROD-003`. Each
checked box counts toward that gate's running total, not toward this single
interview's outcome:

- [ ] Named a recurring rendering, audit, or export-infrastructure problem.
- [ ] Quantified a real cost: hours, dollars, or a specific audit or filing incident.
- [ ] Offered, or agreed in principle, to supply a real production fixture.
- [ ] Named an identifiable economic buyer or budget owner.
- [ ] Expressed interest in a technical proof of value.
- [ ] Expressed openness to a paid pilot.

## Disqualification signals

Disqualify and move on when an interview shows any of:

- The primary need is browser-only interactive or animated dashboards.
- No recurring cost is identified and the prospect is not uncomfortable with current
  tooling.
- No path to an identifiable economic buyer emerges from the conversation.

## Tracking against the validation gate

`SC-PROD-003` requires, before significant engineering-breadth expansion resumes: 20
qualified interviews, at least 10 recurring problems, at least 6 quantified costs, at
least 4 real fixtures, at least 3 completed technical proofs, at least 2 paid pilots,
and 1 annual conversion. Keep a running tally against these thresholds; do not resume
broad chart-family expansion on the basis of engineering readiness alone.

## Handling interview records

Real interview notes will name prospects, organizations, and internal cost figures.
That is customer and business-sensitive information and MUST NOT be committed to this
governed, version-controlled document or elsewhere in the repository. Keep a separate,
access-controlled interview log outside of source control; use this document only for
the script, the rubric, and the aggregate tally against the validation gate.
