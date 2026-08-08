# Changelog

All notable product and contract changes are recorded here. StoneCharts uses its
governed product release identifiers, PEP 440-compatible Python versions, and explicit
Go module mappings when Go semantic-version tagging is required. Release `0.0.0.1` is
not represented as Semantic Versioning.

## [Unreleased]

No unreleased changes.

## [0.0.0.6] - 2026-08-08

### Added

- `histogram` chart type (DEC-021): binning transform (sqrt-rule default, explicit
  count/width, pre-binned mode with density normalization), contiguous bars with
  numeric linear x-scale and en-dash edge labels, optional overlays (pareto cumulative
  line on secondary y-axis, bellcurve normal-distribution fit). Certified renderers in
  both Python and Go with byte-identical golden SVGs across 5 examples (basic,
  prebinned, pareto, themed-dark, adversarial). Approved as validation infrastructure
  under DEC-017.
- Schema extended with `histogram` in the type enum.
- Cross-render corpus expanded to 43 examples across 8 chart types.
- Python test coverage expanded to 146 tests.

## [0.0.0.5] - 2026-08-08

### Added

- `combo` chart type (DEC-020): per-series mark types (column + line) on shared
  Cartesian axes with optional dual y-axis (`secondaryYAxis`). Certified renderers in
  both Python and Go with byte-identical golden SVGs. Schema extended with
  `series[].type` and `series[].yAxis` fields. Legend swatch differentiates column
  (rect) vs line (thin bar). Approved as validation infrastructure under DEC-017.
- Gated demo site (DEC-019): landing page with stats bar, problem/solution cards, and
  access-request form; demo gallery, benchmarks dashboard, StoneVerify evidence viewer.
  Deployed via Astro with Cloudflare Access gate. JSON-LD structured data, canonical
  URLs, Open Graph image, Twitter cards, sitemap, CSP headers, 404 page.
- Go fuzz test (`FuzzFromJSON`) with 10 seed corpus entries from all 7 chart types.
- Go benchmark functions (`BenchmarkRender`, `BenchmarkRenderComplex`,
  `BenchmarkFromJSON`) covering all 7 chart types with basic and complex specs.
- Browser qualification tests for all 7 chart types: Playwright + Chromium tests cover
  tooltip on hover, keyboard navigation, legend toggle, and ARIA attributes.
- Validation coverage expanded to 99%: 34 new edge-case assertions covering gradient
  stops, pattern/marker/theme objects, scatter/bubble datum models, margin plot-area
  checks, unknown chart types, and percent-stacking guards.
- Python test coverage improved to 88% overall (140 tests).
- Content-draft articles rewritten with governed YAML frontmatter.

### Fixed

- Area chart monotone spline parity: Go `area.go` now respects the per-series `curve`
  property, matching Python's `_spline_d` dispatch for `curve: "monotone"`.
- Bar chart margin parity: Go `cartesian.go` removed orientation-aware margin swap that
  diverged from Python's always-use-axis-title logic.
- Secondary-axis `ypix2` was mapping values to the wrong dimension (horizontal instead
  of vertical) in `cartesian.go` and `_cartesian.py`.
- `util._nice_num` could return `int` instead of `float`, causing downstream type
  mismatches.
- `verify/cli.py`: type annotation fixes and file handle context manager fix.
- CI: updated stale CodeQL and golangci-lint action SHAs; replaced `bc -l` with `awk`
  for Go coverage threshold (fixes Windows runner).
- `check_docs.py`: 51 pre-existing issues resolved (content-draft frontmatter, backlog
  schema `site` area, traceability cross-references, document ID patterns).

## [0.0.0.4] - 2026-07-28

### Added

- `bubble` chart type (DEC-016): extends scatter's point model with `z` value and a
  deterministic area-proportional size scale (`r = sqrt(z)`). Certified renderers in
  Python and Go with byte-identical golden SVGs. No shared-frame changes required.
- StoneVerify conformance workflow: installable `stoneverify` console script, semantic
  difference categories, baseline comparison workflow, result-envelope helper with
  stable `VERIFY.*` finding codes, resource limits and timeout exit codes, JUnit XML
  output and GitHub Actions annotations.
