// Shared Cartesian chrome — the substrate every Cartesian/XY chart rides
// (docs/roadmap/chart-families.md §4, charts/_cartesian/README.md). A chart
// renderer supplies ONLY a marks callback; the frame owns everything else —
// margins, scales, ticks, gridlines, axis lines/titles, legend, crosshair,
// background, <defs>, theme resolution, the a11y summary, and the <svg>
// open/close. Chrome bodies were moved VERBATIM out of line.go so the line
// goldens are the frozen witness that the extraction changed nothing (§4.6).
package stonecharts

import (
	"fmt"
	"strconv"
	"strings"
	"unicode/utf8"
)

// dashArray maps a dashStyle name to an SVG stroke-dasharray value ("" = solid).
// SHARED, not duplicated (§4.7 #4): gridline chrome and the series-line mark
// both call this one function so "5 5"/"2 3" can't drift.
func dashArray(style string) string {
	switch style {
	case "dashed":
		return "5 5"
	case "dotted":
		return "2 3"
	default:
		return ""
	}
}

// gradientDef mirrors _cartesian.py gradient_def: a <linearGradient> with
// x1,y1->x2,y2 direction and offset/color/opacity stops.
func gradientDef(gid string, g *Gradient) string {
	var b strings.Builder
	b.WriteString(`<linearGradient id="` + gid + `" x1="` + fmtNum(g.x1()) +
		`" y1="` + fmtNum(g.y1()) + `" x2="` + fmtNum(g.x2()) + `" y2="` + fmtNum(g.y2()) + `">`)
	for _, st := range g.Stops {
		b.WriteString(`<stop offset="` + fmtNum(st.Offset) + `" stop-color="` + esc(st.Color) + `"`)
		if st.Opacity != nil {
			b.WriteString(` stop-opacity="` + fmtNum(*st.Opacity) + `"`)
		}
		b.WriteString(`/>`)
	}
	b.WriteString(`</linearGradient>`)
	return b.String()
}

// patternDef mirrors _cartesian.py pattern_def: a diagonal hatch tile.
func patternDef(pid string, pat *Pattern) string {
	sz := fmtNum(pat.size())
	var b strings.Builder
	b.WriteString(`<pattern id="` + pid + `" patternUnits="userSpaceOnUse" width="` + sz +
		`" height="` + sz + `" patternTransform="rotate(` + fmtNum(pat.angle()) + `)">`)
	if pat.Background != "" {
		b.WriteString(`<rect width="` + sz + `" height="` + sz + `" fill="` + esc(pat.Background) + `"/>`)
	}
	b.WriteString(`<line x1="0" y1="0" x2="0" y2="` + sz + `" stroke="` + esc(pat.hatchColor()) +
		`" stroke-width="` + fmtNum(pat.strokeWidth()) + `"/></pattern>`)
	return b.String()
}

// seriesStyle holds the resolved paint refs for one series.
//
// Caution (§4.3) — the no-area sentinel is per-language: Go uses `areaFill
// string` where "" means "no area", while Python uses `area_fill:
// Optional[str]` where None means "no area". Safe ONLY while a real fill value
// is never "" and never a meaningful None; new fields must not overload these.
type seriesStyle struct {
	stroke   string // line/edge stroke ref (hex or url(#grad))
	solid    string // representative solid for markers/legend/data-color
	areaFill string // "" = no area fill; else hex/url(#grad)/url(#pat)
	areaOp   string // fill-opacity attribute (with leading space) or ""
	fill     string // resolved BAR paint: url(#pat) -> url(#grad) -> solid hex
	//                (populated by the defs pre-pass; UNREAD by line marks)
}

// a11ySummary mirrors _cartesian.py a11y_summary: a screen-reader chart
// summary. noun is the BARE word ("Line", "Column"), not "Line chart" — called
// with "Line" it reproduces "Line chart with N series…" byte-for-byte.
func a11ySummary(spec *ChartSpec, noun string) string {
	names := make([]string, len(spec.Series))
	for i, s := range spec.Series {
		names[i] = s.Name
	}
	parts := []string{}
	if spec.Title != "" {
		parts = append(parts, spec.Title+".")
	}
	parts = append(parts, fmt.Sprintf("%s chart with %d series: %s.", noun, len(spec.Series), strings.Join(names, ", ")))
	if len(spec.XAxis.Categories) > 0 {
		c := spec.XAxis.Categories
		parts = append(parts, fmt.Sprintf("Categories from %s to %s.", c[0], c[len(c)-1]))
	}
	return strings.Join(parts, " ")
}

// cartesianFrame is everything a cartesian chart needs but its marks — built
// once per render by buildFrame(). Marks read geometry through xpix / ypix /
// bandWidth and never recompute a scale (§5.2). Mirrors the Python
// CartesianFrame dataclass field-for-field.
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
	includeZero                bool   // value-axis zero-anchor (see buildFrame)
	orientation                string // "vertical" | "horizontal"
	stacking                   string // "" | "normal" | "percent" — frame owns the stacked y-domain
	y2Min                      float64
	y2Max                      float64
	y2Ticks                    []float64
	secondaryAxis              *Axis
	xMin, xMax                 float64 // LINEAR scale only (scatter) — free numeric x-domain
	xTicks                     []float64
	slotLefts                  []float64 // variwide only — per-category slot left edge
	slotWidths                 []float64 // variwide only — per-category slot width
	sgBaseline                 []float64   // streamgraph only
	sgCumBottom                [][]float64 // streamgraph only
	sgCumTop                   [][]float64 // streamgraph only
}

