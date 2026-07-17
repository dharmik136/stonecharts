---
id: SC-GOV-001
title: StoneCharts Documentation Control Policy
status: proposed
classification: normative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: all
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-10-18"
supersedes: null
superseded_by: null
---

# Documentation Control Policy

## Purpose

StoneCharts treats product promises, requirements, architecture decisions, contracts,
quality gates, security controls, and release evidence as versioned product assets.
This policy keeps those assets reviewable and traceable without equating document
count with engineering maturity.

## Authority and language

Normative documents define obligations. Informative documents explain context or
intent and cannot override a normative source. The words `MUST`, `MUST NOT`,
`SHOULD`, `SHOULD NOT`, and `MAY` have the meanings defined by BCP 14 (RFC 2119 and
RFC 8174) only when capitalized.

When sources conflict, authority descends in this order:

1. Released schema and versioned normative contracts.
2. Approved architecture decision records.
3. Approved requirements in `docs/requirements/registry.yaml`.
4. Approved chart and substrate designs.
5. Roadmaps, research, examples, and commentary.

An approved lower source that conflicts with a higher source is defective and MUST
be corrected or explicitly superseded.

## Controlled material

Markdown under `docs/governance`, `docs/product`, `docs/requirements`,
`docs/architecture`, `docs/contracts`, `docs/quality`, `docs/security`, and
`docs/releases` is controlled and MUST contain valid frontmatter. Released chart
designs and `spec/svg-contract.md` are also controlled. Machine-readable registries
and schemas are controlled through their own schemas and Git history.

`docs/research` contains working evidence and is not normative. Existing roadmap
material is being migrated incrementally; its implementation sequence remains useful,
but approved contracts and ADRs take precedence. Diataxis categories are reserved for
user documentation (`tutorial`, `how-to`, `reference`, `explanation`); they are not
used to organize internal governance records.

## Required metadata

Every controlled Markdown document MUST declare the fields validated by
`docs/governance/schemas/document-metadata.schema.json`. IDs are immutable. Git is
the change history; frontmatter records current control state, applicability, links,
and review responsibility.

The project currently has one human maintainer. Role names therefore represent real
responsibilities held in `docs/governance/roles.yaml`; they do not imply fictional
boards or working groups. `review_mode: self` makes the lack of independent review
explicit. A document MUST NOT claim independent review unless another qualified
person performed it.

## Lifecycle

`draft` means incomplete. `proposed` means complete enough for decision review.
`approved` means authoritative within its applicability. `deprecated` remains valid
for existing consumers but should not be used for new work. `superseded` has a named
replacement. `archived` is retained only as history.

Normative changes follow this sequence:

1. Add or update a requirement and its acceptance criteria.
2. Record architecturally significant choices in an ADR.
3. Update affected contracts and designs.
4. Add semantic tests before changing golden output.
5. Implement and collect immutable evidence.
6. Approve the release only when all applicable gates pass.

## Evidence policy

Document `evidence` fields contain stable evidence IDs, not the result of the latest
test run. Definitions live in `docs/quality/evidence-registry.yaml`. Individual runs
belong in an immutable release evidence directory and are referenced by a release
manifest. Automation MUST NOT rewrite approved normative documents to insert current
results.

## Generated and duplicated content

Schema reference, capability tables, document indexes, traceability views, benchmark
reports, and release manifests SHOULD be generated from machine-readable sources.
Generated files MUST identify their source and MUST NOT be edited manually. A concept
MUST have one authoritative source; summaries link to it rather than duplicating it.

## Review and staleness

The owner reviews a document by `review_due`, after a relevant contract change, or
before a release to which it applies. An overdue normative document blocks a release
unless the release record contains a written risk acceptance by the product owner.

