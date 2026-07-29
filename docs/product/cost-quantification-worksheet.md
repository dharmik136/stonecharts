---
id: SC-PROD-009
title: Interview Cost-Quantification Worksheet
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

# Interview Cost-Quantification Worksheet

A companion to [`SC-PROD-006`](prospect-qualification-scorecard.md)'s interview
script. Its scoring rubric asks whether a prospect quantified a real cost; this
worksheet is the structured way to capture that number during the conversation
instead of it staying a vague impression afterward. It supports one specific
validation-gate criterion in [`SC-PROD-003`](visual-integrity-strategy.md): "at least
6 quantified engineering, compliance, or release-review costs."

## How to use this

Fill this out live, during or immediately after an interview, from what the prospect
says. Never estimate or fill in a number the prospect did not state. An empty field is
honest; a guessed field is not evidence.

## Worksheet

**Interview date:** `[date]`
**Organization (or anonymized identifier):** `[ ]`
**Interviewee role:** `[platform engineering lead / audit-compliance-actuarial owner / reporting-BI product manager]`

### Cost category 1: Engineering time on duplicate/drifted rendering logic

- Do they maintain more than one chart/report-rendering implementation? `[yes/no]`
- If yes, estimated engineer-hours per month maintaining the duplication, **in their
  own words**: `[ ]`
- Loaded cost basis, if they state one (do not assume a rate): `[ ]`

### Cost category 2: A specific drift incident

- Did a chart or figure ever look different between two systems/releases/teams in a
  way that caused a review question, refiling, or complaint? `[yes/no]`
- What did resolving it cost — hours, a delayed filing, or a specific named incident?
  `[quote or paraphrase, with their permission to record it]`
- Did this happen once, or is it recurring? `[ ]`

### Cost category 3: Headless-browser/export-service operational cost

- Do they run Puppeteer/Playwright/a Node export service in a controlled or
  air-gapped environment? `[yes/no]`
- Has it been flagged in a security or platform review? `[yes/no, and what happened
  as a result]`
- Any stated cost of that review, remediation, or the service's own infrastructure
  footprint: `[ ]`

### Cost category 4: Regression-verification cost on dependency/library upgrades

- How do they currently verify nothing visually changed after a chart-library or
  rendering-service upgrade? `[describe their current process]`
- Estimated time this takes per upgrade cycle, in their words: `[ ]`

### Cost category 5: Client- or regulator-facing consequence

- Has a chart/report inconsistency ever reached a client or regulator? `[yes/no]`
- What was the stated consequence (a complaint, a support ticket, a filing question)?
  `[ ]`

### Cost category 6: Budget and buyer

- Who owns the budget for reporting infrastructure or audit tooling? `[name/role]`
- What is their approval path for a paid pilot? `[describe]`

## Rolling tally (across all interviews)

Keep a running count elsewhere (not in this per-interview file) of how many
interviews produced at least one filled-in, prospect-stated cost figure above. That
count is what closes `SC-PROD-003`'s "at least 6 quantified costs" gate criterion —
not the number of interviews conducted.
