// TEMPLATE — not compiled; the real module lands in libs/ during the §4 extraction.
//
// skeleton_cartesian.go — a SKELETON of the shared Cartesian chrome module that the
// §4 EXTRACTION CONTRACT (docs/roadmap/chart-families.md) mandates. It sketches the
// cartesianFrame struct, buildFrame, and renderCartesian ONLY as signatures + doc
// comments that pin the parity rules verbatim. It lives here (charts/_cartesian/,
// OUTSIDE libs/) as a design reference and is deliberately NOT wired into the build:
// the real, compiled module is `libs/go/cartesian.go` (flat `package peakcharts`),
// created with Rank 1 / Column when the shared chrome is extracted out of line.go.
//
// This file has NO package clause and imports nothing on purpose — it must never be
// compiled, registered in render.go, or pinned by a golden. The line reference
// renderer (libs/go/line.go) is the source of the verbatim chrome bodies; this file
// only fixes the shapes and the pinned math so the eventual extraction reproduces
// line's bytes exactly (§4.6 byte-identity gate). Bodies are elided as `panic(...)`
// placeholders solely to mark "not implemented here".
//
// The Go skeleton mirrors skeleton_cartesian.py field-for-field: both languages parse
// and lay out identically, and every number flows through the same parity-locked
// formatters (fmtNum / f1) so Python == Go byte-for-byte.

// ─────────────────────────────────────────────────────────────────────────────
// seriesStyle — moved from line.go 161–167, PLUS the new `fill` field (resolved bar
// paint) the extraction adds. `fill` is populated by the defs pre-pass but UNREAD by
// line marks, so line bytes do not move.
//
// Caution (§4.3) — the no-area sentinel is per-language: Go uses `areaFill string`
// where "" means "no area", while Python uses `area_fill Optional[str]` where None
// means "no area". Safe ONLY while a real fill value is never "" and never a
// meaningful None; new fields must not overload these sentinels.
type seriesStyle struct {
	stroke   string // line/edge stroke ref (hex or url(#grad))
	solid    string // representative solid for markers / legend / data-color
	areaFill string // "" = no area fill; else hex / url(#grad) / url(#pat)
	areaOp   string // fill-opacity attribute (with leading space) or ""
	fill     string // resolved BAR paint: url(#pat) -> url(#grad) -> solid hex
}

// cartesianFrame — everything a cartesian chart needs but its marks; built once per
// render by buildFrame(). Marks read geometry through xpix / ypix / bandWidth and
// never recompute a scale (§5.2). Mirrors the Python CartesianFrame dataclass.
type cartesianFrame struct {
	spec                       *ChartSpec
	W, H                       int
	theme                      *Theme
	plotX, plotY, plotW, plotH float64
	n                          int
	cats                       []string
	yMin, yMax                 float64
	yTicks                     []float64
	cid                        string
	styles                     []seriesStyle
	defs                       string
	a11yAttr, a11yDesc         string
	scale                      string // "point" | "band"
	includeZero                bool   // value-axis zero-anchor (see buildFrame doc)
	stacking                   string // "" | "normal" | "percent" — frame owns stacked y-domain
}

// xpix maps a category index i to a pixel x, per the frame's x-scale strategy.
//
// The ONE generalization allowed during extraction is a first-class x-scale strategy.
// Both formulas below are PINNED (identical in both languages, in this exact operation
// order) so f1 rounding lands ULP-for-ULP identically:
//
// POINT scale (line/area/scatter-with-categories) — line.go 264–269 verbatim:
//
//	xpix(i) = plotX + plotW*i/(n-1),  and  plotX + plotW/2  when n <= 1
//
// Line MUST keep this exact formula so its bytes do not move.
//
// BAND scale (column/bar) — §4.3 pinned formula, this operation order:
//
//	bandWidth() = plotW / n
//	xpix(i)     = plotX + bandWidth()*i + bandWidth()/2   (band center)
//
// The x-label loop calls frame.xpix(i), so labels land under points (point) or band
// centers (band) with no per-chart label code.
func (f *cartesianFrame) xpix(i int) float64 { panic("TEMPLATE — not compiled") }

// ypix maps a value v to a pixel y — line.go 270–272 verbatim:
//
//	ypix(v) = plotY + plotH * (1 - (v - yMin) / (yMax - yMin))
func (f *cartesianFrame) ypix(v float64) float64 { panic("TEMPLATE — not compiled") }

// bandWidth is the BAND scale per-category slot width. PINNED: `plotW / float64(n)`.
//
// The mark drawer builds sub-bands from bandWidth() with the §3.2 constants, evaluated
// in EXACTLY this order so f1 rounding matches ULP-for-ULP in Py and Go (PAD and K are
// fixed constants, not per-author choices):
//
//	bandWidth  = plotW / n
//	xpix(i)    = plotX + bandWidth*i + bandWidth/2      // band center
//	PAD        = 0.2                                    // single group-padding constant
//	groupW     = bandWidth*(1 - PAD)
//	K          = len(series)
//	barW       = groupW / K
//	left(i, k) = xpix(i) - groupW/2 + barW*k
//
// (Basic single-series => K=1 => one centered bar of width groupW.)
func (f *cartesianFrame) bandWidth() float64 { panic("TEMPLATE — not compiled") }

