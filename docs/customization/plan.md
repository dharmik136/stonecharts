# Customization Layer — Plan of Record

Approved plan for the styling/theming layer, with the guardrails that protect our
two non-negotiables. Source research: `docs/research/design-customization-brief.md`.

## Non-negotiables (every feature must respect these)
1. **Byte-identical Python/Go output.** Same spec → same SVG bytes, golden-tested.
2. **Static-first & portable.** Renders as pure SVG with JS disabled; JS only enhances.

## Guardrails (hold the line)
- **No server-side text measurement** this era. Ellipsis/wrap/auto-margins need a
  shared font-metrics table to stay parity-safe — deferred. Use fixed heuristics
  (e.g. `len(name)*7`) only.
- **Themes are resolved server-side into concrete SVG attributes** (`fill`/`stroke`
  hex baked in), never CSS variables. CSS-var theming is a browser-only bonus, later.
- **Palettes/themes live in one shared data file** both languages read (like
  `runtime/`), never duplicated per renderer.
- **Forward-compatible spec:** unknown keys are ignored (no `additionalProperties:false`).
- **Web Component / Shadow DOM / imperative API / live re-render = a separate,
  later "Embedding & Integration" track.** Live client re-render implies a JS
  renderer; out of scope here.

## Golden policy (the mechanical trap)
- The **default** rendering (light, no gradient, `responsive:false`) must stay
  **byte-identical to the existing `charts/line-basic/golden/basic.svg`**. Do not
  emit new elements (`<defs>`, background `<rect>`) when they'd be empty/implicit.
- A **new visual** (responsive, dashed gridlines, a theme, …) gets its **own new
  golden fixture** — never mutate an existing golden by accident. Each phase names
  exactly which goldens it adds.

## Roadmap (build in this order — cheap + static first)
1. **Phase 1 — Sizing & gridlines:** `responsive` (viewBox + `preserveAspectRatio`
   + `width:100%`), `yAxis.gridLine {enabled, color, dashStyle}`.  ✅ done
2. **Phase 2 — Line styles & markers:** `series.dashStyle` + `lineWidth`,
   `series.marker {symbol, radius}` (circle/square/triangle/diamond), `series.step`
   (before/after/center).  ✅ done
3. **Phase 3 — Spline:** `series.curve: "monotone"` (Fritsch–Carlson, identical math
   both languages, golden-tested).  ✅ done
4. **Phase 4 — Gradients & patterns:** `<defs>` + gradient/pattern fills.  ✅ done
   `series.color` as a linear gradient (stroke + area), `series.fillOpacity` (area
   under the line → area chart), `series.pattern` (hatch fill), chart `id` namespaces
   `<defs>` ids. Defs emitted only when needed, so `basic.svg` stays byte-identical.
5. **Phase 5 — Themes, a11y, deeper interactivity:** shared `spec/themes/*.json`
   (light/dark, colorblind-safe palette), ARIA/`<desc>`/data-table, keyboard nav.

## Nits to fix as we touch them
- `legend` will become `oneOf [boolean, object]` when legend layout lands (Phase 5);
  boolean stays valid, default preserves current rendering.
- `curve` enum: only ship values that render (`linear`, `monotone`); no bare `spline`.
