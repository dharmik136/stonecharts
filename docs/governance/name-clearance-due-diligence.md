---
id: SC-GOV-NAME-DD-001
title: StoneCharts Name Clearance Due Diligence
status: draft
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4 and later
requirements: []
evidence: []
last_reviewed: "2026-08-07"
review_due: "2026-09-07"
supersedes: null
superseded_by: null
---

# StoneCharts Name Clearance Due Diligence

**Date:** 2026-08-07
**Controlling decision:** DEC-012
**Names searched:** "StoneCharts", "stonecharts", "stone-charts", "Stone Charts"

## Summary

The name "StoneCharts" is clear across package indexes, trademark registries,
and business entity databases. Two items require follow-up action:

1. The GitHub username `stonecharts` is occupied by an empty account created
   2026-07-18 — determine if this is an internal reservation.
2. The domain `stonecharts.com` is likely registered or parked — verify via
   registrar checkout and assess acquisition if held by a third party.

## Package Indexes

| Registry | Name | Status | Risk |
|---|---|---|---|
| PyPI | `stonecharts` | Not registered (HTTP 404) | Clear |
| PyPI | `stone-charts` | Not registered (HTTP 404) | Clear |
| npm | `stonecharts` | Not registered (HTTP 404) | Clear |
| npm | `stone-charts` | Not registered (HTTP 404) | Clear |
| pkg.go.dev | `stonecharts` | No module found | Clear |
| crates.io | `stonecharts` | Not registered | Clear |
| crates.io | `stone-charts` | Not registered | Clear |

**Action:** Consider registering placeholder packages on PyPI, npm, and
crates.io to secure the names while they are available.

## GitHub

| Resource | Status | Risk |
|---|---|---|
| User `stonecharts` | **Taken** — created 2026-07-18, 0 public repos, no activity | Moderate |
| User `stone-charts` | Available | Clear |
| Repo `StoneChart` (singular) | Exists — gemology reference PDF by `righthandabacus`, unrelated | Low |

The `stonecharts` GitHub account was created 2026-07-18 with no activity since.
If this is an internal reservation, no conflict exists. If it is external:

- Register `stone-charts` or `stonecharts-dev` as alternatives.
- File an inactive-name claim via GitHub support if the account remains dormant.

## Domains

| Domain | Status | Risk |
|---|---|---|
| `stonecharts.com` | Likely registered or parked (Sedo purchase offer detected) | Moderate–High |
| `stonecharts.dev` | WHOIS returned no data; likely available | Low |
| `stonecharts.io` | WHOIS returned no data; likely available | Low |

**Action:** Perform live registrar checkout for all three domains. Register
`.dev` and `.io` immediately if available. Assess `.com` acquisition cost if
held by a third party.

## Trademark

| Registry | Search terms | Result | Risk |
|---|---|---|---|
| USPTO (TESS) | "stonecharts", "stone charts" (Classes 9, 42) | No registration or pending application found | Clear |
| EUIPO | "stonecharts", "stone charts" | No registration found | Clear |
| WIPO Global Brand Database | "stonecharts", "stone charts" | No registration found | Clear |

**Nearest match:** "BEYOND CHARTS" by Stone Business Investments Pty Ltd
(USPTO Serial No. 79139693, filed 2013) — financial charting. The word "Stone"
appears only in the company name, not the trademark. No meaningful confusion risk.

**Action:** Confirm directly on `tmsearch.uspto.gov` before any filing decision.

## Business Entities

| Search | Result | Risk |
|---|---|---|
| OpenCorporates (global) | No results | Clear |
| U.S. Secretary of State filings | No results | Clear |
| General business search | No entity in software/technology sector | Clear |

Similar-sounding companies (StoneCo, StoneX, StoneRiver) are distinct names in
distinct segments. "Stonechart" is used descriptively by a gemstone jewelry
supplier for a product reference PDF — different industry, descriptive use.

## Recommended Actions

1. **Determine ownership of GitHub `stonecharts` account.** If internal, no
   action needed. If external, register `stone-charts` as a fallback.

2. **Register `stonecharts.dev` and `stonecharts.io`** via a registrar checkout
   to confirm availability and secure the names.

3. **Assess `stonecharts.com`.** Perform a registrar lookup. If parked,
   evaluate acquisition cost. If too expensive, proceed with `.dev` as the
   primary domain (consistent with the developer-tools positioning).

4. **Reserve package names** on PyPI (`stonecharts`), npm (`stonecharts`), and
   crates.io (`stonecharts`) with placeholder packages.

5. **Confirm USPTO all-clear** via direct `tmsearch.uspto.gov` search before
   public commercial use.

## Conclusion

The name "StoneCharts" has no trademark conflicts, no business-entity conflicts,
and no package-index conflicts. The two actionable items (GitHub username and
`.com` domain) are solvable. Once the actions above are completed, DEC-012's
name-clearance requirement can be resolved and the gated demo can be ungated to
a public site.
