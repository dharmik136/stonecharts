# Changelog

All notable product and contract changes are recorded here. StoneCharts uses its
governed product release identifiers, PEP 440-compatible Python versions, and explicit
Go module mappings when Go semantic-version tagging is required. Release `0.0.0.1` is
not represented as Semantic Versioning.

## [Unreleased]

No unreleased changes.

## [0.0.0.22] - 2026-08-10

### Added

- **Technical-indicators chart** (`type: "technical-indicators"`) — base metric/
  price line plus derived overlays computed from transforms: SMA, EMA, Bollinger
  bands, VWAP, RSI, MACD (DEC-038). Series carries `indicators[]` array of
  `{type, period?, color?, dashStyle?, params?, pane?}` objects; transforms run
  in the renderer, not authored as raw series. Supports plot bands/lines on both
  axes and panes, event flags (flag/circlepin/squarepin shapes), and oscillator
  panes (RSI renders in a separate vertical split below the main chart).
  Certified renderers in both Python and Go with byte-identical golden SVGs.
- Pane objects now parse `plotBands` and `plotLines` from JSON (previously
  silently ignored). Both renderers now render pane-scoped bands and lines.
- Cross-render corpus expanded to 123 examples across 25 chart types.
- Site gallery expanded to 25 chart types.

## [0.0.0.21] - 2026-08-10

### Added

- **X-range chart** (`type: "xrange"`) — horizontal span bars on lane categories
  with optional milestones and dependency connectors (DEC-037). Data model uses
  `series[].spans` array of `{x, x2, y, id?, name?, dependency?, milestone?}`
  objects where x/x2 are start/end positions and y is the lane index. Supports
  Gantt charts, distributed-trace span waterfalls, and per-thread swimlanes.
  Rides the shared cartesian frame with `orientation="horizontal"` and band
  x-scale. Milestone spans render as diamond `<polygon>` glyphs. Dependency
  connectors render as orthogonal elbow `<path>` elements with arrowheads.
  Certified renderers in both Python and Go with byte-identical golden SVGs.
- Cross-render corpus expanded to 118 examples across 24 chart types.
- Site gallery expanded to 24 chart types.

### Fixed

- Python spec parser now parses `yAxis.categories` (was missing, causing
  horizontal-mode charts to show numeric lane labels instead of category names).

## [0.0.0.20] - 2026-08-10

### Added

- **Vector-plot chart** (`type: "vector-plot"`) — arrow glyphs on a numeric x/y
  plane where each datum carries direction (heading in degrees, 0 = north,
  clockwise) and length (magnitude scaled to pixel length via a global
  length-scale) (DEC-036). New spec fields: `vectorLength` (max arrow pixel
  length, default 20), `rotationOrigin` (`"center"`, `"start"`, or `"end"`
  anchor placement). New series fields: `x` (numeric x-coordinates), `length`
  (per-point magnitude). Uses linear x-scale with `include_zero=False`. Arrow
  glyphs rendered as stroked `<path>` elements (shaft + arrowhead barbs) with
  trigonometric rotation. Certified renderers in both Python and Go with
  byte-identical golden SVGs.
- Cross-render corpus expanded to 105 examples across 23 chart types.
- Site gallery expanded to 23 chart types.

## [0.0.0.19] - 2026-08-10

### Added

- **Streamgraph chart** (`type: "streamgraph"`) — stacked, filled area ribbons
  over a shared x-axis displaced off a floating baseline (DEC-035). New spec
  field: `offset` (`"wiggle"` or `"silhouette"` baseline algorithm, default
  `"wiggle"`). Uses point x-scale with `include_zero=False`. Baseline offset
  pre-computed in `build_frame()` so gridlines and axis labels reflect the true
  offset envelope. Supports monotone curve smoothing, gradient fills, dark
  theme. Certified renderers in both Python and Go with byte-identical golden
  SVGs.
- Cross-render corpus expanded to 100 examples across 22 chart types.
- Site gallery expanded to 22 chart types.

## [0.0.0.18] - 2026-08-10

### Added

