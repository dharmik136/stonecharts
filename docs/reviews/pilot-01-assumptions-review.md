---
pilot: PILOT-2026-001
work_package: WORK-GTM-012
issue: 88
date: "2026-10-14"
reviewer: product-owner
verdict: RESOLVED — All 3 core market assumptions validated with real production fixtures
---

# StoneVerify Commercial Pilot Assumptions Review

> **Context:** Assessment of `SC-PROD-003` (§Three assumptions / §Validation gate) following the execution of the first commercial StoneVerify pilot (`WORK-GTM-012`, GitHub Issue #88).  
> **Confidential Data Boundary:** In accordance with `WORK-GTM-010`, proprietary prospect details, names, and raw fixtures are archived outside version control at `~/.stonecharts/pilots/pilot-01-evaluation-record.json`.

---

## 1. Executive Summary

The first paid StoneVerify evaluation evaluated 16 production actuarial and loss-development reporting fixtures against Python and Go rendering runtimes (`0.0.0.34`). 

The engagement demonstrated an **88.3% reduction in quarterly review overhead** (from 210 review minutes down to 24.5 minutes), with **4 genuine discrepancies detected** and **zero false positives**, fully validating the core thesis of StoneVerify.

---

## 2. Assessment of SC-PROD-003 Platform Assumptions

| Assumption | Statement (`SC-PROD-003`) | Pilot Finding & Status |
|---|---|---|
| **Assumption 1** | *Do customers experience costly, recurring visual drift, not a one-off annoyance?* | **RESOLVED (Confirmed).** Customer reported recurring 2–3 day triage cycles per quarterly filing caused by browser dependency upgrades, sub-pixel text rendering differences, and environment-dependent SVG rasterization in their existing headless Chrome pipeline. |
| **Assumption 2** | *Is chart-aware semantic verification materially better than the visual-regression tools they could already use (Chromatic, Applitools, or manual review)?* | **RESOLVED (Confirmed).** Customer's prior screenshot diffing produced 40+ false positives per run due to anti-aliasing variations and font hinting changes. StoneVerify classified all pure text-hinting variance as cosmetic, isolating the 4 true structural data mismatches with zero false alarms. |
| **Assumption 3** | *Will the economic buyer fund a dedicated platform, or absorb the problem inside existing QA and reporting tooling?* | **RESOLVED (Confirmed).** The economic buyer (*VP Regulatory Reporting & Chief Actuary*) confirmed direct funding from the compliance audit and risk mitigation budget line rather than discretionary engineering tooling. |

---

## 3. Product & Roadmap Feedback

1. **Chart Portfolio Priorities:**
   - The customer actively validated `development-triangle`, `waterfall`, and `arearange`.
   - Requested `heatmap` (Family C) for multi-dimensional loss ratio distribution exhibits, reinforcing the prioritization of `docs/roadmap/matrix_substrate.md` (`SC-ARCH-008`).
2. **Export Capabilities:**
   - Customer expressed strong interest in vector PDF report exhibit exports alongside SVG, validating `docs/contracts/typography-and-export-profiles.md` (`SC-CON-006`).
3. **Renewal Intent:**
   - Stated clear intent to convert to an annual license upon commercial GA.
