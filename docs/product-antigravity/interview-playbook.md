---
id: SC-PROD-006-ANTIGRAVITY
title: StoneCharts Customer Discovery & Objection Handling Playbook
status: superseded
classification: informative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: Post-0.0.0.1
requirements: []
evidence: []
last_reviewed: "2026-07-30"
review_due: "2027-07-30"
supersedes: null
superseded_by: SC-PROD-006
---

# Customer Discovery & Objection Playbook

> [!WARNING]
> Superseded research artifact - not an approved product commitment. The approved
> post-0.0.0.4 direction is governed by
> `docs/product/visual-integrity-strategy.md`,
> `docs/product/capability-matrix.md`, and DEC-017.

This playbook maps target personas, structures competitive objection handling, and establishes a rubric for evaluating customer interview signals during the post-0.0.0.1 validation campaign.

---

## 1. Key Buyer Personas & Core Pain Points

We must speak to different organizational stakeholders by translating technical deterministic rendering into their specific language of cost, security, or consistency.

### A. The Platform / Infrastructure Architect
* **Primary Care**: System complexity, execution performance, dependency bloat, container image sizes.
* **Core Pain**: Running Puppeteer/Playwright in production containers increases container sizes, bloats memory overhead, and exposes the cluster to headless browser security CVEs.
* **StoneCharts Value**: Native Python/Go runtimes, no browser daemon, zero sandbox dependencies, minimal memory footprint.

### B. The Audit & Compliance Director
* **Primary Care**: Traceability, repeatability, regulatory reporting accuracy.
* **Core Pain**: Financial or clinical reports must look identical to historical versions. Chart drift between a Python data science notebook and Go production server results in audit defects.
* **StoneCharts Value**: Byte-identical SVG output guarantees that a chart rendered on any server platform is identical, traceable, and version-controlled.

### C. The Embedded Analytics Product Manager
* **Primary Care**: White-labeling, brand consistency, on-premise export support.
* **Core Pain**: Customers exporting dashboards to PDF complain when fonts break, legends overflow, or layouts shift during print rendering.
* **StoneCharts Value**: Governed themes, manual layout validation, certified export pipelines, and offline-resilient execution.

---

## 2. Competitive Objection Handling

When interviewing prospective buyers, they will raise existing alternatives. Use these positioning rebuttals:

### Objection 1: "We already use Vega / Vega-Lite for declarative charts."
* **Rebuttal**: Vega is excellent for flexible visual exploration. However, server-side SVG generation in Vega requires running a Node.js daemon (or v8 engine) to evaluate the specification. If your backend service is Go or Python, this introduces a heavy, cross-language inter-process dependency. StoneCharts renders natively in Go or Python with zero JS engine requirements.
* **Follow-up question**: *"How do your Go/Python microservices currently interface with Vega, and what is the overhead of running that JavaScript engine?"*

### Objection 2: "We run a Highcharts Export Server in a separate container."
* **Rebuttal**: Highcharts offers rich charts, but their export server is basically a Node app running headless Chromium via Puppeteer. If your security team flags Chromium vulnerabilities or your platform team is trying to trim container cold-starts, that architecture represents a major liability. StoneCharts replaces that entire container infrastructure with a lightweight, native library import.
* **Follow-up question**: *"How often does your security team audit the Chromium version in your reporting containers, and what is the memory footprint of that service?"*

### Objection 3: "We just call a hosted QuickChart API endpoint to get image charts."
* **Rebuttal**: QuickChart is highly convenient, but in regulated domains (healthcare, banking, defense), sending raw customer data to an external third-party API for rendering violates data governance policies. StoneCharts runs completely locally, on-premise, or in air-gapped environments without any network egress.
* **Follow-up question**: *"Are there data privacy rules that restrict you from sending sensitive user metrics to external third-party chart APIs?"*

---

## 3. Customer Signal Evaluation Rubric

Use this matrix to classify qualitative feedback from discovery interviews:

| Signal Strength | Customer Response Pattern | Strategic Action |
| :--- | :--- | :--- |
| **Strong Positive (Buy/Pilot)** | *"We are trying to remove Puppeteer from our reporting service right now because it keeps crashing."* or *"We maintain separate chart code in Python and JS and they drift."* | Immediate trial offer with the **Deterministic Reporting SDK**. Ask for their current chart JSON configurations. |
| **Neutral (Interested but Low Priority)** | *"We have visual drift, but it hasn't caused client complaints yet."* or *"Node/Chromium works fine, but we'd look at alternatives if memory usage became an issue."* | Place on the newsletter list. Follow up with benchmarks demonstrating resource savings and security benefits. |
| **Negative (Poor Fit)** | *"We need highly interactive, 3D animated dashboards in the browser."* or *"We only write Node.js microservices."* | Disqualify immediately. Do not spend sales or engineering resources trying to win general-purpose front-end analytics teams. |
