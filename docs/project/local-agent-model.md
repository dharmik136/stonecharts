---
id: SC-OPS-009
title: StoneCharts Local Agent Operating Model
status: proposed
classification: normative
owner: product-owner
approver: maintainer
review_mode: self
applies_to: all
requirements: []
evidence: [TEST-DOCS-CONTROL]
last_reviewed: "2026-07-18"
review_due: "2026-09-18"
supersedes: null
superseded_by: null
---

# Local Agent Operating Model

## Purpose

StoneCharts uses local CLI agents as private, role-scoped workers. They are not GitHub
collaborators, not visible as separate repo users, and not a substitute for the
governed project or release process.

This model exists to coordinate work safely when several terminal sessions operate in
the same repository.
It is designed for continuous operation: one role can finish, record its handoff, and
the next role can continue from the recorded state without the human restating the
entire plan.

## Operating principles

1. One human owns the repo and the integration path.
2. Each agent owns one bounded role and one bounded outcome.
3. Each write-capable agent uses its own branch or git worktree.
4. Shared repo files are read-only unless the handoff explicitly authorizes edits.
5. The coordinator serializes merges when two agents need the same surface.
6. No agent invents scope, approvals, or release claims.
7. Agents communicate through repo state files, branch locks, handoff notes, and the
   inventory log.
8. Human intervention is required only for scope changes, approval decisions, or
   blockers that cannot be resolved from the recorded state.

## Role lanes

- `planner`: project docs, decisions, backlog, work splits, and release gates.
- `stakeholder`: stakeholder-facing feedback capture, routing, and traceability.
- `developer`: implementation files, fixtures, and narrow contract-adjacent tests.
- `qa`: verification commands, parity evidence, and regression reporting.
- `security`: trust boundaries, workflow risk, dependency risk, and mitigation notes.
- `compliance`: traceability, approvals, status drift, and release readiness.
- `release`: manifests, evidence packs, versioning, and final ship checks.
- `notetaker`: inventory logs, launch summaries, and coordination drift notes.

## Branch and worktree rules

- Prefer one writable branch or worktree per active agent.
- Never let two agents write to the same branch at the same time.
- If branch sharing is unavoidable, treat the branch as a serialized queue.
- Record the active owner, branch or worktree, intended files, and stop point before
  editing.
- Keep file ownership narrow and explicit.

## Handoff rules

A handoff is valid only when the current agent records:

- next owner
- bounded outcome
- files safe to touch
- checks already completed
- checks still required
- current commit or working state
- blockers, deferrals, and intentional exclusions
- Socratic self-check results
- a next-step note that lets the following agent continue without rebriefing

The next agent may not widen the handoff without explicit coordinator approval.

## Review gates

1. Planner defines the work.
2. Developer implements only the handed-off scope.
3. QA confirms the exact change with evidence.
4. Compliance checks status, traceability, and release readiness.
5. Security checks the attack surface and workflow boundaries.
6. Release assembles evidence only after the earlier gates pass.

## Continuous loop

The intended operating pattern is a loop, not a single pass:

1. Planner writes the bounded outcome and file ownership.
2. Developer implements within the handed-off scope.
3. QA and compliance verify against the recorded evidence.
4. Security reviews the surface when the change affects execution, workflow, or
   external interaction.
5. Notetaker records what changed and what remains.
6. The coordinator hands the next bounded outcome to the next role.

This can run concurrently when file ownership is disjoint and serially when one branch
must carry the work. In both cases, the repo state is the source of truth.

If StoneCharts is being coordinated through an external orchestrator such as n8n or a
different agent runtime, the shared contract in
[`agent-orchestration.md`](agent-orchestration.md) still applies. The transport may
change; the task schema, handoff format, stop/resume semantics, evidence logging, and
branch-lock rules do not.

## Non-goals

- No GitHub collaborator visibility for the local agent roles.
- No direct merge authority for worker agents.
- No informal approval by activity alone.
- No cross-role editing without a recorded handoff.
- No stakeholder role approval of scope or technical changes.
- No note-taker edits to implementation files.