// xpix maps a category index (or, under LINEAR scale, a numeric x-VALUE) to a
// pixel x. All formulas are PINNED (identical in both languages, in this
// exact operation order) so f1 rounding lands ULP-for-ULP identically (§4.3):
//
//	LINEAR (scatter, §3.3 Rank 3) — a free numeric x-domain, mirrors ypix:
//	    xpix(v) = plotX + plotW*(v - xMin)/(xMax - xMin)
//	    Degenerate domain (xMax == xMin) pins to plot center BEFORE the
//	    divide, identically to valuePix's existing y-degenerate guard.
//	POINT (line/area) — line.go verbatim:
//	    xpix(i) = plotX + plotW*i/(n-1),  and  plotX + plotW/2  when n <= 1
//	    Line MUST keep this exact formula so its bytes do not move.
//	BAND (column/bar):
//	    xpix(i) = plotX + bandWidth()*i + bandWidth()/2   (band center)
//
// The x-label loop calls xpix(i), so labels land under points (point) or band
// centers (band) with no per-chart label code.
func (f *cartesianFrame) xpix(i float64) float64 {
	if f.scale == "linear" || f.scale == "numeric" {
		if f.xMax == f.xMin {
			return f.plotX + f.plotW/2
		}
		return f.plotX + f.plotW*(i-f.xMin)/(f.xMax-f.xMin)
	}
	if f.scale == "band" {
		return f.plotX + f.bandWidth()*i + f.bandWidth()/2
	}
	if f.scale == "variwide" {
		idx := int(i)
		if idx < 0 || idx >= len(f.slotLefts) {
			return f.plotX + f.plotW/2
		}
		return f.slotLefts[idx] + f.slotWidths[idx]/2
	}
	if f.n <= 1 {
		return f.plotX + f.plotW/2
	}
	return f.plotX + f.plotW*i/float64(f.n-1)
}

// ypix maps a value v to a pixel y — moved from line.go verbatim.
func (f *cartesianFrame) ypix(v float64) float64 {
	return f.plotY + f.plotH*(1-(v-f.yMin)/(f.yMax-f.yMin))
}

// bandWidth is the BAND scale per-category slot width. PINNED: plotW / n.
// The mark drawer builds sub-bands from bandWidth() with the §3.2 constants
// (PAD = 0.2, K = len(series)), evaluated in exactly the pinned order.
func (f *cartesianFrame) bandWidth() float64 {
	return f.plotW / float64(f.n)
}

// slotWidth returns the variwide per-category slot width. Returns 0 if out of range.
func (f *cartesianFrame) slotWidth(i int) float64 {
	if i < 0 || i >= len(f.slotWidths) {
		return 0.0
	}
	return f.slotWidths[i]
}

// bandHeight is the BAND scale per-category slot height for horizontal charts.
func (f *cartesianFrame) bandHeight() float64 {
	return f.plotH / float64(f.n)
}

// bandCenter returns the pixel center of category i on the band axis.
func (f *cartesianFrame) bandCenter(i int) float64 {
	if f.orientation == "horizontal" {
		return f.plotY + f.bandHeight()*float64(i) + f.bandHeight()/2
	}
	return f.xpix(float64(i))
}

// valuePix maps a numeric value to the value-axis pixel.
func (f *cartesianFrame) valuePix(v float64) float64 {
	if f.orientation == "horizontal" {
		if f.yMax == f.yMin {
			return f.plotX + f.plotW/2
		}
		return f.plotX + f.plotW*(v-f.yMin)/(f.yMax-f.yMin)
	}
	return f.ypix(v)
}

// valueZero returns the pixel coordinate for the zero baseline on the value axis.
func (f *cartesianFrame) valueZero() float64 { return f.valuePix(0.0) }

// ypix2 maps a secondary-axis value to a pixel y (used by combo dual-axis charts).
func (f *cartesianFrame) ypix2(v float64) float64 {
	if f.y2Max == f.y2Min {
		return f.plotY + f.plotH/2
	}
	return f.plotY + f.plotH*(1-(v-f.y2Min)/(f.y2Max-f.y2Min))
}

// marksFn — a chart supplies ONLY this: append its marks for one plot into the
// shared accumulator p.
type marksFn func(f *cartesianFrame, p *strings.Builder)

