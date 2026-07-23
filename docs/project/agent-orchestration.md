---
id: SC-OPS-010
title: StoneCharts Cross-Orchestrator Agent Contract
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

# Cross-Orchestrator Agent Contract

## Purpose

StoneCharts may be coordinated by multiple execution surfaces, including local CLI
agents, n8n-style workflow automation, and alternate agent runtimes. These surfaces
may differ in UI and transport, but they must share one contract for work intake,
handoff, evidence, and branch ownership.

This document defines the shared contract. It does not authorize new product scope,
new release claims, or remote repository access.

## Contract scope

All orchestrators MUST use the same:

1. task schema
2. handoff format
3. stop and resume semantics
4. evidence logging format
5. branch and lock rules

If an orchestrator cannot honor one of these rules, it may not own write-capable work
for StoneCharts.

## Task schema

Each task record MUST carry:

| Field | Meaning |
|---|---|
| Task ID | Stable identifier for the work item |
| Role | Planner, developer, QA, security, compliance, release, stakeholder, or notetaker |
| Owner | Current writable agent or coordinator |
| State | Inbox, active, blocked, paused, complete, or handed off |
| Branch | Current branch or worktree name |
| Scope | Exact files or document paths allowed for the task |
| Inputs | Source docs, evidence, or prior handoff state |
| Outputs | Expected artifact, change, or verification result |
| Checks | Required commands or review steps |
| Evidence | Files or records proving the task outcome |
| Stop point | Where the current agent must stop |

The schema MAY be carried in a sheet, database row, queue payload, YAML record, or
another durable store, but the fields above remain required.

## Handoff format

Every handoff MUST answer the following:

1. What is the next bounded outcome?
2. Which files or records are safe to touch?
3. Which checks must pass before the next handoff?
4. What is the current commit, branch, or working state?
5. What is blocked, deferred, or intentionally left out?

The handoff SHOULD be written back to the shared state store before the next agent
starts. The human may read it directly, but the next machine agent should not need a
fresh verbal restatement.

## Stop and resume semantics

An agent MUST stop when one of the following occurs:

- token or budget limit reached
- required check fails
- scope boundary reached
- branch lock is held by another writer
- the next decision belongs to a different role

When stopping, the agent MUST persist:

- current task state
- latest commit or repo state
- completed checks
- unfinished checks
- blocker or pause reason
- next owner

Resume MUST continue from the saved state, not from a new interpretation of the task.
If the runtime changes, the saved task state remains authoritative.

## Evidence logging

Every significant step MUST be logged in the inventory or equivalent audit trail with:

- timestamp
- role
- action
- scope
- verification
- repo state or commit reference

Evidence records MUST be append-only where practical. If a record is corrected, the
correction SHOULD preserve the original record and name the replacement.

## Branch and lock rules

The same write branch MUST NOT be edited by two agents at once.

Required controls:

- one active writer per branch
- explicit branch-lock record
- narrow file ownership
- no cross-role editing without a recorded handoff
- coordinator approval before lock transfer if scopes overlap

If a token budget expires while a lock is held, the agent must release the lock in the
state file before the workflow pauses.

## Orchestrator expectations

- Local CLI agents may own repo work only through the recorded handoff model.
- n8n may route and retry tasks, but it does not replace the repo records.
- Alternate runtimes, including Antigravity, must respect the same task schema and
  lock model before they are allowed to write.
- A human-visible sheet may act as a dashboard, but not as the only source of truth.

## Non-goals

- No direct GitHub collaborator model for private worker agents.
- No parallel writes on one branch.
- No implicit completion when a runtime stops.
- No release claim from orchestration alone.
- No bypass of the governed backlog or review gates.