- **Windbarb chart** (`type: "windbarb"`) — meteorological wind-barb glyphs on a
  fixed lane, each encoding speed (feathers/flags) and direction (SVG rotate
  transform — no trig) (DEC-034). New spec fields: `series[].direction`
  (per-point wind direction in degrees), `speedUnit`, `calmThreshold`,
  `hemisphere`, `barbLength`, `yOffset`. Uses band x-scale with
  `include_zero=True` (0-based speed reference axis). Supports Northern and
  Southern hemisphere feather placement, calm glyph, pennant flags for 50+ kt
  speeds, dark theme. Certified renderers in both Python and Go with
  byte-identical golden SVGs.
- Cross-render corpus expanded to 96 examples across 21 chart types.
- Site gallery expanded to 21 chart types.

## [0.0.0.17] - 2026-08-10

### Added

- **Timeline chart** (`type: "timeline"`) — events placed along a single time
  axis with markers, leader lines, and alternating labels (DEC-033). New spec
  field: `series[].labels` (per-event label text). Uses numeric x-scale with
  `include_zero=False` (free time axis). Supports multiple event lanes, marker
  symbols (circle/square/triangle/diamond), dark theme, gradient fills.
  Certified renderers in both Python and Go with byte-identical golden SVGs.
- Cross-render corpus expanded to 91 examples across 20 chart types.
- Site gallery expanded to 20 chart types.

## [0.0.0.16] - 2026-08-10

### Added

- **Variwide chart** (`type: "variwide"`) — column chart where each bar's width
  also encodes a value (DEC-032). New spec field: `series[].widths` (per-datum
  width metric). Cumulative-width x-layout replaces column's equal bands.
  Supports negative y-values (bars drop below baseline), dark theme, gradient
  and pattern fills. Certified renderers in both Python and Go with
  byte-identical golden SVGs.
- Cross-render corpus expanded to 87 examples across 19 chart types.
- Site gallery expanded to 19 chart types.

## [0.0.0.15] - 2026-08-09

### Added

- **Funnel chart** (`type: "funnel"`) — centered trapezoid stack with
  value-to-width scaling for conversion and drop-off visualization (DEC-031).
  Subtypes: `funnel` (default, each stage tapers to the next), `pyramid`
  (reversed draw order for hierarchy), `neck` (tapers to a fixed-width neck
  at the bottom). New spec fields: `neckWidth`, `neckHeight`, `minWidth`.
  Does NOT use render_cartesian — funnel is the declared substrate exception
  (no axes, own SVG shell). Certified renderers in both Python and Go with
  byte-identical golden SVGs.
- Cross-render corpus expanded to 83 examples across 18 chart types.
- Site gallery expanded to 18 chart types.

## [0.0.0.14] - 2026-08-09

### Added

- **Dumbbell chart** (`type: "dumbbell"`) — connected-dot plot with two marker
  heads (low + high) joined by a thin connector per category (DEC-030). Uses
  `data` for low values and `high` array for high values with `include_zero=False`.
  Supports vertical and horizontal orientation, single and grouped (multi-series)
  dumbbells, all four marker symbols, dark theme. Certified renderers in both
  Python and Go with byte-identical golden SVGs.
- Cross-render corpus expanded to 78 examples across 17 chart types.

## [0.0.0.13] - 2026-08-09

### Added

- **Lollipop chart** (`type: "lollipop"`) — thin stems from the baseline capped
  with marker heads. Reuses column's band layout and line's marker shapes
  (DEC-029). Supports vertical and horizontal orientation, single and grouped
  (multi-series) lollipops, all four marker symbols (circle/square/triangle/
  diamond), dark theme. Certified renderers in both Python and Go with
  byte-identical golden SVGs.
- Cross-render corpus expanded to 73 examples across 16 chart types.

## [0.0.0.12] - 2026-08-09

### Added

- **Boxplot chart** (`type: "boxplot"`) — box-and-whisker glyphs showing a
  5-number summary (low, q1, median, q3, high) plus optional outliers per
  category (DEC-028). New spec field: `boxData` (summary-mode array of
  `{low, q1, median, q3, high, outliers?}` per category). Supports vertical
  and horizontal orientation, single and grouped (multi-series) boxes, dark
  theme, and gradient fills. Certified renderers in both Python and Go with
  byte-identical golden SVGs.
