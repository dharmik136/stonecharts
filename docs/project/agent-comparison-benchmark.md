---
id: SC-OPS-011
title: StoneCharts Agent Comparison Benchmark
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: all
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-19"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Agent Comparison Benchmark

## Purpose

StoneCharts can compare multiple orchestration runtimes against the same bounded
work item to evaluate consistency, traceability, and evidence quality.

This benchmark is for controlled comparison only. It does not waive checks, shorten
handoff requirements, or authorize a dangerous skip path.

## Benchmark task

Use the same input pack for every runtime:

- `docs/project/agent-orchestration.md`
- `docs/project/local-agent-model.md`
- `.agents/coordination.md`
- `.agents/state/handoff.md`
- `.agents/state/inventory.md`

Task:

1. Identify any mismatch between the local agent model, the cross-orchestrator
   contract, and the live coordination state.
2. State which files are authoritative for each mismatch.
3. Recommend the smallest governed correction.
4. Do not edit files unless the benchmark explicitly assigns a write task.

## Required output shape

Each runtime SHOULD return:

- claim
- evidence
- mismatch or confirmation
- recommended next action
- any blocked dependency

The answer MUST stay bounded to the supplied docs and state files.

## Evaluation criteria

The comparison is considered stronger when the runtime:

- identifies the same mismatches as the repo state
- preserves file-path traceability
- avoids inventing scope or approvals
- respects the branch and handoff rules
- states what is blocked instead of pretending it is complete

The comparison is considered weaker when the runtime:

- skips verification
- invents approval
- widens the task
- ignores branch ownership
- omits the evidence trail

## Intended use

This benchmark can be used to compare Codex, Antigravity, n8n-driven agents, or any
future runtime that needs to follow StoneCharts coordination rules.

All runtimes are judged against the same controlled source state and the same
verification expectations.
