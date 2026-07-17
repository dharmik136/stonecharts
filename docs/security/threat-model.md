---
id: PC-SEC-001
title: PeakCharts Threat Model
status: proposed
classification: normative
owner: security-contact
approver: maintainer
review_mode: self
applies_to: 0.0.1-alpha.1
requirements: [REQ-SEC-001, REQ-CUST-001, REQ-CAP-001]
evidence: [TEST-XSS-ESCAPING, TEST-CAPABILITY-MATRIX, TEST-RUNTIME-BROWSER]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Threat Model

## Scope and assets

Protected assets are host application integrity, generated SVG/HTML integrity, chart
data confidentiality, renderer availability, release artifacts, package consumers, and
the credibility of PeakCharts conformance claims.

Chart specs are untrusted even when constructed through typed APIs. Output may be
opened as a document, embedded inline, served by an application, converted by another
tool, or included in reports.

## Trust boundaries

1. Spec input into language parsers and validators.
2. User strings and style values into SVG/XML attributes and text.
3. SVG and data attributes into runtime HTML and CSS sinks.
4. Generated files into host applications and downstream converters.
5. Dependencies, toolchains, fonts, and build services into release artifacts.

## Priority threats and controls

| Threat | Current or required control | Residual gap |
|---|---|---|
| SVG/HTML script injection | Contextual escaping and hostile-string tests | Structured color/style validation remains incomplete |
| CSS/style injection | No raw CSS in certified spec | Color and URL grammar need explicit allowlists |
| Identifier/reference injection | Escaped IDs and scoped defs | Pure-static multi-chart IDs require unique chart IDs |
| Runtime DOM XSS | Runtime encodes tooltip text | Inline color insertion requires validated color grammar |
| Denial of service | Dimension and input validation | Formal data-size and complexity limits not yet set |
| Panic/exception on input | Planned typed capability boundary | Current dispatch can still panic/throw |
| Supply-chain substitution | Planned hashes, SBOM, provenance | No release pipeline yet |
| Malicious downstream converter | Certified exporters will be pinned | Arbitrary converters remain outside guarantees |
| Accessibility spoofing or loss | Contracted names, table, keyboard tests | Browser and assistive-technology qualification pending |

## Security rules

- The certified schema MUST NOT accept executable code, raw markup, event attributes,
  or unrestricted URLs.
- Encoding is contextual; XML text encoding is not assumed safe for style, URL, or
  script contexts.
- Unknown fields MUST NOT create hidden executable behavior.
- Render limits for dimensions, series, points, string lengths, and nested style
  objects must be defined before untrusted multi-tenant service use.
- Security defects rated critical or high block release unless the product owner and
  security contact record a time-bounded risk acceptance. In the current solo role
  model, that acceptance is explicitly self-approved and not an independent audit.

## Out of scope for Alpha core

PeakCharts is not yet a hosted multi-tenant service. Authentication, authorization,
tenant isolation, network controls, billing, account recovery, production monitoring,
and service incident response require a separate service threat model before an app is
deployed.