- StoneVerify evaluation-kit builder: creates a repo-independent zip with wheel, Go
  adapter, sample spec, schemas, governed docs, and a demo runner.
- StoneVerify pilot-readiness gate (`GATE-VERIFY-PILOT-001`): CI job with external
  fixture, artifact upload, and annotation verification.
- Competitor benchmark against Vega, Highcharts Export Server, and QuickChart
  (`SC-QUAL-003`): measured determinism, cold-start, throughput, dependency surface.
- Visual Integrity Infrastructure repositioning (DEC-017): paused broad expansion,
  focused on insurance reporting validation segment.
- Name-clearance due-diligence framework (DEC-012, WORK-GTM-014).
- Prospect qualification scorecard, pilot-offer hypothesis, and GTM content drafts.

## [0.0.0.3] - 2026-07-27

### Added

- `scatter` chart type (DEC-015): introduces the governed point model
  (`series[].data` normalizes to `{x,y}` / `[x,y]` / bare-number) and a numeric
  `linear` x-scale. Forces two generalizations shared across every chart type.
  Certified renderers in Python and Go with byte-identical golden SVGs.

## [0.0.0.2] - 2026-07-27

### Added

- `bar` chart type (DEC-014): pure orientation transpose of the column substrate.
  Reuses column's band-layout, stacking, and shared chrome with no new data or point
  model. Certified renderers in Python and Go with byte-identical golden SVGs.

## [0.0.0.1] - 2026-07-24

### Added

- Stage 0 product and engineering governance system.
- Controlled document metadata, requirements, evidence, risk, and role registries.
- Product thesis, first-release scope, renderer constitution, guarantee contracts, security
  controls, test strategy, benchmark protocol, and 0.0.0.1 release qualification plan.
- Architecture decisions for guarantee profiles, capability validation, signed
  stacking, adaptive runtime behavior, and typography/layout profiles.
- Documentation and traceability validation tool plus CI quality workflow.
- Governed GitHub Project backlog, workflow fields, and conformance controls.
- ADR 0007 establishing `0.0.0.1` as the canonical first release identifier.
- `line` chart renderer (Python and Go): basic, styled, markers, spline, gradient,
  dark theme. Certified with byte-identical golden SVGs.
- `column` chart renderer (Python and Go): grouped, stacked, and percent-stacked
  profiles. Certified with byte-identical golden SVGs.
- `area` chart renderer (Python and Go): basic, stacked, and percent-stacked profiles.
  Certified with byte-identical golden SVGs.
- Shared Cartesian frame: axis rendering, grid lines, legend, runtime interactions
  (tooltip, highlight, crosshair, keyboard navigation, legend toggle).
- Self-contained interactive HTML runtime with governed interaction semantics.
- Structured customization surface (DEC-004): themes (light/dark/custom), series
  styling, gradients, patterns, sizing, layout controls. Arbitrary CSS, callbacks,
  and DOM mutation rejected.
- Immutable release evidence pack (`REQ-REL-001`): manifest, SBOM, provenance, hashes,
  and qualification evidence.
- Qualified Python wheel install and Go module consumption.

### Fixed

- Removed unapproved chart type implementations (`bar`, `arearange`, `combo`,
  `histogram`, `scatter`) that had been added without `DEC-*`/`REQ-*` decisions,
  widening scope beyond the ratified `line`/`column`/`area` set (DEC-002).
- CI `python` job was missing `jsonschema` dependency.
- Documentation linked to `.gitignore`d benchmark output files as committed evidence.
- CI workflow triggered `push` builds on the legacy `master` branch instead of `main`.

## [0.1.0] - Unreleased historical metadata

An earlier development snapshot reported this version before `DEC-001` established
`0.0.0.1` as the canonical release identifier. The Python package now correctly reports
`0.0.0.1` (`libs/python/pyproject.toml`); this line is retained only as historical
context and must not be treated as a published compatibility milestone.
