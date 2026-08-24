# Security Policy

## Supported versions

StoneCharts is pre-release software at version `0.0.0.33` with 36 certified chart
types. No version is currently designated for production security support. Security
evidence is included in release qualification evidence packs (see `docs/releases/`).

## Reporting a vulnerability

Do not disclose a suspected vulnerability in a public issue. Use GitHub private
vulnerability reporting for this repository when available. If that facility is not
available, contact the repository owner through GitHub to establish a private channel
without including exploit details in the initial public message.

Include:

- Affected commit, package, and version.
- Reproduction steps or a minimal proof of concept.
- Expected and observed impact.
- Relevant environment and embedding mode.
- Whether the issue is already public or under active exploitation.

The current project does not promise a response-time SLA. Receipt, severity,
remediation, coordination, and disclosure decisions are handled by the
`security-contact` role defined in `docs/governance/roles.yaml`. Commercial response
obligations require a separate written support agreement.

## Scope priorities

High-priority reports include SVG/HTML/script/style injection, unsafe URL handling,
renderer denial of service, package or release substitution, provenance failure,
sensitive-data exposure, and accessibility behavior that creates a security or fraud
risk. The current threat model is
[`docs/security/threat-model.md`](docs/security/threat-model.md).