// buildFrame does the §4.2 "frame build" phase: margins, plot rect, n/cats,
// the value-axis range + niceTicks, and the <defs> pre-pass that resolves each
// seriesStyle (stroke, solid, areaFill, areaOp, fill) + cid + defs + the a11y
// summary (parameterized by noun).
//
// includeZero (PINNED semantics, §3.2 caveat / §4.2):
//
//	true  -> value axis / y baseline (line/column/bar/area): FORCE 0 into the
//	         domain, i.e. lo = min(values, 0), hi = max(values, 0). Line passes
//	         true and this reproduces its existing domain exactly.
//	false -> free numeric x (and free numeric y) scatter/bubble axis: domain
//	         from the DATA ONLY (empty data -> 0,0).
func buildFrame(spec *ChartSpec, noun, xScale string, includeZero bool, orientation string) *cartesianFrame {
	W, H := int(spec.Width), int(spec.Height)
	theme := spec.theme
	if theme == nil {
		t := lightTheme()
		theme = &t
	}
	palette := theme.Palette
	a11yAttr, a11yDesc := "", ""
	if spec.a11yOn() {
		s := esc(a11ySummary(spec, noun))
		a11yAttr = ` role="img" aria-label="` + s + `"`
		a11yDesc = "<desc>" + s + "</desc>"
	}

	mTop := 20.0
	if spec.Title != "" {
		mTop += 26
	}
	if spec.Subtitle != "" {
		mTop += 18
	}
	mLeft := 52.0
	if spec.YAxis.Title != "" {
		mLeft = 62
	}
	hasSecondary := spec.SecondaryYAxis != nil
	mRight := 22.0
	if hasSecondary {
		if spec.SecondaryYAxis.Title != "" {
			mRight = 62
		} else {
			mRight = 52
		}
	}
	mBottom := 46.0
	if spec.legendOn() {
		mBottom += 18
	}
	if spec.XAxis.Title != "" {
		mBottom += 18
	}
	if spec.Layout != nil && spec.Layout.Margin != nil {
		if spec.Layout.Margin.Top != nil {
			mTop = *spec.Layout.Margin.Top
		}
		if spec.Layout.Margin.Left != nil {
			mLeft = *spec.Layout.Margin.Left
		}
		if spec.Layout.Margin.Right != nil {
			mRight = *spec.Layout.Margin.Right
		}
		if spec.Layout.Margin.Bottom != nil {
			mBottom = *spec.Layout.Margin.Bottom
		}
	}

	plotX := mLeft
	plotY := mTop
	plotW := float64(W) - mLeft - mRight
	plotH := float64(H) - mTop - mBottom

	// LINEAR scale (scatter, §3.3 Rank 3): series carry point-model
	// DataPoints instead of a plain []float64 — n/values/x-domain extraction
	// branches here, additively, so every ELSE branch below (line/column/
	// area/bar) is byte-for-byte the same code that ran before scatter
	// existed.
	isPointModel := xScale == "linear"

	n := 0
	if isPointModel {
		for _, s := range spec.Series {
			if len(s.DataPoints) > n {
				n = len(s.DataPoints)
			}
		}
	} else {
		for _, s := range spec.Series {
			if len(s.Data) > n {
				n = len(s.Data)
			}
		}
	}
	cats := spec.XAxis.Categories
	if len(cats) == 0 {
		cats = make([]string, n)
		for i := 0; i < n; i++ {
			cats[i] = strconv.Itoa(i)
		}
	}

	xMin, xMax := 0.0, 0.0
	var xTicks []float64
	if isPointModel {
		xFirst := true
		xLo, xHi := 0.0, 0.0
		for _, s := range spec.Series {
			for _, d := range s.DataPoints {
				if xFirst {
					xLo, xHi = d.X, d.X
					xFirst = false
					continue
				}
				if d.X < xLo {
					xLo = d.X
				}
				if d.X > xHi {
					xHi = d.X
				}
			}
		}
		if spec.XAxis.Min != nil {
			xLo = *spec.XAxis.Min
		}
		if spec.XAxis.Max != nil {
			xHi = *spec.XAxis.Max
		}
		xMin, xMax, xTicks = niceTicks(xLo, xHi, 6)
	} else if xScale == "numeric" {
		xFirst := true
		xLo, xHi := 0.0, 0.0
		for _, s := range spec.Series {
			for _, v := range s.Data {
				if xFirst {
					xLo, xHi = v, v
					xFirst = false
					continue
				}
				if v < xLo {
					xLo = v
				}
				if v > xHi {
					xHi = v
				}
			}
		}
		if spec.XAxis.Min != nil {
			xLo = *spec.XAxis.Min
		}
		if spec.XAxis.Max != nil {
			xHi = *spec.XAxis.Max
		}
		xMin, xMax, xTicks = niceTicks(xLo, xHi, 6)
	}

	// Value-axis range. Stacking changes the domain to per-category totals.
	lo, hi := 0.0, 0.0
	if spec.Stacking == "normal" || spec.Stacking == "percent" {
		if spec.Stacking == "percent" {
			lo = 0.0
			hi = 100.0
		} else {
			posTotals := make([]float64, n)
			negTotals := make([]float64, n)
			for _, s := range spec.Series {
				for i, v := range s.Data {
					if i >= n {
						continue
					}
					if v >= 0 {
						posTotals[i] += v
					} else {
						negTotals[i] += v
					}
				}
			}
			lo = 0.0
			hi = 0.0
			for _, t := range negTotals {
				if t < lo {
					lo = t
				}
			}
			for _, t := range posTotals {
				if t > hi {
					hi = t
				}
			}
		}
		if spec.YAxis.Min != nil {
			lo = *spec.YAxis.Min
		}
		if spec.YAxis.Max != nil {
			hi = *spec.YAxis.Max
		}
	} else if includeZero {
		for _, s := range spec.Series {
			for _, v := range s.Data {
				if v < lo {
					lo = v
				}
				if v > hi {
					hi = v
				}
			}
			for _, v := range s.Low {
				if v < lo {
					lo = v
				}
				if v > hi {
					hi = v
				}
			}
			for _, v := range s.High {
				if v < lo {
					lo = v
				}
				if v > hi {
					hi = v
				}
			}
		}
		if spec.YAxis.Min != nil {
			lo = *spec.YAxis.Min
		}
		if spec.YAxis.Max != nil {
			hi = *spec.YAxis.Max
		}
	} else if isPointModel {
		// Free y-domain via DataPoints (scatter always passes includeZero=false;
		// unlike s.Data, DataPoints is populated regardless of bare-number,
		// positional, or object input form — see Series.UnmarshalJSON).
		first := true
		for _, s := range spec.Series {
			for _, d := range s.DataPoints {
				if first {
					lo, hi = d.Y, d.Y
					first = false
					continue
				}
				if d.Y < lo {
					lo = d.Y
				}
				if d.Y > hi {
					hi = d.Y
				}
			}
		}
		if spec.YAxis.Min != nil {
			lo = *spec.YAxis.Min
		}
		if spec.YAxis.Max != nil {
			hi = *spec.YAxis.Max
		}
	} else {
		first := true
		for _, s := range spec.Series {
			for _, v := range s.Data {
				if first {
					lo, hi = v, v
					first = false
					continue
				}
				if v < lo {
					lo = v
				}
				if v > hi {
					hi = v
				}
			}
			for _, v := range s.Low {
				if first {
					lo, hi = v, v
					first = false
					continue
				}
				if v < lo {
					lo = v
				}
				if v > hi {
					hi = v
				}
			}
			for _, v := range s.High {
				if first {
					lo, hi = v, v
					first = false
					continue
				}
				if v < lo {
					lo = v
				}
				if v > hi {
					hi = v
				}
			}
		}
		if spec.YAxis.Min != nil {
			lo = *spec.YAxis.Min
		}
		if spec.YAxis.Max != nil {
			hi = *spec.YAxis.Max
		}
	}
	// Streamgraph baseline-offset: pre-compute so chrome renders correct y-domain.
	var sgBaseline []float64
	var sgCumBottom, sgCumTop [][]float64
	if spec.Type == "streamgraph" && n > 0 {
		K := len(spec.Series)
		allVals := make([][]float64, K)
		for k := 0; k < K; k++ {
			vals := make([]float64, 0, n)
			for i, v := range spec.Series[k].Data {
				if i >= n {
					break
				}
				vals = append(vals, v)
			}
			allVals[k] = vals
		}
		sgTotals := make([]float64, n)
		for k := 0; k < K; k++ {
			for i := 0; i < len(allVals[k]); i++ {
				sgTotals[i] += allVals[k][i]
			}
		}
		running := make([]float64, n)
		sgCumBottom = make([][]float64, K)
		sgCumTop = make([][]float64, K)
		for k := 0; k < K; k++ {
			bot := make([]float64, n)
			copy(bot, running)
			top := make([]float64, len(allVals[k]))
			for i := range allVals[k] {
				top[i] = running[i] + allVals[k][i]
			}
			sgCumBottom[k] = bot
			sgCumTop[k] = top
			copy(running, top)
		}
		offsetMode := spec.Offset
		if offsetMode == "" {
			offsetMode = "wiggle"
		}
		sgBaseline = make([]float64, n)
		if offsetMode == "silhouette" {
			for i := 0; i < n; i++ {
				sgBaseline[i] = -sgTotals[i] / 2.0
			}
		} else {
			sgBaseline[0] = 0.0
			yAcc := 0.0
			for i := 1; i < n; i++ {
				numW := 0.0
				denW := 0.0
				for k := 0; k < K; k++ {
					ctI := 0.0
					if i < len(sgCumTop[k]) {
						ctI = sgCumTop[k][i]
					}
					ctPrev := 0.0
					if i-1 < len(sgCumTop[k]) {
						ctPrev = sgCumTop[k][i-1]
					}
					moveK := ctI - ctPrev
					weightK := moveK / 2.0
					for j := 0; j < k; j++ {
						ctJI := 0.0
						if i < len(sgCumTop[j]) {
							ctJI = sgCumTop[j][i]
						}
						ctJPrev := 0.0
						if i-1 < len(sgCumTop[j]) {
							ctJPrev = sgCumTop[j][i-1]
						}
						weightK += ctJI - ctJPrev
					}
					numW += weightK * moveK
					denW += moveK
				}
				if denW != 0.0 {
					yAcc -= numW / denW
				}
				sgBaseline[i] = yAcc
			}
		}
		if spec.YAxis.Min == nil {
			lo = sgBaseline[0]
			for i := 1; i < n; i++ {
				if sgBaseline[i] < lo {
					lo = sgBaseline[i]
				}
			}
		}
		if spec.YAxis.Max == nil {
			hi = sgBaseline[0] + sgTotals[0]
			for i := 1; i < n; i++ {
				if sgBaseline[i]+sgTotals[i] > hi {
					hi = sgBaseline[i] + sgTotals[i]
				}
			}
		}
	}

	yMin, yMax, yTicks := niceTicks(lo, hi, 6)

	if xScale == "numeric" {
		yTicks = nil
	}

	// Secondary y-axis domain (combo dual-axis).
	y2Min, y2Max := 0.0, 0.0
	var y2Ticks []float64
	if hasSecondary {
		var y2vals []float64
		for si := range spec.Series {
			if spec.Series[si].YAxis == 1 {
				y2vals = append(y2vals, spec.Series[si].Data...)
			}
		}
		y2lo := 0.0
		y2hi := 0.0
		if len(y2vals) > 0 {
			y2lo = y2vals[0]
			y2hi = y2vals[0]
			for _, v := range y2vals[1:] {
				if v < y2lo {
					y2lo = v
				}
				if v > y2hi {
					y2hi = v
				}
			}
			if y2lo > 0 {
				y2lo = 0
			}
			if y2hi < 0 {
				y2hi = 0
			}
		}
		if spec.SecondaryYAxis.Min != nil {
			y2lo = *spec.SecondaryYAxis.Min
		}
		if spec.SecondaryYAxis.Max != nil {
			y2hi = *spec.SecondaryYAxis.Max
		}
		y2Min, y2Max, y2Ticks = niceTicks(y2lo, y2hi, 6)
	}

	// Resolve per-series styling and collect <defs>. Defs are emitted ONLY when
	// a series needs them, so default output stays byte-identical. `fill` is the
	// resolved BAR paint (pattern -> gradient -> solid hex); line ignores it.
	cid := esc(spec.ID) // namespaces <defs> ids; escaped so a hostile id can't inject
	var defs strings.Builder
	styles := make([]seriesStyle, len(spec.Series))
	for si := range spec.Series {
		s := &spec.Series[si]
		grad, solidHex := s.colorSpec()
		var stroke, fillColor, solid string
		if grad != nil {
			gid := cid + "-grad-" + strconv.Itoa(si)
			defs.WriteString(gradientDef(gid, grad))
			stroke = "url(#" + gid + ")"
			fillColor = stroke
			if len(grad.Stops) > 0 {
				solid = esc(grad.Stops[0].Color)
			} else {
				solid = esc(palette[si%len(palette)])
			}
		} else if solidHex != "" {
			c := esc(solidHex)
			stroke, fillColor, solid = c, c, c
		} else {
			c := esc(palette[si%len(palette)])
			stroke, fillColor, solid = c, c, c
		}
		fill := fillColor // bar paint: url(#grad) for a gradient, else the solid hex
		var areaFill, areaOp string
		if s.Pattern != nil {
			pid := cid + "-pat-" + strconv.Itoa(si)
			defs.WriteString(patternDef(pid, s.Pattern))
			areaFill = "url(#" + pid + ")"
			fill = areaFill // pattern wins the bar paint
		} else if s.FillOpacity > 0 {
			areaFill = fillColor
			areaOp = ` fill-opacity="` + fmtNum(s.FillOpacity) + `"`
		}
		styles[si] = seriesStyle{stroke: stroke, solid: solid, areaFill: areaFill, areaOp: areaOp, fill: fill}
	}

	// Variwide slot layout — cumulative-width x-scale (mirrors Python build_frame).
	var slotLefts, slotWidths []float64
	if xScale == "variwide" {
		var rawWidths []float64
		if len(spec.Series) > 0 && len(spec.Series[0].Widths) > 0 {
			rawWidths = spec.Series[0].Widths
		}
		if rawWidths != nil {
			clamped := make([]float64, n)
			for i := 0; i < n; i++ {
				if i < len(rawWidths) {
					v := rawWidths[i]
					if v < 0 {
						v = 0
					}
					clamped[i] = v
				}
			}
			totalZ := 0.0
			for _, z := range clamped {
				totalZ += z
			}
			if totalZ <= 0 {
				for i := range clamped {
					clamped[i] = 1.0
				}
				totalZ = float64(n)
			}
			slotLefts = make([]float64, n)
			slotWidths = make([]float64, n)
			cum := 0.0
			for i, z := range clamped {
				sw := plotW * z / totalZ
				slotLefts[i] = plotX + cum
				slotWidths[i] = sw
				cum += sw
			}
		} else {
			slotLefts = make([]float64, n)
			slotWidths = make([]float64, n)
			sw := 0.0
			if n > 0 {
				sw = plotW / float64(n)
			}
			for i := 0; i < n; i++ {
				slotLefts[i] = plotX + sw*float64(i)
				slotWidths[i] = sw
			}
		}
	}

	return &cartesianFrame{
		spec:  spec,
		W:     W,
		H:     H,
		theme: theme,
		plotX: plotX, plotY: plotY, plotW: plotW, plotH: plotH,
		n:    n,
		cats: cats,
		yMin: yMin, yMax: yMax, yTicks: yTicks,
		cid:      cid,
		styles:   styles,
		defs:     defs.String(),
		a11yAttr: a11yAttr, a11yDesc: a11yDesc,
		scale:       xScale,
		includeZero: includeZero,
		orientation: orientation,
		stacking:    spec.Stacking,
		xMin:        xMin, xMax: xMax, xTicks: xTicks,
		slotLefts:  slotLefts,
		slotWidths: slotWidths,
		sgBaseline:  sgBaseline,
		sgCumBottom: sgCumBottom,
		sgCumTop:    sgCumTop,
		secondaryAxis: spec.SecondaryYAxis,
		y2Min:         y2Min, y2Max: y2Max, y2Ticks: y2Ticks,
	}
}

