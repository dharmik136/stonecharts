# Coordination State

Use this directory for transient agent coordination records.

## Purpose

The files here are not product documentation. They are working notes that let multiple
agents coordinate branch ownership, handoffs, and review state.

## Suggested files

- `branch-lock.md`: current writer, branch or worktree, start time, and stop point.
- `handoff.md`: next owner, verified state, and required checks.
- `queue.md`: ordered pending agent tasks when work is serialized on one branch.
- `inventory.md`: append-only run log for launches, searches, edits, checks, and handoffs.
- `stakeholder.md`: routed stakeholder questions, responses, and planning follow-ups.
- `stage-0-review.md`: generated baseline review package for `WORK-S0-001` and
  `GATE-S0`.

## Rule

If a file here conflicts with the active repo state, the repo state wins and the
coordination note must be refreshed.
