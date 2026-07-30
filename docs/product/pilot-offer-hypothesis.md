---
id: SC-PROD-011
title: StoneVerify Pilot-Offer Hypothesis
status: proposed
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4 and later
requirements: []
evidence: []
last_reviewed: "2026-07-30"
review_due: "2026-08-30"
supersedes: null
superseded_by: null
---

# StoneVerify Pilot-Offer Hypothesis

## What this document is

This is a **pilot-offer hypothesis, not an approved price list**. It exists to give
prospect conversations something concrete to react to, so the reaction — not a guess
made in advance — decides which offer structure, framing, and price band actually
converts. Every dollar figure below is an untested hypothesis to be revised (or
discarded) from real conversation data gathered through
[`SC-PROD-010`](prospect-outreach-plan.md)'s pipeline and scored with
[`SC-PROD-006`](prospect-qualification-scorecard.md)'s interview script. Nothing here
is a quote, a commitment, or a claim that any prospect has agreed to any of these
terms.

## What this document is not

- **Not a commercial terms approval.** All actual commercial terms — license grant,
  support boundary, distribution rights, and commercial use scope — are governed
  exclusively by [`SC-CON-020`](../contracts/commercial-terms-policy.md). This
  document does not restate, replace, or contradict that policy; it only proposes
  structures to *test in conversation*. No pilot may actually be contracted,
  invoiced, or distributed until SC-CON-020's required written approvals exist.
- **Not authorization to sell.** `GATE-VERIFY-PILOT-001` (a Release Gate tracked in
  [`docs/project/backlog.yaml`](../project/backlog.yaml)) is what certifies StoneVerify
  as pilot-ready — installable outside the repository, semantically explaining drift,
  defaulting to cross-release comparison, robust against external fixtures, packaged
  into a reviewable evaluation kit, and CI-integrated. Until that gate passes, this
  document may be used to *discuss and test* offer framing with prospects, but no
  structure below may be contracted or delivered as a real paid engagement. Discovery
  and objection-testing may proceed in parallel with `GATE-VERIFY-PILOT-001` closing,
  per `WORK-GTM-011`'s own scheduling; actually closing a sale may not.
