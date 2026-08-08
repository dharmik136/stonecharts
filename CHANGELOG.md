# Changelog

All notable product and contract changes are recorded here. StoneCharts uses its
governed product release identifiers, PEP 440-compatible Python versions, and explicit
Go module mappings when Go semantic-version tagging is required. Release `0.0.0.1` is
not represented as Semantic Versioning.

## [Unreleased]

### Added

- `combo` chart type: per-series mark types (column + line) on shared Cartesian axes
  with optional dual y-axis (`secondaryYAxis`). Certified renderers in both Python and
  Go with byte-identical golden SVGs. Schema extended with `series[].type` and
  `series[].yAxis` fields. Legend swatch differentiates column (rect) vs line (thin bar).
  Release target: 0.0.0.5.
- Go fuzz test (`FuzzFromJSON`) with 10 seed corpus entries from all 7 chart types.
- Go benchmark functions (`BenchmarkRender`, `BenchmarkRenderComplex`, `BenchmarkFromJSON`)
  covering all 7 chart types with basic and complex specs.
- Cross-language fuzz property check now reports actual case count (120) including combo.
- Browser qualification tests for all 7 chart types (line, column, bar, scatter, bubble,
  area, combo): Playwright + Chromium tests cover tooltip on hover, keyboard navigation
  (ArrowRight, ArrowDown, Escape), legend toggle, and ARIA attributes.
- Validation coverage expanded to 99% (`validate.py`): 34 new edge-case assertions covering
  gradient stops, pattern/marker/theme objects, scatter/bubble datum models, margin
  plot-area checks, unknown chart types, and percent-stacking guards.
- Python test coverage improved to 88% overall (140 tests, 6 skipped) with targeted tests
  for `util.fmt_num`, `CapabilityError`, resource limits, theme resolution, scatter
  `__post_init__` normalization, and empty-data renderer paths. `capabilities.py` at 100%.

### Fixed

- CI `quality.yml`: updated wheel install and pilot gate jobs from `0.0.0.4` to `0.0.0.5`;
  added combo to evidence-regression chart type list and wheel-install smoke test.

- Area chart monotone spline parity: Go `area.go` now respects the per-series `curve`
  property, matching Python's `_spline_d` dispatch for `curve: "monotone"`.
- Bar chart margin parity: Go `cartesian.go` removed orientation-aware margin swap that
  diverged from Python's always-use-axis-title logic.
- `__init__.py` version bumped to `0.0.0.5` (was stale at `0.0.0.4`).
- `check_docs.py`: 51 pre-existing issues resolved (content-draft frontmatter, backlog
  schema `site` area, traceability cross-references, document ID patterns).
- Stage 0 product and engineering governance system.
- Controlled document metadata, requirements, evidence, risk, and role registries.
- Product thesis, first-release scope, renderer constitution, guarantee contracts, security
  controls, test strategy, benchmark protocol, and 0.0.0.1 release qualification plan.
- Architecture decisions for guarantee profiles, capability validation, signed
  stacking, adaptive runtime behavior, and typography/layout profiles.
- Documentation and traceability validation tool plus CI quality workflow.
- Governed GitHub Project backlog, workflow fields, and conformance controls.
- ADR 0007 establishing `0.0.0.1` as the canonical first release identifier.
- Stage 1 (`GATE-S1`): `area` chart renderer in both languages; reconciled schema/Python/Go
  validation semantics; signed normal and percent stacking geometry; deterministic
  validated manual margins; qualified runtime interaction semantics; deterministic
  customization boundary.
- Stage 2 (`GATE-S2`): canonical SVG byte-parity requalified across the full active
  corpus (line, column, area) including a direct Python-Go cross-render sweep; browser
  and manual accessibility qualification (live Chromium harness + Node DOM harness +
  recorded ARIA-tree review); visual reproducibility profile review; untrusted
  specification safety requalification (XSS/injection escaping, both languages);
  reproducible performance qualification against the approved Small/Business/Dense/Stress
  workload matrix (rewrote both language benchmark harnesses to implement it, replacing an
  older, unrelated point-count/layout-style dimension).
- `REQ-REL-001`: immutable release evidence pack (manifest, SBOM, provenance, hashes,
  package install matrix) for candidate `rc.1`, validated against
  `docs/releases/0.0.0.1/evidence/manifest.schema.json`.
- Toward `GATE-S3`: qualified Python wheel install (built, installed into an isolated
  venv, confirmed resolution from the installed copy rather than the source tree, on
  3.14 locally and 3.9 in CI) and Go module consumption (via a separate consumer module
  using a local `replace` directive).

### Fixed

- Removed `bar`, `arearange`, `combo`, `histogram`, and `scatter` renderer
  implementations, golden fixtures, and schema/capability registrations that had been
  added without an approved `DEC-*`/`REQ-*` decision, widening active scope beyond the
  ratified `line`/`column`/`area` (`DEC-002`). Restored their pre-existing
  `design.md`/`examples/` informative scaffolding.
- CI `python` job was missing the `jsonschema` dependency `test_golden.py` imports,
  failing test collection on every fresh run since it was introduced.
- Documentation linked to `.gitignore`d, machine-specific benchmark output files as if
  they were committed evidence; changed to plain references with an explanation.
- CI workflow triggered `push` builds on the legacy `master` branch instead of the
  canonical `main` (`DEC-006`).

### Known release blockers

- Release tag and publication are not yet performed (`DEC-011`: private until Stage 3
  evidence is complete).
- Public support channel sign-off is not yet recorded.

## [0.1.0] - Unreleased historical metadata

An earlier development snapshot reported this version before `DEC-001` established
`0.0.0.1` as the canonical release identifier. The Python package now correctly reports
`0.0.0.1` (`libs/python/pyproject.toml`); this line is retained only as historical
context and must not be treated as a published compatibility milestone.
