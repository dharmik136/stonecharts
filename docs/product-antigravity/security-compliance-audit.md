---
id: SC-PROD-007-ANTIGRAVITY
title: StoneCharts Security & Compliance Audit (Antigravity Version)
status: superseded
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-SEC-001, REQ-VAL-001, REQ-CAP-001]
evidence: []
last_reviewed: "2026-07-30"
review_due: "2027-07-30"
supersedes: null
superseded_by: SC-SEC-001
---

# Security & Compliance Audit

> [!WARNING]
> Superseded research artifact - not an approved product commitment. The approved
> post-0.0.0.4 direction is governed by
> `docs/product/visual-integrity-strategy.md`,
> `docs/product/capability-matrix.md`, and DEC-017.

This audit evaluates the StoneCharts Antigravity product documents against the core security policies in [threat-model.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/security/threat-model.md) and governance risks in [risk-register.yaml](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/governance/risk-register.yaml). The objective is to identify compliance gaps, scope discrepancies, and technical risk vectors that must be resolved prior to the `0.0.0.1` pilot release.

---

## 1. Document Scope and References

The following documents were audited:
1. **Thesis**: [thesis.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/thesis.md) (`SC-PROD-001-ANTIGRAVITY`)
2. **Scope**: [positioning-and-scope.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/positioning-and-scope.md) (`SC-PROD-002-ANTIGRAVITY`)
3. **Validation**: [validation-plan.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/validation-plan.md) (`SC-PROD-003-ANTIGRAVITY`)
4. **Integration**: [pilot-integration-guide.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pilot-integration-guide.md) (`SC-PROD-004-ANTIGRAVITY`)
5. **Pricing**: [pricing-and-packaging.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pricing-and-packaging.md) (`SC-PROD-005-ANTIGRAVITY`)
6. **Playbook**: [interview-playbook.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/interview-playbook.md) (`SC-PROD-006-ANTIGRAVITY`)

Against the baseline governing frameworks:
- **Threat Model**: [threat-model.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/security/threat-model.md) (`SC-SEC-001`)
- **Risk Register**: [risk-register.yaml](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/governance/risk-register.yaml) (`SC-GOV-003`)

---

## 2. High-Level Compliance Mapping

| Product Document | Threat Model Coverage / Gaps | Risk Register Coverage / Gaps | Compliance Status |
| :--- | :--- | :--- | :--- |
| **Thesis** | Aligned with basic static-first & cross-language rules. | Mentions byte-parity oracle limits. | **Compliant** |
| **Scope** | Discrepancy on supported chart types (includes `area`). | Fails to outline render limits required for SaaS. | **Minor Gaps** |
| **Validation** | Mentions PDF conversion without security guidelines. | Discrepancy: includes `scatter` and `bar` in pilot. | **Major Gaps** |
| **Integration** | Critically exposes SSRF in downstream converter (`weasyprint`). | Example code lacks broad exception catching. | **Critical Gaps** |
| **Pricing** | Gates SBOM and security audits behind paid tiers. | Conflicts with the public distribution requirements. | **Minor Gaps** |
| **Playbook** | Highlights local execution but ignores runtime data risks. | Aligned with basic competitor positioning. | **Compliant** |

---

## 3. Critical Gaps & Risk Vectors

### Gap 1: Downstream PDF Exporter Security (SSRF/XXE/LFI)
* **Target File**: [pilot-integration-guide.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pilot-integration-guide.md) & [validation-plan.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/validation-plan.md)
* **Governing Rule**: `threat-model.md` - *Malicious downstream converter* threat ("Certified exporters will be pinned. Arbitrary converters remain outside guarantees").
* **Description**: 
  Section 5 of the [pilot-integration-guide.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pilot-integration-guide.md) instructs pilot developers to use `weasyprint` to compile charts and HTML directly to PDF:
  ```bash
  weasyprint report.html q3_report.pdf
  ```
  By default, `weasyprint` resolves external URLs (such as CSS `@import` or `<img src="...">` inside the HTML/SVG spec) and local files. If the input contains malicious links, an attacker could trigger Server-Side Request Forgery (SSRF) or Local File Inclusion (LFI). The integration guide contains no warning or instructions on how to disable network resource fetching or restrict file system access.
