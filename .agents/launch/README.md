# Agent Launch

Use these entrypoints to start a role-specific session against the StoneCharts repo.

## Rules

- Start from the role folder that matches the work.
- Read `AGENTS.md` and `.agents/coordination.md` first.
- Read `.agents/self-checks.md` before handoff.
- Claim the branch or worktree before editing.
- Do not mix roles inside one session unless the task is explicitly handoff-based.
- The launch files are for local CLI agents only; they do not create GitHub-visible
  collaborators.

## Roles

- `planner/`
- `stakeholder/`
- `developer/`
- `qa/`
- `security/`
- `compliance/`
- `release/`
- `notetaker/`

Each role folder contains a launch note with the exact docs to read and the kind of
work that role may own.

For serialized multi-agent runs, start with `tools/launch-coordinator.ps1` to write
the queue and print the role order.
