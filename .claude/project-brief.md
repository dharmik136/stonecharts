# StoneCharts Project Brief
**For Claude Code Agent Navigation**

---

## PART 1: PROJECT SCOPE (What Was Decided)

### Product Promise
**StoneCharts turns one structured chart specification into the same validated, auditable chart across certified programming languages.**

- Not just a chart-drawing collection
- A **portable chart contract**: shared input semantics, independent native renderers, canonical output, bounded customization, evidence of agreement
- Server-side deterministic SVG (no browser needed)
- Cross-language byte-parity (Python ≡ Go)
- Optional interactivity layer (tooltip, legend toggle, crosshair, keyboard nav, a11y)

### Current Scope (Release 0.0.0.4, certified)

**Chart Types:** `line`, `column`, `area`, `bar`, `scatter`, `bubble` — see
`docs/product/capability-matrix.md` for the authoritative table; do not restate it
here or let this list drift again.
**Languages:** Python, Go (only certified implementations)
**Axis Types:** Categorical X, linear numeric Y, plus a numeric linear X scale (added
for scatter/bubble) and the point model (`{x,y[,z]}`) it depends on.
**Customization:** Themes (light/dark/custom), series styling, gradients, patterns, sizing, layout controls
**Output:** Static SVG + self-contained interactive HTML + local StoneVerify conformance evidence bundles (`tools/stonecharts_verify.py`)

**Frozen since DEC-017 (2026-07-28):** broad chart-family and language expansion is
paused pending paid customer validation evidence or explicit approval; see
`docs/product/visual-integrity-strategy.md`. Do not propose a new chart type or
language without checking that decision first.

**Not in scope:**
- Remaining design-only chart recipes (roadmap material) until each passes the chart admission checklist
- Arbitrary CSS, callbacks, DOM mutation inside certified profile
- Automatic text measurement / collision avoidance / universal label fitting
- Pixel-perfect guarantee outside named visual profiles
- Hosted rendering, accounts, billing, collaboration, StoneVault, StonePolicy

### Expansion Rule (Hard Boundary)
A new chart type, language, export engine, or feature may enter scope **only after**:
- ✅ Contract is written
- ✅ Acceptance criteria defined
- ✅ Conformance fixtures built
- ✅ Ownership assigned
- ✅ Compatibility matrix complete
- ✅ Performance evidence collected
- ✅ Security review done
- ✅ Release documentation finished

**Files on disk ≠ supported. Examples passing ≠ supported.**

---

## PART 2: GOVERNANCE MODEL (How Work is Controlled)

### Stage Gates (Current State)
**Stage 0 through Stage 14 are all closed (`GATE-S0` through `GATE-S14`, all
`Done`).** Releases `0.0.0.1` through `0.0.0.4` are tagged. All 8 chart-related
decisions (DEC-001 through DEC-016) plus the DEC-017/DEC-018 repositioning are
resolved — see `docs/project/decisions.md`; its "Open decisions" table is currently
empty. Do not treat any DEC-001..018 as pending; check `decisions.md` directly if in
doubt, this brief is not the source of truth for decision status.

**Current phase:** post-0.0.0.4, Visual Integrity Infrastructure validation
(DEC-017). Engineering breadth is intentionally paused; see
`docs/product/visual-integrity-strategy.md` for the validation gate that must be met
before it resumes.

### Sources of Truth (Precedence)
1. **Approved normative documents** (thesis, positioning, guarantees, contracts, requirements)
2. **Requirements, risks, decisions, evidence registries** (YAML files)
3. **Execution backlog** (backlog.yaml, schema-validated)
4. **GitHub Project** (current status, ownership, priority, dependencies)
5. **GitHub issues/PRs** (bounded outcomes, reviewed changes)
6. **Generated evidence** (actual test results, conformance proof)

**When they disagree: The higher source controls. The lower source is corrected.**

### Document Status & Classification
Every document has metadata:
- **Status:** `proposed` | `approved` — reflects truthful review state
- **Classification:** `normative` (binding) | `informative` (reference only)
- **Owner:** Who wrote it
- **Approver:** Who approves it (often same person, tagged `review_mode: self`)
- **Review due:** When re-review is required

---

## PART 3: AGENT RESPONSIBILITIES & HANDOFF PROTOCOL

### Default Agent Roles (When Work is Distributed)

