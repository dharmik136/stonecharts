## Outcome

Describe the user or system outcome, not only the files changed.

## Traceability

- Requirement(s):
- ADR or contract:
- Risk(s):
- Target release:
- Closes:

## Change Class

- [ ] Defect correction
- [ ] Compatible capability
- [ ] Contract or architecture change
- [ ] Canonical-output change
- [ ] Security or supply-chain change
- [ ] Documentation or operations only

## Compatibility

Describe schema, API, DOM, output-byte, runtime, packaging, and migration impact.

## Verification

- [ ] `python tools/check_docs.py`
- [ ] `python tools/check_github_project.py` when Project or backlog controls change
- [ ] `python -m pytest libs/python/tests`
- [ ] `go test ./...` from `libs/go`
- [ ] Direct cross-render comparison, when canonical output changes
- [ ] Browser/runtime qualification, when interaction behavior changes
- [ ] Benchmark comparison, when a performance-sensitive path changes

Evidence or exact commands:

## Review

- [ ] Acceptance criteria are demonstrated.
- [ ] Intentional golden changes are explained and independently inspectable.
- [ ] Security, accessibility, and failure behavior were considered.
- [ ] Documentation and release evidence are updated where required.
- [ ] The review mode is identified honestly as self or independent review.
