# StoneCharts Agent Guide

This repository is governed by the Stage 0 product and project documents. Treat this
file as the root operating guide for Codex-compatible agents and other terminal-based
tools.

## Read first

Before making changes, read the documents that define current scope and control:

1. `docs/project/README.md`
2. `docs/project/stage-0.md`
3. `docs/project/backlog.yaml`
4. `docs/project/decisions.md`
5. `docs/product/thesis.md`
6. `docs/product/positioning-and-scope.md`
7. `CHARTS.md`
8. `.agents/self-checks.md`
9. The relevant chart `design.md`, `spec/chart-spec.schema.json`, `spec/svg-contract.md`,
   and `runtime/chart-interactions.js` for the task at hand

## Working rules

- Follow the governed backlog and stage gate order.
- Do not widen chart scope, language scope, or release claims unless the relevant
  decision or requirement is approved first.
- Keep byte-parity work deterministic. Do not regenerate goldens unless the change
  being made explicitly requires new fixtures.
- Use `apply_patch` for manual file edits.
- Prefer small, reviewable changes that match the existing repository structure.
- Run the smallest relevant checks first, then broader checks when the change crosses
  code, docs, schema, or runtime boundaries.
- If a task touches release, project, or contract documents, verify the corresponding
  backlog and traceability entries as part of the work.

## Response discipline

- Speak plainly and keep answers bounded.
- Separate facts, verification, and recommendation.
- Use exact dates, branch names, file paths, and decision IDs when they matter.
- Do not imply certainty the repo does not support.
- If an agent role is speaking, keep that role's voice consistent with
  `.agents/agents.md`.

## Multi-agent operation

- The local agent team is private and CLI-only. Do not treat worker roles as GitHub
  collaborators or as a substitute for repo permissions.
- Agents coordinate through repo artifacts, not through ad hoc user prompts between
  every step. They may continue work, hand off, and adjust their path from the
  recorded state as long as the current scope, approvals, and branch ownership stay
  within the governed model.
- Prefer one writable git worktree or branch per active agent.
- Do not let two agents write to the same branch at the same time.
- If branch sharing is unavoidable, one coordinator owns writes and all others work
  read-only until the coordinator grants a handoff.
- Record the active owner, intended files, and stop point in the coordination state
  before editing.
- Use the branch lock, handoff note, and inventory log as the live communication
  surface between agents.
- Keep file ownership narrow. An agent should not cross into unrelated files unless
  the handoff explicitly includes them.
- Merge only after the owning agent has recorded verification evidence and the next
  agent has accepted the handoff.
- Every agent must complete the Socratic self-checks before handoff.

## Handoff protocol

Every handoff between agents should answer these questions:

1. What is the next bounded outcome?
2. Which files are safe to touch?
3. Which checks must pass before the next handoff?
4. What is the current commit or working state?
5. What is blocked, deferred, or intentionally left out?

## Baseline checks

Use the relevant checks for the area being changed:

- `python tools/check_docs.py`
- `python tools/check_github_project.py`
- `python -m pytest libs/python/tests -q`
- `go test ./...` from `libs/go`
- `node --check runtime/chart-interactions.js`

## Agent roles

When splitting work across multiple agents, use the following default roles:

- `planner`: converts requests into scope, backlog items, decisions, and release gates.
- `stakeholder`: carries agent outputs into stakeholder discussion and routes
  feedback back to planning.
- `developer`: implements approved code, schema, runtime, and fixture changes.
- `qa`: runs verification, compares outputs, and reports regressions.
- `security`: reviews attack surface, supply chain, execution boundaries, and secrets.
- `compliance`: checks traceability, approvals, documentation status, and release evidence.
- `release`: assembles the release manifest, evidence pack, and final ship checklist.
- `notetaker`: maintains the running inventory of launches, searches, edits, checks,
  and handoffs.

The normal flow is `planner` -> `stakeholder` -> `developer` -> `qa` -> `compliance`
-> `security` when the task is release-adjacent. `notetaker` runs alongside or after
the active roles to record what happened. `release` only begins after the required
checks and approvals are already recorded.

The flow is continuous, not one-shot: once a role finishes its bounded outcome, the
next role may pick up from the recorded handoff without asking the human to restate
the whole task. The human only needs to re-enter when scope, approvals, or release
claims must change.

## Coordination rules

- One agent owns one bounded outcome.
- Reviewers do not merge unverified changes.
- Release work waits for the required decision and requirement approvals.
- Human approval is required before any change that alters product scope or release
  claims.
