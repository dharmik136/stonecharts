# Collaboration Cycle

## Description

Use this workflow when multiple agents are active on the same repository.

## Steps

1. The coordinator writes or updates `.agents/state/branch-lock.md`.
2. The active agent reads `AGENTS.md`, `.agents/coordination.md`, and the relevant
   project docs.
3. The active agent runs the Socratic self-checks for its role.
4. The active agent edits only the files named in the lock.
5. The active agent records verification results in `.agents/state/handoff.md`.
6. The coordinator accepts the handoff or returns it for fixes.
7. The next agent only begins after the handoff is accepted.
8. If the work is serialized on one branch, the coordinator can generate the queue
   with `tools/launch-coordinator.ps1`.
9. The notetaker records the run in `.agents/state/inventory.md` after each active
   agent finishes.
