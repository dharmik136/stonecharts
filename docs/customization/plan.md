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
- The **default** rendering (light theme, no gradient, `responsive:false`) must stay
  **byte-identical to the current `charts/line-basic/golden/basic.svg`**. Do not
  emit new elements (`<defs>`, background `<rect>`) when they'd be empty/implicit.
- A **new visual** (responsive, dashed gridlines, a theme, …) gets its **own new
  golden fixture** — never mutate an existing golden by accident. Each phase names
  exactly which goldens it adds.
- **Deliberate baseline changes are allowed but rare:** Phase 5b intentionally
  added default-on a11y markup (`role`/`aria-label`/`<desc>`) to *every* golden. That
  is the one sanctioned way to change existing goldens — regenerate them all in
  lockstep, verify the diff is exactly the intended change, and re-prove Python==Go.
  "the default stays byte-identical" now means byte-identical to the a11y baseline.

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
5. **Phase 5 — Themes, a11y, deeper interactivity:**
   - **5a Themes ✅ done.** `spec.theme` = `light` (default, byte-identical) / `dark`
     / custom object. Canonical values in `spec/themes/*.json`, baked into both
     renderers and locked to the JSON by a parity test. Threads bg + all text/grid/
     axis/marker-halo colors + palette. New fixture `dark.svg`; light default keeps
     every existing golden byte-identical.
   - **5b a11y ✅ done (default-on).** SVG gets `role="img"` + a **concise** summary
     `aria-label` + a matching `<desc>` (chart type + series names + category range).
     Accessibility rules of record:
     - **Do NOT `aria-describedby` the data table.** Pointing the SVG's description
       at a `<table>` makes screen readers read the whole table as one flattened
       string on focus — overwhelming and unusable. The summary stays short.
     - **The data table is a SEPARATE semantic element** in the HTML (its own
       `<caption>` + column/row headers + every value), visually hidden with the
       `!important` sr-only pattern. A screen-reader user navigates it with standard
       table commands at their own pace — it is not tied to the SVG's description.
     `spec.a11y` (default true); `a11y:false` restores the pre-a11y bytes. Making a11y
     baseline DELIBERATELY regenerated all goldens (diff = purely the a11y markup;
     Python==Go re-proven).
   - **Keyboard navigation ✅ done (runtime).** The chart is a single focus stop
     (tabindex set by the runtime, so the static SVG is unchanged); arrow keys walk
     the points (Left/Right within a series, Up/Down across series, Home/End),
     reusing the live tooltip + crosshair + highlight.
     - **No focus trap.** Tab focuses the chart and the next Tab passes focus on to
       the next element normally; arrows are the only intercepted keys.
     - **Esc collapses the active state without stealing focus** — it clears the
       highlight/tooltip but leaves focus on the SVG root, and bubbles when nothing
       is active (so a parent modal's Esc still works).
     Sighted keyboard users get the visual experience; screen-reader users use the
     separate data table.

## Nits to fix as we touch them
- `legend` will become `oneOf [boolean, object]` when legend layout lands (Phase 5);
  boolean stays valid, default preserves current rendering.
- `curve` enum: only ship values that render (`linear`, `monotone`); no bare `spline`.