- **Not a claim about product scope.** Every structure below is bounded to the
  commercial pilot scope already defined in
  [`SC-PROD-004`](capability-matrix.md#commercial-pilot-scope): Python and Go only,
  the certified `line`/`column`/`bar`/`area`/`scatter`/`bubble` chart set, local
  evidence bundles, no hosted storage.

## Why three structures, not one

`SC-PROD-006`'s interview script already asks every qualified prospect who owns the
budget and what their approval path looks like for a paid pilot
(see [`SC-PROD-009`](cost-quantification-worksheet.md)'s "Cost category 6: Budget and
buyer"). That question does not tell us which *framing* — software, technical proof,
or services — matches how that budget owner actually buys. Proposing only one
price band in advance would test a guess about framing instead of the framing itself.
Each structure below is scoped narrowly enough to run as a real, bounded engagement,
and different enough in framing that a prospect's reaction to each one is itself a
data point about which model to pursue.

## Common scope elements (apply to all three structures)

Unless a structure's section below states otherwise, every candidate offer is bounded
to:

- **One report workflow** — the prospect's own real chart or report specification,
  not a synthetic example, per `SC-PROD-006`'s interview question asking whether the
  prospect can supply a real, anonymizable fixture.
- **One or two runtimes** — Python only, Go only, or Python-and-Go comparison; never
  a third language, per `SC-PROD-004`'s deferred-capabilities list.
- **A bounded fixture set** — a small, named number of chart specifications agreed in
  advance, not open-ended "verify whatever we send you."
- **Baseline creation** — an initial approved-good evidence bundle
  (see [`SC-QUAL-004`](../quality/stoneverify-quickstart.md)) established before any
  comparison run is treated as pass/fail.
- **CI integration** — wiring `tools/stonecharts_verify.py` into the prospect's own
  CI (illustrated, not prescribed, by the workflow template in
  `SC-QUAL-004`'s "Dropping this into a customer's own CI" section), so verification
  runs on the prospect's own pipeline, not only on a demo machine.
- **Evidence-report delivery** — the `manifest.json` / `comparison.json` /
  `report.html` / `checksums.txt` bundle `SC-QUAL-004` already produces, handed to the
  prospect as the deliverable artifact, not a slide deck describing it.

## Candidate structure 1 — Low-friction paid assessment

**Framing: a paid diagnostic, priced like software, not a services engagement.**

- **Scope:** one report workflow, one runtime pair (Python-and-Go), a fixture set of
  1-3 chart specifications the prospect supplies. Baseline creation and one
  comparison run against it. CI integration is a documented template handed to the
  prospect's engineering team to wire in themselves, not performed on their
  infrastructure by us.
- **Deliverable:** one evidence bundle plus a short written read-out of what it shows.
- **Hypothesized price band (untested):** roughly $2,000-$5,000, one-time.
- **What this tests:** whether a low commitment, low-price, self-serve-leaning offer
  is enough to get a "yes" from a budget owner who cannot easily approve a services
  contract, and whether the diagnostic alone (without hands-on CI integration)
  produces a result the prospect finds credible enough to act on.

## Candidate structure 2 — Fixed-scope technical proof

**Framing: a bounded, hands-on technical proof of value, priced between a diagnostic
and a full engagement.**

- **Scope:** one report workflow, one or two runtimes, a fixture set of up to 5 chart
  specifications. Baseline creation, CI integration performed jointly with the
  prospect's engineering team against their real CI system (not just a template
  handed off), and at least two comparison runs — one demonstrating a passing
  baseline, one demonstrating a deliberately introduced or naturally occurring drift,
  matching the "prove it fails honestly before trusting it passes honestly" pattern
  in `SC-QUAL-004`.
- **Deliverable:** the evidence bundle for each run, the working CI integration left
  in place in the prospect's own repository, and a short written summary of findings.
  This is the same "technical proof of value" step named as the next step for a
  qualified prospect in [`SC-PROD-007`](one-pager.md#next-step-for-a-qualified-prospect)
  and counted toward `SC-PROD-003`'s "at least 3 completed technical proofs"
  validation-gate criterion.
- **Hypothesized price band (untested):** roughly $8,000-$15,000, one-time or as a
  fixed-term (30-60 day) engagement.
- **What this tests:** whether a fixed-scope, fixed-price technical engagement is the
  framing that a platform/infrastructure engineering lead (one of `SC-PROD-006`'s
  three target personas) can get approved without a longer procurement cycle, and
  whether "working CI integration left behind" is itself the differentiating value
  versus structure 1's read-out-only deliverable.

## Candidate structure 3 — Higher-priced implementation pilot

**Framing: a recurring services engagement, priced like an implementation, not a
one-time diagnostic.**

- **Scope:** one report workflow, one or two runtimes, a bounded fixture set (up to
  10 chart specifications, expandable only by written agreement), baseline creation,
  full CI integration maintained jointly for a fixed term (suggested: one full
  reporting cycle — e.g., one quarterly filing period — so the offer covers at least
  one real recurring use, not a single snapshot), and evidence-report delivery on an
  ongoing cadence (e.g., per CI run or per filing cycle) rather than a single
  hand-off.
- **Deliverable:** everything in structure 2, plus a defined renewal or conversion
  conversation at the end of the term, explicitly tied to `SC-PROD-003`'s "1 annual
  conversion" validation-gate criterion and to `WORK-GTM-012`'s planned pilot record
  (buyer, budget owner, renewal willingness, strongest objection, requested
  chart/runtime expansion).
- **Hypothesized price band (untested):** roughly $20,000-$40,000 for the fixed term,
  positioned as the highest-commitment of the three.
- **What this tests:** whether an audit/compliance/actuarial reporting owner or a
  reporting/BI product manager (the other two `SC-PROD-006` personas) values ongoing,
  recurring verification enough to fund it at services-engagement pricing, and
  whether a services framing — versus structures 1 and 2's software/technical-proof
  framing — is what an economic buyer with a compliance or audit budget actually
  responds to.

## What to learn from each conversation

Every conversation that reaches a pilot-offer discussion (per `SC-PROD-010`'s Phase 5,
after a technical proof has succeeded) should come back with answers to all three of
the following, regardless of which structure the prospect reacts to most favorably:

1. **Who can actually authorize the purchase** — the named individual or role, not an
   assumed title. This is the same question `SC-PROD-006`'s script already asks
   ("who owns the budget... what does your approval path look like for a paid
   pilot?") and `SC-PROD-009`'s "Cost category 6" worksheet field is built to
   capture; this document does not introduce a new question, it names why the answer
   matters for pricing.
2. **Which budget it comes from** — engineering/infrastructure budget, audit/
   compliance budget, or a reporting/BI product budget. The budget line is itself
   evidence about which of the three structures' framing (software, technical proof,
   or services) is the one that will actually get approved, independent of which
   price the prospect says out loud.
3. **Whether verification, migration, or compliance evidence is valued most** — i.e.,
   whether the prospect's stated interest is in ongoing drift verification (favors
   structure 3's recurring framing), a one-time technical proof before a decision
   (favors structure 2), or a low-commitment sanity check before either (favors
   structure 1). A prospect who cares most about producing an audit-ready evidence
   bundle for a regulator or client is a different buyer than one who cares most
   about catching drift in CI before merge, even if both are willing to pay.

Record these three answers using the existing outside-source-control tracking method
described in `SC-PROD-010` and, once a pilot actually runs,
`WORK-GTM-012`'s pilot record — not inline in this governed document, and never with
real prospect names or figures committed to this repository.

## Revision rule

This hypothesis is expected to be wrong in places. Revise the price bands, scope
boundaries, or the set of structures itself as soon as real conversation data
(objections, budget answers, or which structure gets a "yes") contradicts an
assumption above. Do not treat any figure in this document as validated until a
structure has actually converted per `SC-PROD-003`'s gate criteria.