- Cross-render corpus expanded to 68 examples across 15 chart types.
- Site gallery expanded from 7 to 15 chart types.

## [0.0.0.11] - 2026-08-09

### Added

- **Bullet chart** (`type: "bullet"`) — horizontal KPI bars with a comparative
  target tick and qualitative range bands (DEC-027). New spec fields:
  `bulletTarget` (comparison value), `bulletRanges` (qualitative bounds).
  Rides bar's horizontal orientation and shared Cartesian chrome. Certified
  renderers in both Python and Go with byte-identical golden SVGs.

## [0.0.0.10] - 2026-08-08

### Added

- **Waterfall chart** (`type: "waterfall"`) — signed deltas as floating bars
  with running-total transform and connector lines (DEC-026).
  New spec fields: `totalColor`, `sumIndices`, `intermediateSumIndices`,
  `connector`.

## [0.0.0.9] - 2026-08-08

### Added

- `arearange` chart type (DEC-024): pure `{low,high}` point model with band-fill
  between two data paths. Point x-scale with `include_zero=True`, high boundary L→R
  via `_path_d`/`_spline_d`, low boundary R→L, closed band path with configurable
  fill-opacity (default 0.5). Optional bounding strokes when lineWidth > 0 and
  `.sc-point` markers at high edge. Supports monotone spline interpolation.
  Certified renderers in both Python and Go with byte-identical golden SVGs across
  4 examples (basic, spline-range, themed-dark, adversarial). Approved as validation
  infrastructure under DEC-017.
- `columnrange` chart type (DEC-025): floating-bar `{low,high}` mark over discrete
  categories with non-zero-anchored value axis (`include_zero=False`). Band x-scale
  with PAD=0.2 sub-band layout, floating rect from `ypix(max(lo,hi))` with
  `height = max(abs(ypix(lo)-ypix(hi)), 1.0)` min-1px degenerate rule. Supports
  horizontal orientation and grouped multi-series layout. Certified renderers in both
  Python and Go with byte-identical golden SVGs across 5 examples (basic, grouped,
  horizontal, themed-dark, adversarial). Approved as validation infrastructure under
  DEC-017.
- Schema extended with `arearange` and `columnrange` in the type enum.
- Cross-render corpus expanded to 62 examples across 12 chart types.
- A11y data table generalized for range types: Category/Series/Low/High columns.

## [0.0.0.8] - 2026-08-08

### Added

- `error-bar` chart type (DEC-023): vertical whisker marks (stem + two caps) with
  center-value markers on top. Band x-scale with sub-band centering for grouped
  multi-series layout, y-axis spanning `min(low)..max(high)` whisker extents,
  fixed CAP=6.0 half-width and stroke-width=1.5 constants. Supports all four
  marker symbols (circle/square/triangle/diamond). Certified renderers in both
  Python and Go with byte-identical golden SVGs across 5 examples (basic,
  overlay-grouped, asymmetric, themed-dark, adversarial). Approved as validation
  infrastructure under DEC-017.
- Schema extended with `error-bar` in the type enum.
- Cross-render corpus expanded to 53 examples across 10 chart types.
- A11y data table generalized for error-bar: Y/Low/High columns per datum.

## [0.0.0.7] - 2026-08-08

### Added

- `candlestick` chart type (DEC-022): OHLC financial chart with 5 subtypes
  (candlestick, ohlc, hlc, heikin-ashi, hollow). Band x-scale with floating-bar
  primitive, price-driven y-axis (`include_zero=False`), doji min-1px rule, and
  configurable up/down colors. Certified renderers in both Python and Go with
  byte-identical golden SVGs across 5 examples (basic, ohlc, heikin-ashi,
  themed-dark, adversarial). Approved as validation infrastructure under DEC-017.
- Schema extended with `candlestick` in the type enum.
- Cross-render corpus expanded to 48 examples across 9 chart types.

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