* **Remediation**: 
  - Update the [pilot-integration-guide.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pilot-integration-guide.md) to explicitly warn users that downstream PDF tools must be sandboxed.
  - Provide a safe execution model (e.g., using Weasyprint's URL fetcher redirection API to drop non-local or non-embedded assets).

### Gap 2: Chart Type Support Discrepancies
* **Target File**: All Product Documents
* **Governing Rule**: `risk-register.yaml` - `RISK-001` (Released schema overstates renderer support) & `RISK-003` (Accepted input can panic or throw during dispatch).
* **Description**:
  There are major contradictions regarding the supported chart types for version `0.0.0.1`:
  - **Thesis** ([thesis.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/thesis.md)): States only `line` and `column` are active.
  - **Scope** ([positioning-and-scope.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/positioning-and-scope.md)): States user outcomes include `line`, `column`, `bar`, or `area`, but the "In Scope" section lists `line`, `column`, and `area` (excluding `bar`).
  - **Validation** ([validation-plan.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/validation-plan.md)): Lists `Line`, `Bar`, `Column`, `Area`, and `Scatter` for the pilot.
  This mismatch directly exposes the platform to `RISK-003` (unsupported chart types passing validation and throwing Go panics or Python exceptions).
* **Remediation**:
  Align all documents to state that only `line` and `column` are supported for the `0.0.0.1` pilot release. Explicitly mark `bar`, `area`, and `scatter` as post-pilot roadmap items (aligned with `Post-0.0.0.1` tags).

### Gap 3: Absence of Render Limits and DoS Controls
* **Target File**: [positioning-and-scope.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/positioning-and-scope.md) & [pilot-integration-guide.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pilot-integration-guide.md)
* **Governing Rule**: `threat-model.md` - *Denial of service* threat & Security Rules ("Render limits for dimensions, series, points, string lengths, and nested style objects must be defined before untrusted multi-tenant service use").
* **Description**:
  The [pricing-and-packaging.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pricing-and-packaging.md) document offers "Embedded Analytics (Redistribution)" which allows software vendors to embed the SDK in multi-tenant SaaS environments. However, none of the product guides declare or enforce limits on spec inputs. Without default bounds (e.g. max series count, dimension caps), an application embedding the SDK is vulnerable to memory exhaustion or process panics.
* **Remediation**:
  - Define default thresholds in the JSON schema (e.g., maximum dimensions of 4096x4096px, limit series to 50, data points per series to 1000, and category string lengths to 256 characters).
  - Explicitly document these limits in the [positioning-and-scope.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/positioning-and-scope.md) limits boundary.

### Gap 4: Text Measurement, Font Dependencies, and Pixel Drift
* **Target File**: [pilot-integration-guide.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pilot-integration-guide.md)
* **Governing Rule**: `risk-register.yaml` - `RISK-006` (Unicode legend geometry differs by language) & `RISK-011` (Byte identity may be misrepresented as pixel identity).
* **Description**:
  The [pilot-integration-guide.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pilot-integration-guide.md) contains an example spec using standard ASCII English words. In production, users will pass Unicode characters. Because Go (byte length) and Python (code-point length) measure Unicode string geometries differently, layout coordinates for legends and labels will drift, breaking byte parity. Furthermore, font dependencies on the rendering machine can lead to clipped text in Weasyprint.
* **Remediation**:
  - Insert a "Text Geometry and Font Considerations" section in the integration guide.
  - Warn developers to configure manual margins when using long labels or non-ASCII characters to prevent differences in label wrapping.

### Gap 5: Supply Chain SBOM Licensing Discrepancy
* **Target File**: [pricing-and-packaging.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pricing-and-packaging.md)
* **Governing Rule**: `risk-register.yaml` - `RISK-012` (Release provenance is not yet reproducible. Mitigation: Build the 0.0.0.1 evidence pack and supply-chain workflow before public distribution).
* **Description**:
  The mitigation for `RISK-012` requires building an SBOM and release workflow before *any* public distribution (including the open-source community release). However, the [pricing-and-packaging.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pricing-and-packaging.md) gates "SBOM exports" and "vulnerability audits" behind the paid Enterprise tier. This commercial separation compromises the supply chain trust promise for the community edition.
* **Remediation**:
  Clarify that basic SBOM manifests and package cryptographic hashes are generated for all public releases as part of the core open-source provenance pipeline, while advanced features like compliance auditing and FIPS validation remain enterprise-only.

### Gap 6: Fault Tolerance and Error Catching in Python Code
* **Target File**: [pilot-integration-guide.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pilot-integration-guide.md)
* **Governing Rule**: `risk-register.yaml` - `RISK-003` (Accepted input can panic or throw during dispatch).
* **Description**:
  The Python rendering snippet in the pilot guide catches only `SpecError` and `CapabilityError`:
  ```python
  except (SpecError, CapabilityError) as e:
  ```
  If the renderer throws a generic exception (e.g. an `IndexError` or `ValueError` due to a layout bug or mismatched category sizes, see `RISK-010`), the process will crash with an unhandled exception rather than returning a clean error.
* **Remediation**:
  Update the snippet in [pilot-integration-guide.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pilot-integration-guide.md) to catch general exceptions gracefully:
  ```python
  except Exception as e:
      print(f"[Python] Unexpected rendering error: {e}", file=sys.stderr)
      sys.exit(1)
  ```

---

## 4. Remediation Checklist for 0.0.0.1

- [x] **Chart Type Alignment**: Update [positioning-and-scope.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/positioning-and-scope.md) and [validation-plan.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/validation-plan.md) to explicitly restrict `0.0.0.1` scope to `line` and `column` charts.
- [x] **PDF Security Warnings**: Add security disclaimers and sandboxing configurations for Weasyprint/PDF rendering in the [pilot-integration-guide.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pilot-integration-guide.md).
- [x] **Input Bounds Definition**: Update the positioning and integration guides to detail the maximum data limits and dimensions.
- [x] **Python Code Update**: Fix the try-catch block in [pilot-integration-guide.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pilot-integration-guide.md) to catch generic exceptions.
- [x] **SBOM Transparency**: Re-align [pricing-and-packaging.md](file:///C:/Users/Dharmik%20Shingala/stonecharts/docs/product-antigravity/pricing-and-packaging.md) to ensure basic build hashes/SBOM are public, preserving the core security thesis.
