# Research Brief — StoneCharts Design & Customization Layer

> Hand this whole document to a research agent. It is self-contained: it explains
> the project, the constraints, exactly what to research, and the exact deliverable
> format. The agent does **not** need repo access, but paths are given for one that has it.

---

## 1. What StoneCharts is (context)

StoneCharts is an original, **proprietary** (all-rights-reserved) charting library.
It is **not** a fork or copy of any existing library; the Highcharts demo gallery is
used only as a *checklist of which chart types to support*, never as source to copy.

**How it works:**
- A **chart spec** is a language-agnostic recipe (JSON) — `type`, `title`, axes,
  `series` with data + color, etc. (JSON Schema at `spec/chart-spec.schema.json`).
- Each language library (**Python and Go** today; more later) has its **own
  renderer** that turns the spec into **SVG**, following a shared DOM contract
  (`spec/svg-contract.md`): classes like `.sc-chart`, `.sc-series`, `.sc-point`,
  `.sc-legend-item`, and `data-*` attributes.
- A single shared **vanilla-JS runtime** (`runtime/chart-interactions.js`, zero deps)
  enhances that SVG with interactivity (tooltip, crosshair, point highlight,
  legend toggle).
- Output is a **single self-contained interactive HTML file** (inline SVG + CSS + JS).
- **Python and Go currently produce byte-identical SVG** from the same spec, locked
  by golden tests. That parity is a core guarantee.

**Current state:** one chart type done — basic line (`line-basic`).

**Current customization options (the whole surface today):** `title`, `subtitle`,
`width`, `height`, `legend` on/off, `xAxis`/`yAxis` `{title, categories, min, max}`,
per-series `{name, data, color}`. Interactivity is fixed (tooltip/crosshair/
highlight/legend-toggle). Everything else — palette, fonts, gridline colors, line
width/style, markers, gradients, textures, tick formatting, sizing behavior — is
**hardcoded** in the renderers and is what this research is meant to inform.

## 2. Hard constraints (these shape every recommendation)

1. **Original implementation only.** Study other libraries' *concepts and config
   APIs* as reference; never propose copying their code. Cite them as inspiration.
2. **Static-first, self-contained.** The chart must render correctly as pure
   inline **SVG with JavaScript disabled**; JS only *enhances*. So prefer
   techniques that live in SVG/CSS. Clearly flag anything that *requires* JS.
3. **Cross-language expressibility.** Every feature must be describable in the
   shared spec and renderable identically by an independent renderer per language
   (Python, Go, …). No feature that only one language can do. Favor things that are
   deterministic string/number → SVG so byte-identical output stays achievable.
4. **No heavy dependencies.** Output embeds everything; avoid anything that needs a
   browser engine, headless Chrome, or large runtime libs to produce the SVG.
5. **Proprietary.** Palettes/techniques must be free of licensing encumbrance
   (e.g., note if a named palette has license terms).

## 3. What to research (scope)