// chromeHead — §4.1 HEAD — writes into p, in place, in emission order: <svg>
// open (responsive + fixed) + font-family, <desc>, <defs>, background rect,
// title + subtitle, y gridlines + labels, axis line, x labels, axis titles
// (x + rotated y), crosshair. Bodies moved verbatim from line.go.
func chromeHead(f *cartesianFrame, p *strings.Builder) {
	spec, theme := f.spec, f.theme
	W, H := f.W, f.H
	plotX, plotY, plotW, plotH := f.plotX, f.plotY, f.plotW, f.plotH
	if spec.Responsive {
		p.WriteString(fmt.Sprintf(
			`<svg class="sc-chart"%s xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid meet" width="100%%" font-family="Segoe UI, Helvetica, Arial, sans-serif">`,
			f.a11yAttr, W, H))
	} else {
		p.WriteString(fmt.Sprintf(
			`<svg class="sc-chart"%s xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Segoe UI, Helvetica, Arial, sans-serif">`,
			f.a11yAttr, W, H, W, H))
	}

	// Accessible description (screen readers; role="img" makes the chart one image).
	if f.a11yDesc != "" {
		p.WriteString(f.a11yDesc)
	}

	// Gradient / pattern defs (only present when a series needs them).
	if f.defs != "" {
		p.WriteString(`<defs>`)
		p.WriteString(f.defs)
		p.WriteString(`</defs>`)
	}

	// Background (only when the theme sets one; light theme -> none).
	if theme.Background != "" {
		p.WriteString(fmt.Sprintf(
			`<rect class="sc-bg" x="0" y="0" width="%d" height="%d" fill="%s"/>`,
			W, H, theme.Background))
	}

	ty := 26
	if spec.Title != "" {
		p.WriteString(fmt.Sprintf(
			`<text class="sc-title" x="%s" y="%d" text-anchor="middle" font-size="17" font-weight="600" fill="%s">%s</text>`,
			f1(float64(W)/2), ty, theme.TitleColor, esc(spec.Title)))
		ty += 20
	}
	if spec.Subtitle != "" {
		p.WriteString(fmt.Sprintf(
			`<text class="sc-subtitle" x="%s" y="%d" text-anchor="middle" font-size="12" fill="%s">%s</text>`,
			f1(float64(W)/2), ty, theme.SubtitleColor, esc(spec.Subtitle)))
	}

	if f.orientation == "horizontal" {
		gridEnabled := spec.YAxis.gridEnabled()
		gridColor := spec.YAxis.gridColorOr(theme.GridColor)
		gridDashAttr := ""
		if da := dashArray(spec.YAxis.gridDashStyle()); da != "" {
			gridDashAttr = ` stroke-dasharray="` + da + `"`
		}
		p.WriteString(`<g class="sc-axis sc-axis-x">`)
		for _, tv := range f.yTicks {
			gx := f.valuePix(tv)
			if gridEnabled {
				p.WriteString(fmt.Sprintf(
					`<line class="sc-gridline" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"%s/>`,
					f1(gx), f1(plotY), f1(gx), f1(plotY+plotH), gridColor, gridDashAttr))
			}
			p.WriteString(fmt.Sprintf(
				`<text x="%s" y="%s" text-anchor="middle" font-size="11" fill="%s">%s</text>`,
				f1(gx), f1(plotY+plotH+18), theme.AxisLabelColor, esc(fmtNum(tv))))
		}
		p.WriteString(`</g>`)

		p.WriteString(fmt.Sprintf(
			`<line class="sc-axis-line" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>`,
			f1(plotX), f1(plotY+plotH), f1(plotX+plotW), f1(plotY+plotH), theme.AxisLineColor))

		p.WriteString(`<g class="sc-axis sc-axis-y">`)
		for i := 0; i < f.n; i++ {
			label := strconv.Itoa(i)
			if i < len(f.cats) {
				label = f.cats[i]
			}
			gy := f.bandCenter(i)
			p.WriteString(fmt.Sprintf(
				`<text x="%s" y="%s" text-anchor="end" font-size="11" fill="%s">%s</text>`,
				f1(plotX-8), f1(gy+4), theme.AxisLabelColor, esc(label)))
		}
		p.WriteString(`</g>`)

		if spec.XAxis.Title != "" {
			yc := f.plotY + f.plotH/2
			p.WriteString(fmt.Sprintf(
				`<text x="14" y="%s" text-anchor="middle" font-size="12" fill="%s" transform="rotate(-90 14 %s)">%s</text>`,
				f1(yc), theme.AxisTitleColor, f1(yc), esc(spec.XAxis.Title)))
		}
		if spec.YAxis.Title != "" {
			p.WriteString(fmt.Sprintf(
				`<text x="%s" y="%d" text-anchor="middle" font-size="12" fill="%s">%s</text>`,
				f1(plotX+plotW/2), H-6, theme.AxisTitleColor, esc(spec.YAxis.Title)))
		}
	} else {
		// Y gridlines + labels. Defaults reproduce the built-in look byte-for-byte.
		gridEnabled := spec.YAxis.gridEnabled()
		gridColor := spec.YAxis.gridColorOr(theme.GridColor)
		gridDashAttr := ""
		if da := dashArray(spec.YAxis.gridDashStyle()); da != "" {
			gridDashAttr = ` stroke-dasharray="` + da + `"`
		}
		p.WriteString(`<g class="sc-axis sc-axis-y">`)
		for _, tv := range f.yTicks {
			gy := f.ypix(tv)
			if gridEnabled {
				p.WriteString(fmt.Sprintf(
					`<line class="sc-gridline" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"%s/>`,
					f1(f.plotX), f1(gy), f1(f.plotX+f.plotW), f1(gy), gridColor, gridDashAttr))
			}
			p.WriteString(fmt.Sprintf(
				`<text x="%s" y="%s" text-anchor="end" font-size="11" fill="%s">%s</text>`,
				f1(f.plotX-8), f1(gy+4), theme.AxisLabelColor, esc(fmtNum(tv))))
		}
		p.WriteString(`</g>`)

		p.WriteString(fmt.Sprintf(
			`<line class="sc-axis-line" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>`,
			f1(f.plotX), f1(f.plotY+f.plotH), f1(f.plotX+f.plotW), f1(f.plotY+f.plotH), theme.AxisLineColor))

		// X labels. LINEAR scale (scatter, §3.3 Rank 3) draws numeric ticks +
		// optional vertical gridlines, mirroring the y-axis; every other scale
		// keeps the original categorical-label loop unchanged.
		if f.scale == "linear" || f.scale == "numeric" {
			xGridEnabled := spec.XAxis.GridLine != nil && spec.XAxis.GridLine.Enabled != nil && *spec.XAxis.GridLine.Enabled
			xGridColor := theme.GridColor
			if spec.XAxis.GridLine != nil && spec.XAxis.GridLine.Color != "" {
				xGridColor = spec.XAxis.GridLine.Color
			}
			xGridDashAttr := ""
			if spec.XAxis.GridLine != nil {
				if da := dashArray(spec.XAxis.GridLine.DashStyle); da != "" {
					xGridDashAttr = ` stroke-dasharray="` + da + `"`
				}
			}
			if xGridEnabled {
				p.WriteString(`<g class="sc-gridlines-x">`)
				for _, tv := range f.xTicks {
					gx := f.xpix(tv)
					p.WriteString(fmt.Sprintf(
						`<line class="sc-gridline" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"%s/>`,
						f1(gx), f1(f.plotY), f1(gx), f1(f.plotY+f.plotH), xGridColor, xGridDashAttr))
				}
				p.WriteString(`</g>`)
			}
			p.WriteString(`<g class="sc-axis sc-axis-x">`)
			for _, tv := range f.xTicks {
				lx := f.xpix(tv)
				p.WriteString(fmt.Sprintf(
					`<text x="%s" y="%s" text-anchor="middle" font-size="11" fill="%s">%s</text>`,
					f1(lx), f1(f.plotY+f.plotH+18), theme.AxisLabelColor, esc(fmtNum(tv))))
			}
			p.WriteString(`</g>`)
		} else {
			p.WriteString(`<g class="sc-axis sc-axis-x">`)
			for i := 0; i < f.n; i++ {
				lx := f.xpix(float64(i))
				label := strconv.Itoa(i)
				if i < len(f.cats) {
					label = f.cats[i]
				}
				p.WriteString(fmt.Sprintf(
					`<text x="%s" y="%s" text-anchor="middle" font-size="11" fill="%s">%s</text>`,
					f1(lx), f1(f.plotY+f.plotH+18), theme.AxisLabelColor, esc(label)))
			}
			p.WriteString(`</g>`)
		}

		if spec.XAxis.Title != "" {
			p.WriteString(fmt.Sprintf(
				`<text x="%s" y="%d" text-anchor="middle" font-size="12" fill="%s">%s</text>`,
				f1(f.plotX+f.plotW/2), H-6, theme.AxisTitleColor, esc(spec.XAxis.Title)))
		}
		if spec.YAxis.Title != "" {
			yc := f.plotY + f.plotH/2
			p.WriteString(fmt.Sprintf(
				`<text x="14" y="%s" text-anchor="middle" font-size="12" fill="%s" transform="rotate(-90 14 %s)">%s</text>`,
				f1(yc), theme.AxisTitleColor, f1(yc), esc(spec.YAxis.Title)))
		}
	}

	if f.secondaryAxis != nil && len(f.y2Ticks) > 0 {
		sideLeft := f.secondaryAxis.Opposite != nil && !*f.secondaryAxis.Opposite
		axX := plotX - 8
		anchor := "end"
		if !sideLeft {
			axX = plotX + plotW + 8
			anchor = "start"
		}
		p.WriteString(`<g class="sc-axis sc-axis-y2">`)
		for _, tv := range f.y2Ticks {
			p.WriteString(fmt.Sprintf(
				`<text x="%s" y="%s" text-anchor="%s" font-size="11" fill="%s">%s</text>`,
				f1(axX), f1(f.ypix2(tv)+4), anchor, theme.AxisLabelColor, esc(fmtNum(tv))))
		}
		p.WriteString(`</g>`)
		if f.secondaryAxis.Title != "" {
			mid := f.plotY + f.plotH/2
			if sideLeft {
				p.WriteString(fmt.Sprintf(
					`<text x="14" y="%s" text-anchor="middle" font-size="12" fill="%s" transform="rotate(-90 14 %s)">%s</text>`,
					f1(mid), theme.AxisTitleColor, f1(mid), esc(f.secondaryAxis.Title)))
			} else {
				p.WriteString(fmt.Sprintf(
					`<text x="%d" y="%s" text-anchor="middle" font-size="12" fill="%s" transform="rotate(90 %d %s)">%s</text>`,
					W-14, f1(mid), theme.AxisTitleColor, W-14, f1(mid), esc(f.secondaryAxis.Title)))
			}
		}
	}

	// Crosshair (hidden until a point is hovered; driven by the JS runtime).
	p.WriteString(fmt.Sprintf(
		`<line class="sc-crosshair" x1="0" y1="%s" x2="0" y2="%s" stroke="%s" stroke-width="1" stroke-dasharray="4 3" style="display:none"/>`,
		f1(plotY), f1(plotY+plotH), theme.CrosshairColor))
}

