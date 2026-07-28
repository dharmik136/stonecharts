---
id: SC-PROD-005-ANTIGRAVITY
title: StoneCharts Pricing and Packaging Specification
status: proposed
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: Post-0.0.0.1
requirements: []
evidence: []
last_reviewed: "2026-07-21"
review_due: "2026-10-21"
supersedes: null
superseded_by: null
---

# pricing-and-packaging.md

> [!WARNING]
> Superseded research artifact - not an approved product commitment. The approved
> post-0.0.0.4 direction is governed by
> `docs/product/visual-integrity-strategy.md`,
> `docs/product/capability-matrix.md`, and DEC-017.

This specification outlines the commercial licensing model, open-core feature boundaries, pricing tiers, and service-level agreement (SLA) guidelines proposed for the post-0.0.0.1 market validation.

---

## 1. Feature Allocation (Open Core vs. Commercial)

To balance adoption velocity with commercial returns, we split features between the open-source community edition and the paid enterprise catalog.

| Feature Area | Community (Open Source) | Enterprise (Paid SDK & License) |
| :--- | :--- | :--- |
| **Active Scope** | `line`, `column` | `line`, `column` + `bar`, `area`, `scatter`, `combo`, `histogram`, `arearange` |
| **Language Renderers** | Python (Standard) | Python, Go, and certified JVM/JS native ports |
| **Visual Output** | Standard SVG (Responsive) | Standard SVG + Certified Export Profiles (PDF/A, print, high-DPI raster) |
| **Parity Validation** | Manual test scripts | Automated Conformance Test Suite (CLI/CI actions) |
| **Security Controls** | Basic XSS escaping, cryptographic build hashes (basic SBOM) | FIPS compliance verification, advanced SBOM exports, third-party vulnerability audits |
| **Support & Updates** | GitHub Community (Best Effort) | Pinned LTS releases, priority security patches, 4hr response SLA |

---

## 2. Pricing & Licensing Tiers

The pricing model avoids CPU/server licensing (which hurts cloud scaling) and developer seat licensing (which blocks team adoption). Instead, it scales with **active deployments** and **redistribution rights**.

### Tier 1: Developer/Evaluation (Free)
* **License**: Evaluation or non-commercial use only.
* **Price**: $0
* **Scope**: Single-developer machines, local test environments.
* **Support**: Best effort via public discussions.

### Tier 2: Team Commercial SDK (Growth)
* **License**: Commercial use for internal application teams.
* **Price**: $4,900 / year (flat fee)
* **Scope**: Up to 3 internal staging/production applications, unlimited developers, 2 certified languages.
* **Support**: Next-business-day email support.

### Tier 3: ISV / Embedded Analytics (Redistribution)
* **License**: Right to embed StoneCharts within commercial SaaS or on-premise platforms sold to end customers.
* **Price**: Starts at $12,500 / year
* **Scope**: Unlimited internal and external distribution, custom visual branding presets, all certified languages.
* **Support**: Priority support (8hr SLA), dedicated Slack channel.

### Tier 4: Regulated Enterprise (Auditable)
* **License**: Full source code access, air-gapped registry keys, and immutable release evidence packs.
* **Price**: Custom contract (starts at $25,000 / year)
* **Scope**: Air-gapped deployments, custom-developed native renderers, and certified compliance artifacts.
* **Support**: Dedicated technical account manager, 4hr critical SLA.

---

## 3. SLA and Support Protocol

Regulated reporting platforms require high reliability during automated reporting runs. Enterprise licenses include:

> [!WARNING]
> Visual regression is treated as a P0 issue for regulated analytics. SLA agreements must explicitly cover rendering inconsistencies.

* **Render Drift Resolution**: Any byte-parity deviation between certified languages on the conformance fixture set is guaranteed a patch within 48 hours.
* **Security Patching**: Vulnerabilities in coordinate parsing or schema validation are patched and backported to all active LTS version nodes.
* **Response Windows**:
  * *Severity 1 (Pipeline blocker)*: 4 hours
  * *Severity 2 (Minor rendering issue)*: 24 hours
  * *Severity 3 (Feature request/general question)*: 5 business days
