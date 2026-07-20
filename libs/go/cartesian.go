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
	stacking                   string // "" | "normal" | "percent" — frame owns the stacked y-domain
}

// xpix maps a category index i to a pixel x, per the frame's x-scale strategy.
// Both formulas are PINNED (identical in both languages, in this exact
// operation order) so f1 rounding lands ULP-for-ULP identically (§4.3):
//
//	POINT (line/area/scatter-with-categories) — line.go verbatim:
//	    xpix(i) = plotX + plotW*i/(n-1),  and  plotX + plotW/2  when n <= 1
//	    Line MUST keep this exact formula so its bytes do not move.
//	BAND (column/bar):
//	    xpix(i) = plotX + bandWidth()*i + bandWidth()/2   (band center)
//
// The x-label loop calls xpix(i), so labels land under points (point) or band
// centers (band) with no per-chart label code.
func (f *cartesianFrame) xpix(i int) float64 {
	if f.scale == "band" {
		return f.plotX + f.bandWidth()*float64(i) + f.bandWidth()/2
	}
	if f.n <= 1 {
		return f.plotX + f.plotW/2
	}
	return f.plotX + f.plotW*float64(i)/float64(f.n-1)
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
func buildFrame(spec *ChartSpec, noun, xScale string, includeZero bool) *cartesianFrame {
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
	mRight := 22.0
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

	n := 0
	for _, s := range spec.Series {
		if len(s.Data) > n {
			n = len(s.Data)
		}
	}
	cats := spec.XAxis.Categories
	if len(cats) == 0 {
		cats = make([]string, n)
		for i := 0; i < n; i++ {
			cats[i] = strconv.Itoa(i)
		}
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
		}
		if spec.YAxis.Min != nil {
			lo = *spec.YAxis.Min
		}
		if spec.YAxis.Max != nil {
			hi = *spec.YAxis.Max
		}
	}
	yMin, yMax, yTicks := niceTicks(lo, hi, 6)

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
		stacking:    spec.Stacking,
	}
}

// chromeHead — §4.1 HEAD — writes into p, in place, in emission order: <svg>
// open (responsive + fixed) + font-family, <desc>, <defs>, background rect,
// title + subtitle, y gridlines + labels, axis line, x labels, axis titles
// (x + rotated y), crosshair. Bodies moved verbatim from line.go.
func chromeHead(f *cartesianFrame, p *strings.Builder) {
	spec, theme := f.spec, f.theme
	W, H := f.W, f.H
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

	// Axis line.
	p.WriteString(fmt.Sprintf(
		`<line class="sc-axis-line" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>`,
		f1(f.plotX), f1(f.plotY+f.plotH), f1(f.plotX+f.plotW), f1(f.plotY+f.plotH), theme.AxisLineColor))

	// X labels.
	p.WriteString(`<g class="sc-axis sc-axis-x">`)
	for i := 0; i < f.n; i++ {
		lx := f.xpix(i)
		label := strconv.Itoa(i)
		if i < len(f.cats) {
			label = f.cats[i]
		}
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" text-anchor="middle" font-size="11" fill="%s">%s</text>`,
			f1(lx), f1(f.plotY+f.plotH+18), theme.AxisLabelColor, esc(label)))
	}
	p.WriteString(`</g>`)

	// Axis titles.
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

	// Crosshair (JS-driven).
	p.WriteString(fmt.Sprintf(
		`<line class="sc-crosshair" x1="0" y1="%s" x2="0" y2="%s" stroke="%s" stroke-width="1" stroke-dasharray="4 3" style="display:none"/>`,
		f1(f.plotY), f1(f.plotY+f.plotH), theme.CrosshairColor))
}

// chromeTail — §4.1 TAIL — writes into p, in place: legend (bottom-center)
// then </svg>. Bodies moved verbatim from line.go. No trailing newline.
func chromeTail(f *cartesianFrame, p *strings.Builder) {
	spec, theme := f.spec, f.theme

	// Legend.
	if spec.legendOn() && len(spec.Series) > 0 {
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
			p.WriteString(fmt.Sprintf(
				`<rect x="%s" y="%s" width="14" height="4" rx="2" fill="%s"/>`,
				f1(lx), f1(ly-9), color))
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
func renderCartesian(spec *ChartSpec, noun, xScale string, marks marksFn, includeZero bool) string {
	f := buildFrame(spec, noun, xScale, includeZero)
	var p strings.Builder
	chromeHead(f, &p)
	marks(f, &p) // chart appends its <g class="sc-series">…</g> blocks here
	chromeTail(f, &p)
	return p.String()
}