// marksFn — a chart supplies ONLY this: append its marks for one plot into the shared
// accumulator p.
type marksFn func(f *cartesianFrame, p *strings.Builder)

// buildFrame does the §4.2 "frame build" phase: margins, plot rect, n/cats, the
// value-axis range + niceTicks, xpix/ypix, and the <defs> pre-pass that resolves each
// seriesStyle (stroke, solid, areaFill, areaOp, fill) + cid + defs + the a11y summary
// (parameterized by noun — the BARE word "Line"/"Column", not "Line chart"; called
// with "Line" it reproduces "Line chart with N series…" byte-for-byte, line.go 179).
//
// includeZero (PINNED semantics, §3.2 caveat / §4.2):
//
//	true  -> value axis / y baseline (column/bar/area): FORCE 0 into the domain, i.e.
//	         lo = min(values, 0), hi = max(values, 0). Line passes true and this
//	         reproduces its existing domain exactly, so line bytes do not move.
//	false -> free numeric x (and free numeric y) scatter/bubble axis: domain from the
//	         DATA ONLY. Do NOT carry the y-baseline zero-anchor into a free axis, or a
//	         scatter with x in [100,200] is wrongly anchored at 0. Both languages would
//	         be wrong identically and still pass byte-parity — so the flag is explicit.
//
// FRAME-OWNED STACKED Y-DOMAIN (the pinned parity rule this frame exists to enforce):
// buildFrame READS the spec's stacking mode and computes the stacking-aware y-domain
// ON THE FRAME — the marks never recompute a scale. Verbatim (§4.2): "For
// stacked/percent the frame computes the y-max from the max column TOTAL (cumulative
// in the pinned summation order), NOT the per-datum max — the frame owns this, the
// marks never recompute a scale." And (§3.2 Stacking): "The frame (not the marks) owns
// the stacking-aware y-domain: for stacked/percent the y-max is the max column total,
// not the per-datum max." The SUMMATION ORDER is pinned: accumulate series in index
// order; the frame's cumulative y-domain uses that same summation order in both
// languages so cumulative floats and %g output match. (Percent mode: the value axis
// becomes niceTicks(0, 100, 6).)
func buildFrame(spec *ChartSpec, noun, xScale string, includeZero bool) *cartesianFrame {
	panic("TEMPLATE — not compiled")
}

// chromeHead — §4.1 HEAD — write into p, in place, in emission order: <svg> open
// (responsive + fixed) + font-family, <desc>, <defs>, background rect, title +
// subtitle, y gridlines + labels, axis line, x labels, axis titles (x + rotated y),
// crosshair. Verbatim bodies moved from line.go 312–407.
func chromeHead(f *cartesianFrame, p *strings.Builder) { panic("TEMPLATE — not compiled") }

// chromeTail — §4.1 TAIL — write into p, in place: legend (bottom-center) then </svg>.
// Verbatim bodies moved from line.go 458–491. No trailing newline.
func chromeTail(f *cartesianFrame, p *strings.Builder) { panic("TEMPLATE — not compiled") }

// renderCartesian orchestrates head -> (chart's marks) -> tail through ONE shared
// accumulator p (a *strings.Builder), making byte-identity true BY CONSTRUCTION (same
// writes, same order, same buffer as today's single-buffer line renderer). Returns
// p.String() with NO trailing newline (goldens carry no trailing newline; UTF-8, no
// BOM).
//
// A per-chart renderer is a one-line delegation, e.g. the line reference becomes:
//
//	renderCartesian(spec, "Line", "point", lineMarks, true)
//
// and Column lands as just another marks callback:
//
//	renderCartesian(spec, "Column", "band", columnMarks, true)  // value axis => includeZero true
func renderCartesian(spec *ChartSpec, noun, xScale string, marks marksFn, includeZero bool) string {
	f := buildFrame(spec, noun, xScale, includeZero)
	var p strings.Builder
	chromeHead(f, &p)
	marks(f, &p) // chart appends its <g class="pk-series">…</g> blocks here
	chromeTail(f, &p)
	return p.String()
}

// Chrome helpers moved verbatim from line.go (bodies elided in this SKELETON):
//   a11ySummary(spec, noun) — was a11ySummary; "Line" -> noun (the BARE word).
//   gradientDef(gid, g), patternDef(pid, pat) — moved verbatim.
//   dashArray(style) — SHARED, not duplicated (§4.7 #4): gridline chrome and the
//     series-line mark both call this ONE function so "5 5"/"2 3" can't drift; line
//     imports it from here.