// chromeTail — §4.1 TAIL — writes into p, in place: legend (bottom-center)
// then </svg>. Bodies moved verbatim from line.go. No trailing newline.
func chromeTail(f *cartesianFrame, p *strings.Builder) {
	spec, theme := f.spec, f.theme

	// Legend.
	if spec.legendOn() && len(spec.Series) > 0 && spec.Type == "waterfall" {
		// Three-swatch direction key: Increase / Decrease / Total
		upColor := spec.UpColor
		if upColor == "" {
			upColor = "#3f9b6a"
		}
		downColor := spec.DownColor
		if downColor == "" {
			downColor = "#d65f5f"
		}
		totalColor := spec.TotalColor
		if totalColor == "" {
			totalColor = "#4b6cb7"
		}
		hasTotal := len(spec.SumIndices) > 0 || len(spec.IntermediateSumIndices) > 0

		type legendEntry struct{ label, color string }
		items := []legendEntry{{"Increase", upColor}, {"Decrease", downColor}}
		if hasTotal {
			items = append(items, legendEntry{"Total", totalColor})
		}

		gap := 22.0
		est := make([]float64, len(items))
		total := 0.0
		for i, item := range items {
			est[i] = float64(utf8.RuneCountInString(item.label)*7 + 26)
			total += est[i]
		}
		total += gap * float64(len(items)-1)
		lx := f.plotX + (f.plotW-total)/2
		lyBase := 10
		if spec.XAxis.Title != "" {
			lyBase += 18
		}
		ly := float64(f.H - lyBase)

		p.WriteString(`<g class="sc-legend">`)
		for idx, item := range items {
			p.WriteString(fmt.Sprintf(`<g class="sc-legend-item" data-series="%d">`, idx))
			p.WriteString(fmt.Sprintf(
				`<rect x="%s" y="%s" width="14" height="4" rx="2" fill="%s"/>`,
				f1(lx), f1(ly-9), item.color))
			p.WriteString(fmt.Sprintf(
				`<text x="%s" y="%s" font-size="12" fill="%s">%s</text>`,
				f1(lx+20), f1(ly-2), theme.LegendTextColor, esc(item.label)))
			p.WriteString(`</g>`)
			lx += est[idx] + gap
		}
		p.WriteString(`</g>`)
	} else if spec.legendOn() && len(spec.Series) > 0 {
		gap := 22.0
		est := make([]float64, len(spec.Series))
		total := 0.0
		for i, s := range spec.Series {
			est[i] = float64(utf8.RuneCountInString(s.Name)*7 + 26)
			total += est[i]
		}
		total += gap * float64(len(spec.Series)-1)
		lx := f.plotX + (f.plotW-total)/2
		lyBase := 10
		if spec.XAxis.Title != "" {
			lyBase += 18
		}
		ly := float64(f.H - lyBase)
		p.WriteString(`<g class="sc-legend">`)
		for si, s := range spec.Series {
			color := f.styles[si].solid
			p.WriteString(fmt.Sprintf(`<g class="sc-legend-item" data-series="%d">`, si))
			if spec.Type == "combo" && s.Type == "line" {
				p.WriteString(fmt.Sprintf(
					`<rect x="%s" y="%s" width="14" height="2" rx="1" fill="%s"/>`,
					f1(lx), f1(ly-8), color))
			} else {
				p.WriteString(fmt.Sprintf(
					`<rect x="%s" y="%s" width="14" height="4" rx="2" fill="%s"/>`,
					f1(lx), f1(ly-9), color))
			}
			p.WriteString(fmt.Sprintf(
				`<text x="%s" y="%s" font-size="12" fill="%s">%s</text>`,
				f1(lx+20), f1(ly-2), theme.LegendTextColor, esc(s.Name)))
			p.WriteString(`</g>`)
			lx += est[si] + gap
		}
		p.WriteString(`</g>`)
	}

	p.WriteString(`</svg>`)
}

// renderCartesian orchestrates head -> (chart's marks) -> tail through ONE
// shared accumulator p (a *strings.Builder), making byte-identity true BY
// CONSTRUCTION (same writes, same order, same buffer as the original
// single-buffer line renderer). Returns p.String() with NO trailing newline
// (goldens carry no trailing newline; UTF-8, no BOM).
//
// A per-chart renderer is a one-line delegation, e.g.:
//
//	renderCartesian(spec, "Line", "point", lineMarks, true)
//	renderCartesian(spec, "Column", "band", columnMarks, true)
func renderCartesian(spec *ChartSpec, noun, xScale string, marks marksFn, includeZero bool, orientation ...string) string {
	orient := "vertical"
	if len(orientation) > 0 && orientation[0] != "" {
		orient = orientation[0]
	}
	f := buildFrame(spec, noun, xScale, includeZero, orient)
	var p strings.Builder
	chromeHead(f, &p)
	marks(f, &p) // chart appends its <g class="sc-series">…</g> blocks here
	chromeTail(f, &p)
	return p.String()
}
