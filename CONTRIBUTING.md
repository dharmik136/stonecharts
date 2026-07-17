# Contributing to PeakCharts

PeakCharts is proprietary software. Access to the repository does not grant a right to
use, copy, modify, distribute, or contribute code. Contributions are accepted only
from authorized collaborators under written terms covering confidentiality and
intellectual property.

## Before work starts

1. Confirm authorization and the intended requirement or defect ID.
2. Read [`docs/README.md`](docs/README.md), the applicable contracts, and the
   [renderer constitution](docs/architecture/renderer-constitution.md).
3. For a contract or architecture change, update the requirement and ADR before code.
4. Keep one change focused enough to review and revert independently.

## Development rules

- Do not modify unrelated files or regenerate goldens to hide a failure.
- Add semantic assertions before approving serialization changes.
- Keep Python and Go behavior, errors, formatting, and tests in lockstep.
- Treat specs as untrusted input and use contextual encoding.
- Do not add a dependency without license, security, maintenance, size, and
  determinism review.
- Do not add a chart type, language, or public option outside an approved release
  scope.

## Required local gates

```powershell
python tools/check_docs.py
python -m pytest libs/python/tests
Push-Location libs/go; go test ./...; Pop-Location
```

A change affecting browser behavior also requires the certified local HTTP browser
suite once that gate is implemented. A change affecting canonical output includes a
reviewed direct Python-to-Go diff and records any intentional golden changes.

## Review record

The pull request or change record links requirements, ADRs, risks, tests, compatibility
impact, security impact, and release target. Self-review is identified as self-review;
it is not described as independent approval.

