# Socratic Self-Checks

Every agent role must answer these questions before handing work off.

## Universal checks

1. What exact claim am I making?
2. What file, doc, test, or evidence proves it?
3. What am I assuming without proof?
4. What is the smallest change that solves the stated problem?
5. What could break if my assumption is wrong?
6. What is out of scope and intentionally untouched?
7. Does the handoff state match the repo state?

## Role-specific checks

### Planner

- Is the decision bounded and answerable now?
- Which governing document controls the answer?
- Does this change scope, release claims, or dependencies?
- Did I separate facts from recommendation?

### Developer

- Did I touch only the files named in the handoff?
- Did I preserve deterministic output and existing contract boundaries?
- Did I avoid widening scope while implementing?
- Did I verify the exact behavior change with the smallest useful check set?

### QA

- Did I reproduce the failure or confirm the pass path with evidence?
- Did I check the contract boundary, not only the happy path?
- Are the failure details exact enough for the owner to act on?
- Would the result still hold on a fresh run or clean tree?

### Security

- What trust boundary is crossed?
- What untrusted input, dependency, or workflow is involved?
- Does this introduce new execution, permission, or secret exposure?
- Is the mitigation concrete, not just descriptive?

### Compliance

- Which requirement, decision, ADR, or release gate is the source of truth?
- Are approval status and document status consistent?
- Did I avoid inferring an approval that was never recorded?
- Is the release target and evidence trail complete?

### Release

- Are all required decisions, requirements, QA, compliance, and security checks done?
- Does the release evidence match the exact commit and version?
- Is the tree clean and the release metadata current?
- Would I be comfortable handing this to someone who only trusts the docs?

### Note-taker

- Did I record the agent role, time, branch, and owner?
- Did I list the searches, edits, checks, and handoff evidence without inventing
  conclusions?
- Did I flag any mismatch between the coordination state and the repo state?
- Did I avoid changing implementation files or approving the work?

### Stakeholder

- Did I restate the original point accurately?
- Did I capture stakeholder feedback without changing the underlying decision?
- Did I route the response to the next planning action or decision?
- Did I preserve traceability to the originating agent output?
