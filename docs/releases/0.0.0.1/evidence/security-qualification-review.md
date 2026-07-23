---
id: SC-REL-011
title: StoneCharts 0.0.0.1 Security Qualification Review
status: approved
classification: normative
owner: security-contact
approver: maintainer
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-SEC-001]
evidence: [TEST-XSS-ESCAPING]
last_reviewed: "2026-07-23"
review_due: "2026-08-23"
supersedes: null
superseded_by: null
---

# Security Qualification Review

## Scope

This review covers the REQ-SEC-001 acceptance contract: untrusted specification
strings and style values must not create markup, script, URL, or style injection in
either language's SVG or HTML output.

## Verified

- `python -m pytest libs/python/tests -k xss` (`test_xss_escaping`): pass.
- `go test ./... -run TestXSSEscaping` (`TestXSSEscaping`): pass.
- Both tests exercise hostile strings (`"><script>alert(1)</script>`) across every
  user-facing field (id, title, subtitle, axis titles, category labels, series
  names) and confirm the structured style allowlist rejects unsafe colors and
  pattern/gradient values, in both the raw SVG and the wrapped self-contained HTML.

## Acceptance criteria

- [x] Hostile text cannot create executable markup in SVG or HTML.
- [x] Style-bearing fields have explicit validation or safe encoding rules.
- [x] Security regressions block release.

## Note on the third criterion

"Blocks release" is enforced procedurally, not by an automated gate: this repository's
GitHub tier does not support branch protection (private repo, confirmed via the API),
so no technical control currently prevents a direct push or an unreviewed merge to
`main`. The actual enforcement is the governed Stage 2/3/4 gate sequence — `GATE-S2`
requires "no unresolved critical or high release defect," and `GATE-S4` cannot close
without it — combined with the risk-acceptance policy already recorded in
[`docs/security/threat-model.md`](../../../security/threat-model.md): critical/high
defects block release unless explicitly, time-boundedly risk-accepted, which in the
current solo maintainer/security-contact role is self-approved, not independently
audited.

This is a known, disclosed limitation of the current operating model, not a gap this
review is papering over. Upgrading to a repo tier with branch protection (or making
the repository public) and requiring the `quality` CI workflow as a required check
would add a technical backstop; it is not in place today.

## Result

`REQ-SEC-001` is approved as qualified for 0.0.0.1 under the process-based enforcement
described above.
