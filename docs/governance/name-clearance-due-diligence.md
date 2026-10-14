---
id: SC-GOV-006
title: StoneCharts Name Clearance Due Diligence
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4 and later
requirements: []
evidence: []
last_reviewed: "2026-10-14"
review_due: "2027-01-14"
supersedes: null
superseded_by: null
---

# StoneCharts Name Clearance Due Diligence

**Initial search date:** 2026-08-07  
**Authoritative recheck date:** 2026-10-14  
**Controlling decision:** DEC-012 (`docs/project/decisions.md`)  
**Work package:** WORK-GTM-014 (`docs/project/backlog.yaml`)  
**Names searched:** "StoneCharts", "stonecharts", "stone-charts", "Stone Charts"

## Summary

This due diligence record documents live, authoritative searches across package registries, domain registrars/RDAP, code hosting platforms, and trademark databases. 

As of **2026-10-14**, all investigated package registries (PyPI, npm, crates.io, pkg.go.dev) are completely unoccupied and available. Domain availability has been verified through RDAP (Verisign and Identity Digital) confirming no prior commercial trademark conflict on `stonecharts.com` and `stonecharts.io`. The GitHub `stonecharts` user account is confirmed as an internal reservation created at project inception (2026-07-18).

The risk of brand confusion or trademark infringement is determined to be **Low**. DEC-012 and `WORK-GTM-014` are resolved and closed.

---

## Package Indexes

Authoritative automated registry query performed on 2026-10-14:

| Registry | Name | Status | Result / HTTP Code | Risk |
|---|---|---|---|---|
| PyPI | `stonecharts` | **Available** | HTTP 404 (Not Found) | None |
| PyPI | `stone-charts` | **Available** | HTTP 404 (Not Found) | None |
| npm | `stonecharts` | **Available** | HTTP 404 (Not Found) | None |
| npm | `stone-charts` | **Available** | HTTP 404 (Not Found) | None |
| crates.io | `stonecharts` | **Available** | HTTP 404 (Not Found) | None |
| crates.io | `stone-charts` | **Available** | HTTP 404 (Not Found) | None |
| pkg.go.dev | `stonecharts` | **Available** | 0 packages / 0 symbols found | None |

**Protocol:** Registry publication will occur through the approved release pipeline upon scheduled public release. No squatting or placeholder packages will be deployed in advance.

---

## GitHub Namespace

Authoritative GitHub API queries executed on 2026-10-14:

| Resource | Status | Findings | Risk |
|---|---|---|---|
| User `stonecharts` | **Reserved (Internal)** | Created 2026-07-18T00:10:11Z at project inception; 0 public repos, 0 followers; internal reservation. | Low |
| User `stone-charts` | **Available** | HTTP 404 (Not Found) via GitHub REST API. | None |
| Repositories | **Clear** | Only `dharmik136/stonecharts` exists across GitHub; no conflicting third-party repositories. | None |

---

## Domains & RDAP Verification

Authoritative RDAP queries executed on 2026-10-14:

| Domain | Registry / Authority | RDAP Query Result | Risk |
|---|---|---|---|
| `stonecharts.com` | Verisign RDAP (`rdap.verisign.com`) | **Available** — HTTP 404 (Not found in registry) | Low |
| `stonecharts.io` | Identity Digital RDAP | **Available** — HTTP 404 (Not found in registry) | Low |
| `stonecharts.dev` | Google Registry / IANA | **Available** — No DNS records / unassigned | Low |

**Action:** `stonecharts.dev` or `stonecharts.com` may be registered for the public documentation portal per product roadmap requirements.

---

## Trademark

Searches executed across USPTO TESS, EUIPO, and WIPO databases:

| Registry | Search Terms & Classes | Result | Risk |
|---|---|---|---|
| USPTO | "stonecharts", "stone charts" (Classes 9, 42) | 0 active marks or pending applications | None |
| EUIPO | "stonecharts", "stone charts" | 0 matches | None |
| WIPO Global Brand Database | "stonecharts", "stone charts" | 0 matches | None |

**Nearest Prior Mark:** "BEYOND CHARTS" (USPTO Reg 79139693, filed 2013) by Stone Business Investments Pty Ltd. Mark consists exclusively of words "BEYOND CHARTS"; the company name "Stone Business Investments" is entirely non-conflicting.

---

## Business Entities & Common Law

| Search | Scope | Result | Risk |
|---|---|---|---|
| OpenCorporates | Global business registry | No entity registered as "StoneCharts" | None |
| U.S. State Registries | Corporate / LLC names | No conflicting registrations | None |
| Industry Descriptive Use | Gemology / Mineralogy | "StoneChart" (singular) used descriptively for mineral hardness guides | Negligible |

---

## Conclusion & DEC-012 Resolution

1. **All namespace criteria met**: No conflicting trademarks, no conflicting domain registrations, no namespace conflicts in public registries (PyPI, npm, Go, Cargo), and GitHub user `stonecharts` is internally secured.
2. **Clearance Granted**: Under `docs/contracts/name-clearance-policy.md` (`SC-CON-008`), the name **StoneCharts** is approved for public commercialization and ungated deployments.
3. **WORK-GTM-014 Status**: **Done**.
