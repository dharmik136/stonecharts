# Antigravity Agent Workspace

This directory is the Antigravity-native instruction area for StoneCharts.

## Structure

- `coordination.md`: branch, worktree, and handoff rules for multiple agents
- `agents.md`: role definitions and behavioral constraints for the agent team
- `self-checks.md`: universal and role-specific Socratic pre-handoff questions
- `skills/`: reusable task manuals for common work types
- `state/`: transient lock and handoff notes used during active coordination
- `workflows/`: stepwise pipelines and slash-command style routines

The agent team is local and private. GitHub only sees the resulting commits, issues,
and pull requests that the human decides to publish.
The persistent inventory log lives in `.agents/state/inventory.md`.
All agents should answer in a factual, bounded style and keep recommendations
separate from evidence.
The agent system is meant to run as a continuing loop: each role records its handoff,
the next role picks up from repo state, and the human only returns for scope or
approval changes.

Keep these files small, explicit, and focused on handoff behavior rather than product
documentation.
