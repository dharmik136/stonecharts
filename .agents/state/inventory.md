# Agent Inventory

This log records local CLI agent launches, their intended scope, and the verification
they reported back.

| Time | Role | Branch or worktree | Owner | Launch note |
|---|---|---|---|---|
| 2026-07-18 14:02:21 +05:30 | notetaker | - | coordinator | Private local CLI worker; no GitHub collaborator role. |
| 2026-07-18 14:51:39 +05:30 | stakeholder | - | coordinator | Private local CLI worker; no GitHub collaborator role. |
| 2026-07-18 15:09:29 +05:30 | planner | - | coordinator | Private local CLI worker; no GitHub collaborator role. |
| 2026-07-19 13:10:55 +05:30 | planner | - | coordinator | Draft agent created for governed scope, decisions, backlog items, and release gates. |
| 2026-07-19 13:10:55 +05:30 | developer | - | coordinator | Draft agent created for approved repo changes in code, schema, runtime, docs, and fixtures. |
| 2026-07-19 13:10:55 +05:30 | qa | - | coordinator | Draft agent created for verification and evidence checking. |
| 2026-07-19 13:10:55 +05:30 | security | - | coordinator | Draft agent created for attack-surface, dependency, and boundary review. |
| 2026-07-19 13:10:55 +05:30 | compliance | - | coordinator | Draft agent created for traceability, approvals, and release readiness. |
| 2026-07-19 13:10:55 +05:30 | release | - | coordinator | Draft agent created for release evidence, version mapping, and ship checklist assembly. |
| 2026-07-19 13:10:55 +05:30 | stakeholder | - | coordinator | Draft agent created for carrying agent outputs into stakeholder-facing discussion. |
| 2026-07-19 13:10:55 +05:30 | notetaker | - | coordinator | Draft agent created for time-ordered inventory of launches, searches, edits, checks, and handoffs. |

## Live schedules

The published workspace agents are now attached to hourly ChatGPT schedules with
staggered offsets in `Asia/Calcutta`:

- planner: minute 00
- developer: minute 05
- qa: minute 10
- security: minute 15
- compliance: minute 20
- release: minute 25
- stakeholder: minute 30
- notetaker: minute 35
- design partner: minute 40

## 2026-07-29 - repository and coordination-state cleanup

| Time | Role | Branch or worktree | Owner | Launch note |
|---|---|---|---|---|
| 2026-07-29 | notetaker | main | coordinator | Reviewed every local and remote branch for unmerged work before deleting: `pmf-positioning-alignment` (local, 0 unique commits vs `main`), `stage0-stage1-approved-scope` (local, 0 unique commits, remote already gone, merged via PR #36), `origin/master` (0 unique commits vs `main`, superseded default branch; `origin/HEAD` now correctly points to `main`). All three confirmed fully-merged ancestors of `main` via `git merge-base --is-ancestor` before deletion; nothing was lost. Repository now has exactly one branch, `main`, locally and on `origin`. |
| 2026-07-29 | notetaker | main | coordinator | Reset `.agents/state/branch-lock.md` and `.agents/state/handoff.md` off a stale, never-closed 2026-07-19 draft-agent-roster handoff to a clean idle state, so the next agent (Codex, Antigravity, or otherwise) does not read a dangling lock/handoff that no longer matches reality. Current ground truth: single branch `main`; `docs/project/backlog.yaml` 62/62 items `Done`; GATE-S0 through GATE-S14 closed; releases `0.0.0.1`-`0.0.0.4` tagged; DEC-017 pauses further chart/language expansion pending paid validation evidence. |

## 2026-08-24 - distribution and pilot readiness continuation

| Time | Role | Branch or worktree | Owner | Launch note |
|---|---|---|---|---|
| 2026-08-24 | release / compliance | main | Codex | Audited the two deferred outcomes after `0.0.0.34`; hardened and CI-qualified the current StoneVerify evaluation kit; pushed commit `f0ed994`; confirmed quality run `32721981417` green; and staged qualified artifacts in a private GitHub Release draft. Public publication and `WORK-GTM-012` remain at the explicit commercial-authorization and named-customer boundary. |