| Role | Responsibility | Passes to |
|---|---|---|
| **Planner** | Converts requests into scope, backlog items, decisions, release gates. Separates facts from recommendation. | Stakeholder |
| **Stakeholder** | Carries agent outputs to discussion, routes feedback back to planning. Preserves traceability. | Planning loop or next role |
| **Developer** | Implements approved code/schema/runtime/fixtures. Touches only named files. Preserves deterministic output & contracts. | QA |
| **QA** | Runs verification, compares outputs, reports regressions. Checks contract boundary, not just happy path. | Compliance |
| **Security** | Reviews attack surface, supply chain, execution boundaries, secrets. Concrete mitigations. | Compliance |
| **Compliance** | Checks traceability, approvals, doc status, release evidence. Verifies truth of approval claim. | Release |
| **Release** | Assembles release manifest, evidence pack, ship checklist. Only starts after all checks done. | Ship |
| **Note-Taker** | Records searches, edits, checks, handoffs without inventing conclusions. Flags repo ↔ coordination mismatches. | (Runs alongside/after) |

**Normal flow:** `Planner` → `Stakeholder` → `Developer` → `QA` → `Compliance` → `Security` ↔ `Compliance` → `Release`

### Handoff Protocol (Every Handoff Must Answer)
1. **What is the next bounded outcome?**
2. **Which files are safe to touch?**
3. **Which checks must pass before the next handoff?**
4. **What is the current commit or working state?**
5. **What is blocked, deferred, or intentionally left out?**

### Coordination Rules
- **One agent owns one bounded outcome.** No concurrent writes to same branch.
- **Reviewers do not merge unverified changes.** QA evidence required.
- **Release work waits for required decisions + approvals.** No side-stepping.
- **Human approval required** for scope/release-claim changes.

### Socratic Self-Checks (Before Every Handoff)
Every agent must answer before passing work:

**Universal:**
1. What exact claim am I making?
2. What file/doc/test/evidence proves it?
3. What am I assuming without proof?
4. What is the smallest change that solves the problem?
5. What could break if my assumption is wrong?
6. What is out of scope and intentionally untouched?
7. Does handoff state match repo state?

**Plus role-specific checks in `.agents/self-checks.md`**

---

## PART 4: WORKING RULES (How to Move Forward as Claude)

### Before Making Any Change
**Read these in order (in `.agents/` or `docs/`):**
1. `docs/project/README.md` — project operating model
2. `docs/project/stage-0.md` — current gate & exit criteria
3. `docs/project/backlog.yaml` — governed work items
4. `docs/project/decisions.md` — open decisions
5. `docs/product/thesis.md` — product promise
6. `docs/product/positioning-and-scope.md` — certified user outcomes and scope
7. `CHARTS.md` — chart router & design guidance
8. `.agents/self-checks.md` — verification before handoff
9. **Relevant chart `design.md`, spec, contracts, runtime code** for the task

### Key Rules
- ✅ **Follow the governed backlog and stage-gate order.** No jumping ahead.
- ✅ **Do NOT widen chart/language/release scope** without approved decision + requirement first.
- ✅ **Keep byte-parity work deterministic.** Do not regenerate goldens unless the change explicitly requires it.
- ✅ **Prefer small, reviewable changes** matching existing repo structure.
- ✅ **Run smallest relevant checks first**, then broader checks at boundaries.
- ✅ **If task touches release/project/contract docs**, verify corresponding backlog + traceability entries.
- ✅ **Speak plainly.** Separate facts, verification, recommendation.
- ✅ **Use exact dates, branch names, file paths, IDs** when they matter.
- ✅ **Do not imply certainty the repo doesn't support.**

### Baseline Checks (Run These)
```bash
# Documentation consistency
python tools/check_docs.py

# Project conformance
python tools/check_github_project.py

# Python tests
python -m pytest libs/python/tests -q

# Go tests (from libs/go/)
go test ./...

# Runtime syntax check
node --check runtime/chart-interactions.js
```

### Multi-Agent Coordination (If Used)
- One agent per bounded outcome
- One writable branch/worktree per active agent
- No concurrent writes to same branch
- Use branch lock + handoff note for coordination
- Record active owner, intended files, stop point **before** editing
- Use handoff protocol (above) before merging

---

## PART 5: CURRENT PROJECT STATE (As of 2026-07-29)

Do not trust this section's specifics for long — re-verify against
`docs/project/backlog.yaml`, `docs/project/decisions.md`, and
`python tools/check_docs.py` / `python tools/check_github_project.py` before acting.
This section rots; those sources do not.

### Repository Status
- **Branches:** exactly one — `main`, local and on `origin`. Every other local and
  remote branch was reviewed for unmerged work (none found) and deleted 2026-07-29.
