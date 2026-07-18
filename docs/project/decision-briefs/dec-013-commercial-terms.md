---
id: SC-OPS-017
title: StoneCharts DEC-013 Commercial Terms Decision Brief
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-PROD-001, REQ-REL-001]
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# DEC-013 Commercial Terms Decision Brief

## Decision question

What commercial license, contribution terms, support model, and access model apply?

## Recommendation

Adopt the commercial-terms and access policy:

1. Keep the product proprietary until a written business model is approved.
2. Do not promise contribution rights, source access rights, distribution rights, or
   support obligations without an explicit policy record.
3. Treat internal repository access and engineering progress as separate from external
   commercial permission.
4. Require the approved policy before public-facing commercial language is used.

This is the correct boundary for the current repo state because the product has not yet
approved a final commercial operating model.

## Options

| Option | What it means | Tradeoff |
|---|---|---|
| Keep the proprietary boundary | No commercial or contribution promises until approved | Safest fit for current state |
| Open contribution and support terms now | Expose terms before they are governed | Creates avoidable ambiguity |
| Defer the decision indefinitely | Leave commercial and support rules unstated | Weakens governance |

## Stakeholder impact

- Product: keeps release language honest.
- Engineering: does not have to improvise policy from technical progress.
- QA and compliance: know which approved document governs external claims.
- Users and partners: are not misled about rights or support.

## Outcome

DEC-013 is approved as a boundary policy: no commercial license, contribution model,
support model, or external access promise is active until a written business policy is
approved.
