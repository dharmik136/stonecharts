---
id: SC-REL-036
title: StoneCharts 0.0.0.34 Package Install Matrix
status: approved
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.34
requirements: [REQ-REL-001]
evidence: [TEST-PACKAGE-INSTALL]
last_reviewed: "2026-08-24"
review_due: "2026-09-24"
supersedes: null
superseded_by: null
---

# Package/install matrix — 0.0.0.34 rc.1

| Surface | Version | Qualification |
|---|---:|---|
| Python wheel | `0.0.0.34` | Isolated install; SVG and interactive HTML smoke for all 36 charts |
| Python source distribution | `0.0.0.34` | Archive content and license inspection |
| Go source module | `0.0.0.34` runtime metadata | Full Go suite; embedded runtime asset; no external module publication |
| Released schemas | `0.0.0.34` | Immutable snapshot and SHA-256 manifest verification |

The wheel and source archive are retained as local release evidence. Upload to a
package registry or another distribution channel is not authorized by this matrix.