- **Repo:** Private git at `C:\Users\Dharmik Shingala\stonecharts`
- **GitHub Project:** [StoneCharts #2](https://github.com/users/dharmik136/projects/2) — kept in sync via `python tools/check_github_project.py --apply`
- **Latest work:** 0.0.0.1-0.0.0.4 chart admissions and releases, the DEC-017 Visual
  Integrity Infrastructure repositioning, StoneVerify (`tools/stonecharts_verify.py`),
  and a measured (not hypothetical) competitor benchmark against Vega,
  Highcharts Export Server, and QuickChart (`docs/quality/competitor-benchmark-results-2026-07.md`).

### Implementation Status
| Chart | First certified release | Python | Go | Interactivity |
|---|---:|---|---|---|
| `line` / `line-basic` | 0.0.0.1 | complete | complete | tooltip, highlight, legend, crosshair |
| `column` | 0.0.0.1 | complete | complete | tooltip, highlight, legend, crosshair |
| `area` | 0.0.0.1 | complete | complete | tooltip, highlight, legend, crosshair |
| `bar` | 0.0.0.2 | complete | complete | tooltip, highlight, legend, crosshair |
| `scatter` | 0.0.0.3 | complete | complete | tooltip, highlight, legend, crosshair |
| `bubble` | 0.0.0.4 | complete | complete | tooltip, highlight, legend, crosshair |

**Byte-parity:** Python and Go render identical SVG for every certified chart type
(verified by golden tests, and independently by StoneVerify's cross-runtime check).
No further chart type is certified without a new DEC + REQ per the admission
checklist, and DEC-017 currently pauses that path by default.

### Known Gaps
- All backlog items are `Done` (64 governed items as of 2026-07-29). The real open
  work is the DEC-017 validation gate: 20 qualified interviews, real production
  fixtures, and paid pilots — none of which an agent can complete unilaterally.
- Test coverage: see `docs/quality/test-strategy.md`.

### Documentation Status
- Normative docs: all `approved` for anything currently load-bearing; `docs/project/decisions.md`'s open-decisions table is empty.
- Schema validation: passing (`python tools/check_docs.py`)
- Project conformance: passing (`python tools/check_github_project.py`)
- Release evidence: complete and immutable for 0.0.0.1 through 0.0.0.4

---

## PART 6: HOW YOU (CLAUDE) SHOULD PROCEED

### Your Role & Boundaries
You are operating as a **development + documentation assistant** under this governance model. Your job:

**✅ DO:**
- Read and internalize the governance documents (do this first for every task)
- Implement work items **already in `Ready` status** in the GitHub Project
- Write or refine code, tests, fixtures, and docs for in-scope chart types/languages
- Verify changes against baseline checks (documentation, Python, Go, runtime)
- Answer questions about the architecture, spec, or existing implementations
- Propose bounded improvements to unfinished work items
- Record what you did (handoff notes, evidence)

**❌ DON'T:**
- Propose or implement chart types/languages without approved DEC + REQ
- Regenerate golden fixtures unless the change explicitly requires it
- Skip Socratic self-checks before claiming work is done
- Claim byte-parity, customization guarantees, or release readiness without evidence
- Merge unverified changes (wait for human review + QA verification)
- Change scope mid-task; escalate to human for scope decisions
- Treat files-on-disk as proof of support (only approved requirements + evidence count)

### Immediate Next Steps (For Any Task You Undertake)
1. **Clarify the outcome:** Is this a new feature, bug fix, documentation, qualification work, or release prep?
2. **Map to scope:** Does it map to an existing work item in `backlog.yaml`? Is that item in `Ready` status?
3. **Read dependencies:** Open the relevant normative docs + backlog item + workstream.
4. **Identify files:** Which files will you touch? Are they in the handoff scope?
5. **Plan verification:** What baseline checks will prove this is done?
6. **Execute small:** Make the smallest change that proves the outcome. Don't over-engineer.
7. **Self-check:** Answer the Socratic questions before claiming handoff.
8. **Record it:** Leave a clear handoff note with what changed, what was verified, what's next.

### Questions to Ask the User (Before Starting Work)
- "Which work item in the GitHub Project should I focus on?"
- "Is this work item in `Ready` status?"
- "Are there any blocked decisions I should know about?"
- "What is the exact bounded outcome you want?"
- "Should I record my work as a formal handoff, or just report back?"

---

## References
- **Product:** `docs/product/thesis.md`, `positioning-and-scope.md`
- **Governance:** `docs/governance/`, `docs/contracts/`
- **Project:** `docs/project/README.md`, `backlog.yaml`, GitHub Project
- **Requirements:** `docs/requirements/registry.yaml`
- **Quality:** `docs/quality/test-strategy.md`
- **Release:** `docs/releases/0.0.0.1/plan.md`
- **Agents:** `.agents/self-checks.md` (this file), `AGENTS.md`
- **Architecture:** `docs/architecture/system-design.md`, `spec/`

---

**Last Updated:** 2026-07-29
**Written for:** Claude (Claude Code Agent)
**Status:** Reference guide (informative). This file duplicates ground already covered
by `AGENTS.md`; if the two ever disagree, `AGENTS.md` and the actual governed docs win
— fix this file, don't trust it over them.
