---
id: SC-QUAL-005
title: StoneVerify Commercial Pilot Evaluation Protocol
status: approved
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.4 and later
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-10-14"
review_due: "2027-01-14"
supersedes: null
superseded_by: null
---

# StoneVerify Commercial Pilot Evaluation Protocol

> **Location:** `docs/quality/pilot-evaluation-protocol.md`  
> **Controlling Work Package:** WORK-GTM-012 (Issue #88)  
> **Controlling Strategy:** SC-PROD-003 (Visual Integrity Strategy) & SC-CON-020 (Commercial Terms Policy)

---

## 1. Purpose & Scope

This protocol establishes the standardized measurement framework for executing and evaluating commercial StoneVerify pilots with external design partners and prospective enterprise customers.

In accordance with `WORK-GTM-012` and `WORK-GTM-010`:
- **Real Customer Confidentiality:** Actual customer identity, proprietary spec fixtures, financial terms, and interview responses MUST reside strictly outside git-tracked repositories (e.g. in secured local storage at `~/.stonecharts/pilots/` or authorized CRM repositories).
- **Reusable Market Evidence:** Quantitative outcomes (time savings, false positive reduction, drift detection efficacy) and qualitative buyer objections MUST be captured in a structured format to resolve key platform hypotheses in `SC-PROD-003`.

---

## 2. Quantitative Metric Protocol

Every pilot evaluation measures seven canonical operational metrics comparing the customer's pre-pilot baseline with StoneVerify-assisted review:

| Metric Identifier | Metric Name | Definition & Measurement Unit | Target Hypothesis |
|---|---|---|---|
| `M-SETUP-TIME` | **Baseline Setup Time** | Hours required to import customer specs, validate against schema, and generate initial baseline hashes. | $< 4.0$ hours |
| `M-REVIEW-PRE` | **Review Time (Pre-StoneVerify)** | Minutes spent per release reviewing chart outputs visually or with generic pixel diffs. | Customer baseline ($15\text{--}60\text{ min/chart}$) |
| `M-REVIEW-POST` | **Review Time (With StoneVerify)** | Minutes spent inspecting StoneVerify HTML diff reports and finding classifications. | $\ge 80\%$ reduction ($< 3\text{ min/chart}$) |
| `M-TRUE-DIFFS` | **True Differences Detected** | Count of real rendering regressions or intentional visual changes correctly highlighted. | High sensitivity ($100\%$) |
| `M-FALSE-POS` | **False-Positive Count** | Count of cosmetic, non-functional differences (e.g., insignificant text metrics, anti-aliasing variations) flagged as errors. | Zero false positives ($0$) |
| `M-UNEXPLAINED` | **Unexplained Differences** | Count of differences where semantic classification was inconclusive or ambiguous. | Zero unexplained ($0$) |
| `M-COVERAGE` | **Fixture Count** | Number of unique customer report fixtures and charts evaluated during the pilot period. | $\ge 10$ production fixtures |

---

## 3. Commercial & Qualitative Capture Protocol

The evaluation record captures essential buyer and organizational dynamics:

1. **Economic Buyer & Budget Owner:**
   - Role / Title (e.g., *VP of Actuarial Technology*, *Head of Regulatory Reporting*, *Director of Engineering*).
   - Funding Source (e.g., *Central Compliance Budget*, *Release Tooling Budget*, *Departmental Software Discretionary*).
2. **Renewal & Conversion Signal:**
   - Explicit willingness to convert to an annual license upon pilot conclusion (Yes / Conditional / No).
   - Primary driver for conversion (e.g., *audit defense assurance*, *elimination of manual sign-off delay*).
3. **Primary Objections:**
   - Categorized objection: *Pricing*, *Hosting / Deployment*, *Unsupported Chart Type*, *Unsupported Runtime (e.g., JVM/Rust)*.
4. **Scope Expansion Requests:**
   - Newly requested chart types (e.g., *Heatmap*, *Treemap*, *Waterfall*).
   - Newly requested language runtimes (e.g., *Java/Kotlin*, *TypeScript SSR*, *C# / .NET*).

---

## 4. Standard Schema for External Pilot Records

External pilot records stored outside version control adhere to the following canonical JSON schema:

```json
{
  "$schema": "https://stonecharts.dev/schemas/pilot-record.schema.json",
  "pilotId": "PILOT-2026-001",
  "organizationAlias": "Prospect-InsureCorp",
  "evaluationDate": "2026-10-14",
  "toolVersion": "0.0.0.34",
  "operationalMetrics": {
    "fixturesEvaluated": 14,
    "baselineSetupHours": 2.5,
    "reviewMinutesPreStoneVerify": 240.0,
    "reviewMinutesWithStoneVerify": 28.0,
    "timeSavingsPercentage": 88.3,
    "trueDifferencesDetected": 3,
    "falsePositiveCount": 0,
    "unexplainedDifferenceCount": 0
  },
  "commercialFindings": {
    "buyerTitle": "Head of Enterprise Actuarial Systems",
    "budgetOwnerTitle": "VP of Regulatory Compliance",
    "budgetSource": "Quarterly Financial Reporting Integrity Budget",
    "statedWillingnessToRenew": "Yes",
    "strongestObjectionRaised": "Requires export to vector PDF exhibits in addition to SVG",
    "requestedChartTypes": ["development-triangle", "waterfall", "heatmap"],
    "requestedRuntimes": ["Python", "Go"]
  },
  "assumptionsResolved": {
    "recurringDriftCost": "Confirmed — customer lost 18 engineering hours last quarter investigating anti-aliasing false alarms in headless Chrome",
    "semanticVerificationSuperiority": "Confirmed — eliminated 100% of false positives caused by font metric differences",
    "budgetAvailability": "Confirmed — funded from compliance risk mitigation line item"
  }
}
```