For **each** area below: what the feature is, the concrete **SVG/CSS technique** to
implement it (element/attribute level), whether it's **static or needs JS**, how
leading libraries expose it in their config (Highcharts, ECharts, Chart.js,
Plotly, Vega-Lite, D3, Observable Plot — as references), and a **proposed spec
shape** (what JSON fields we'd add) that stays cross-language.

**A. Sizing & responsiveness** — fixed vs fluid; SVG `viewBox` + `preserveAspectRatio`;
`width:100%`/container-fit; aspect-ratio lock; min/max size; retina/DPI; auto-margins
computed from label sizes; how to keep it deterministic across languages.

**B. Gradients** — SVG `<linearGradient>`/`<radialGradient>`, stops, direction;
gradient fills for areas/bars and gradient strokes for lines; a clean spec shape
for gradients (stops + angle/type); id/namespacing so multiple charts on a page
don't collide.

**C. Textures / patterns** — SVG `<pattern>` (hatch, diagonal, dots, crosshatch)
for fills; use cases (print, colorblind accessibility, black-and-white); how to
spec a pattern; performance/size cost.

**D. Color & theming** — palette systems (categorical/sequential/diverging);
named **themes** (light/dark/high-contrast) as token sets; theme object structure
and layering (theme < spec overrides); **colorblind-safe** default palettes (give
concrete hex values and note any license); auto-assign vs explicit per series.

**E. Typography** — font family/size/weight/color per element (title, subtitle,
axis, legend, tooltip, data labels); embedding web fonts in a self-contained file
(data-URI `@font-face`) vs system-font stacks; long-label handling (rotate, wrap,
truncate with ellipsis).

**F. Series & marker styling** — line width; dash patterns (`stroke-dasharray`);
line cap/join; **spline/smoothing** (monotone / catmull-rom / basis — with the math
for cubic bezier control points); stepped lines; **markers** (circle/square/
triangle/diamond, size, fill/stroke, show always / on-hover / off); **area fill**
under a line (incl. gradient area); null/gap handling.

**G. Axes / gridlines / ticks** — tick count & interval control; explicit tick
values; **number & date formatting** (decimals, thousands separators, SI prefixes,
currency, %, date patterns — cross-language formatting strategy); scale types
(linear/log/time/category); gridline styling (color/dash/show, zero-line emphasis);
secondary/opposite axis; axis label rotation; reversed axis; **plot lines & bands**
(threshold/target annotations).

**H. Legend** — position (top/right/bottom/left), orientation, alignment, symbol
style, wrapping/pagination for many series, per-item formatting.

**I. Tooltip & interactions** — tooltip templates/formatting, shared-vs-single,
custom HTML; **zoom/pan** approaches on server-rendered SVG (viewBox transform vs
true redraw — pros/cons, and what data/scales the JS runtime would need); brushing;
point/series selection. Mark clearly which need the JS runtime.

**J. Data labels & annotations** — value labels on points/bars (placement,
collision avoidance); free annotations (text/shapes/arrows at data coordinates).

**K. Animation & transitions** — draw-on/enter animations, update transitions;
**SMIL vs CSS vs JS** for SVG animation in a self-contained file (tradeoffs,
support, file size); `prefers-reduced-motion`.

**L. Accessibility** — SVG `<title>`/`<desc>`, ARIA roles/labels, an offscreen
data-table fallback, keyboard navigation, textures for colorblind users, contrast
(WCAG). What's achievable statically vs with JS.

**M. Export** — SVG → PNG/PDF; print CSS; embedding modes. Note which need
external tooling.

**N. Config/spec-model design** — how the leaders structure their options object
(Highcharts `options`, ECharts `option`, Vega-Lite grammar, Chart.js `config`).
Recommend how StoneCharts should split **spec vs theme vs runtime**, defaults and
inheritance, and how to keep the config JSON-schema-first and cross-language.
Which properties belong on the chart, the axis, the series, or a global theme.

## 4. Deliverable (what the agent should produce)

1. **Feature matrix** (the core output), one row per feature:
   `feature | what it is | SVG/CSS technique (element+attrs) | static or needs-JS |
   proposed spec field(s) | cross-language notes | priority (must/should/nice) |
   reference libs`.
2. **Proposed spec + theme structure** — concrete JSON shapes for the new styling/
   theming options (extending `spec/chart-spec.schema.json`), including a `theme`
   object and where per-element style lives.
3. **Concrete SVG recipes** — copy-ready technique snippets (original, illustrative)
   for: a linear + radial gradient fill/stroke, a hatch `<pattern>`, responsive
   `viewBox`, dashed line, each marker shape, spline control-point math, and
   number/date tick formatting.
4. **Colorblind-safe default palettes** — 2–3 categorical palettes (hex values),
   plus a light and dark theme token set, with any licensing notes.
5. **Prioritized roadmap** — what to add first for maximum value at low risk,
   given the static-first + cross-language constraints.
6. **Sources** — cite everything (docs, specs, articles).

## 5. Explicitly out of scope

- Rewriting the architecture (the spec + per-language renderer + shared runtime
  model stays).
- Any chart *type* work (that's a separate track); this is purely styling/design.
- Copying any library's source or bundled assets.

## 6. Repo pointers (only if the agent has access)

Repository root (`github.com/dharmik136/stonecharts`):
`spec/chart-spec.schema.json`, `spec/svg-contract.md`, `runtime/chart-interactions.js`,
`libs/python/stonecharts/charts/line.py`, `libs/go/line.go`,
`charts/line-basic/design.md`, `CHARTS.md`.
