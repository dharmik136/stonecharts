# Agent Coordination

This document controls how multiple agents work on StoneCharts without stepping on
each other.

## Core rule

Multiple agents may share the repository, but they must not share the same writable
branch or the same file set at the same time.

The roles are local CLI workers, not GitHub collaborators. Their permissions come
from the repo owner, the current checkout, and the handoff notes in this repository.

## Preferred topology

1. One coordinator agent owns the integration branch.
2. Each worker agent uses its own branch or git worktree.
3. The worker edits only the files listed in its handoff.
4. The worker records verification and returns a handoff note.
5. The coordinator merges only after the handoff is accepted.

## If you insist on one branch

Using the same branch for concurrent edits is a last resort and should be treated as a
serialized queue, not parallel work.

1. Only one agent may write at a time.
2. Other agents remain read-only until the lock is released.
3. The active owner writes the current claim into `.agents/state/branch-lock.md`.
4. The next agent checks that lock before editing.
5. If the lock is stale, the coordinator must reset the queue before anyone writes.

## Handoff record

Each handoff should include:

- Current branch or worktree name.
- Commit SHA or current working state.
- Files changed or approved for change.
- Verification already completed.
- Verification still required.
- Open issues, risks, or blockers.
- Self-check results or a link to the completed Socratic questions.

## Conflict handling

- If two agents want the same file, the coordinator decides the owner and serializes
  the work.
- If a code change and a docs change touch the same contract, the docs update happens
  in the same handoff or immediately after the implementation handoff.
- If a verification agent finds a mismatch, it returns the task to the owner rather
  than patching around the problem.

## Ownership lanes

- `planner`: `docs/project/`, `docs/product/`, backlog and decisions.
- `developer`: `charts/`, `libs/`, `runtime/`, `spec/`, and fixture updates.
- `qa`: test commands, golden checks, parity evidence, and failure reports.
- `security`: threat model, supply-chain checks, workflows, and execution boundaries.
- `compliance`: traceability, approvals, release readiness, and document status.
- `release`: manifests, changelog, versioning, and final ship evidence.
- `notetaker`: `.agents/state/inventory.md`, run summaries, and agent coordination notes.

## Visibility rule

- Do not encode role membership into GitHub collaborators unless the work actually
  requires remote repository access for a human owner.
- Keep the agent roster in local docs and transient state files.
- Publish only the code, docs, and evidence that are meant to live in the repo.
- The notetaker records launches and handoffs but does not own implementation files.
