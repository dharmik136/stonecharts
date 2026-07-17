package peakcharts

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

// dashArray maps a dashStyle name to an SVG stroke-dasharray value ("" = solid).
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

// pathD builds the line path 'd'. step in {"", before, after, center}.
// Mirrors line.py _path_d (parts joined by a single space).
func pathD(pts [][2]float64, step string) string {
	parts := make([]string, 0, len(pts)*2)
	if step == "" {
		for i, pt := range pts {
			pre := "L"
			if i == 0 {
				pre = "M"
			}
			parts = append(parts, pre+f1(pt[0])+" "+f1(pt[1]))
		}
		return strings.Join(parts, " ")
	}
	for i, pt := range pts {
		x, y := pt[0], pt[1]
		if i == 0 {
			parts = append(parts, "M"+f1(x)+" "+f1(y))
			continue
		}
		px, py := pts[i-1][0], pts[i-1][1]
		switch step {
		case "before":
			parts = append(parts, "L"+f1(px)+" "+f1(y), "L"+f1(x)+" "+f1(y))
		case "center":
			mx := (px + x) / 2
			parts = append(parts, "L"+f1(mx)+" "+f1(py), "L"+f1(mx)+" "+f1(y), "L"+f1(x)+" "+f1(y))
		default: // after
			parts = append(parts, "L"+f1(x)+" "+f1(py), "L"+f1(x)+" "+f1(y))
		}
	}
	return strings.Join(parts, " ")
}

// splineD builds a monotone cubic spline path (Fritsch-Carlson). Identical math
// to _spline_d in line.py so both languages emit byte-identical curves.
func splineD(pts [][2]float64) string {
	n := len(pts)
	if n < 3 {
		return pathD(pts, "")
	}
	xs := make([]float64, n)
	ys := make([]float64, n)
	for i, p := range pts {
		xs[i], ys[i] = p[0], p[1]
	}
	delta := make([]float64, n-1)
	for i := 0; i < n-1; i++ {
		delta[i] = (ys[i+1] - ys[i]) / (xs[i+1] - xs[i])
	}
	m := make([]float64, n)
	m[0] = delta[0]
	m[n-1] = delta[n-2]
	for i := 1; i < n-1; i++ {
		if delta[i-1]*delta[i] <= 0 {
			m[i] = 0
		} else {
			m[i] = (delta[i-1] + delta[i]) / 2
		}
	}
	for i := 0; i < n-1; i++ {
		if delta[i] == 0 {
			m[i] = 0
			m[i+1] = 0
		} else {
			a := m[i] / delta[i]
			b := m[i+1] / delta[i]
			s := a*a + b*b
			if s > 9 {
				t := 3.0 / math.Sqrt(s)
				m[i] = t * a * delta[i]
				m[i+1] = t * b * delta[i]
			}
		}
	}
	parts := make([]string, 0, n)
	parts = append(parts, "M"+f1(xs[0])+" "+f1(ys[0]))
	for i := 0; i < n-1; i++ {
		h := xs[i+1] - xs[i]
		c1x := xs[i] + h/3
		c1y := ys[i] + m[i]*h/3
		c2x := xs[i+1] - h/3
		c2y := ys[i+1] - m[i+1]*h/3
		parts = append(parts,
			"C"+f1(c1x)+" "+f1(c1y)+" "+f1(c2x)+" "+f1(c2y)+" "+f1(xs[i+1])+" "+f1(ys[i+1]))
	}
	return strings.Join(parts, " ")
}

// markerSVG renders one data-point marker. `common` = shared class + data-* attrs.
// Non-circle shapes carry cx/cy attrs so the JS runtime (crosshair) still works.
func markerSVG(symbol string, x, y, r float64, common, color, halo string) string {
	fs := fmt.Sprintf(`fill="%s" stroke="%s" stroke-width="1"`, color, halo)
	switch symbol {
	case "square":
		return fmt.Sprintf(`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" %s/>`,
			common, f1(x), f1(y), f1(x-r), f1(y-r), f1(2*r), f1(2*r), fs)
	case "triangle":
		poly := f1(x) + "," + f1(y-r) + " " + f1(x-r) + "," + f1(y+r) + " " + f1(x+r) + "," + f1(y+r)
		return fmt.Sprintf(`<polygon %s cx="%s" cy="%s" points="%s" %s/>`, common, f1(x), f1(y), poly, fs)
	case "diamond":
		poly := f1(x) + "," + f1(y-r) + " " + f1(x+r) + "," + f1(y) + " " + f1(x) + "," + f1(y+r) + " " + f1(x-r) + "," + f1(y)
		return fmt.Sprintf(`<polygon %s cx="%s" cy="%s" points="%s" %s/>`, common, f1(x), f1(y), poly, fs)
	default: // circle
		return fmt.Sprintf(`<circle %s cx="%s" cy="%s" r="%s" %s/>`, common, f1(x), f1(y), fmtNum(r), fs)
	}
}

// gradientDef mirrors line.py _gradient_def: a <linearGradient> with x1,y1->x2,y2
// direction and offset/color/opacity stops.
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

// patternDef mirrors line.py _pattern_def: a diagonal hatch tile.
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
type seriesStyle struct {
	stroke   string // line stroke ref (hex or url(#grad))
	solid    string // representative solid for markers/legend/data-color
	areaFill string // "" = no area fill; else hex/url(#grad)/url(#pat)
	areaOp   string // fill-opacity attribute (with leading space) or ""
}

// a11ySummary mirrors line.py _a11y_summary: a screen-reader chart summary.
func a11ySummary(spec *ChartSpec) string {
	names := make([]string, len(spec.Series))
	for i, s := range spec.Series {
		names[i] = s.Name
	}
	parts := []string{}
	if spec.Title != "" {
		parts = append(parts, spec.Title+".")
	}
	parts = append(parts, fmt.Sprintf("Line chart with %d series: %s.", len(spec.Series), strings.Join(names, ", ")))
	if len(spec.XAxis.Categories) > 0 {
		c := spec.XAxis.Categories
		parts = append(parts, fmt.Sprintf("Categories from %s to %s.", c[0], c[len(c)-1]))
	}
	return strings.Join(parts, " ")
}

// renderLineSVG mirrors libs/python/peakcharts/charts/line.py exactly so the two
// libraries emit byte-identical SVG for the same spec (see charts/line-basic/golden).
func renderLineSVG(spec *ChartSpec) string {
	W, H := spec.Width, spec.Height
	theme := spec.theme
	if theme == nil {
		t := lightTheme()
		theme = &t
	}
	palette := theme.Palette
	a11yAttr, a11yDesc := "", ""
	if spec.a11yOn() {
		s := esc(a11ySummary(spec))
		a11yAttr = ` role="img" aria-label="` + s + `"`
		a11yDesc = "<desc>" + s + "</desc>"
	}

	mTop := 20
	if spec.Title != "" {
		mTop += 26
	}
	if spec.Subtitle != "" {
		mTop += 18
	}
	mLeft := 52
	if spec.YAxis.Title != "" {
		mLeft = 62
	}
	mRight := 22
	mBottom := 46
	legend := spec.legendOn()
	if legend {
		mBottom += 18
	}
	if spec.XAxis.Title != "" {
		mBottom += 18
	}

	plotX := float64(mLeft)
	plotY := float64(mTop)
	plotW := float64(W - mLeft - mRight)
	plotH := float64(H - mTop - mBottom)

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

	// Y range: min/max across all series, always including 0.
	lo, hi := 0.0, 0.0
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
	yMin, yMax, yTicks := niceTicks(lo, hi, 6)

	xpix := func(i int) float64 {
		if n <= 1 {
			return plotX + plotW/2
		}
		return plotX + plotW*float64(i)/float64(n-1)
	}
	ypix := func(v float64) float64 {
		return plotY + plotH*(1-(v-yMin)/(yMax-yMin))
	}

	// Resolve per-series styling and collect <defs>. Defs are emitted ONLY when a
	// series needs them, so default output stays byte-identical.
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
		var areaFill, areaOp string
		if s.Pattern != nil {
			pid := cid + "-pat-" + strconv.Itoa(si)
			defs.WriteString(patternDef(pid, s.Pattern))
			areaFill = "url(#" + pid + ")"
		} else if s.FillOpacity > 0 {
			areaFill = fillColor
			areaOp = ` fill-opacity="` + fmtNum(s.FillOpacity) + `"`
		}
		styles[si] = seriesStyle{stroke: stroke, solid: solid, areaFill: areaFill, areaOp: areaOp}
	}

	var p strings.Builder
	if spec.Responsive {
		p.WriteString(fmt.Sprintf(
			`<svg class="pk-chart"%s xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid meet" width="100%%" font-family="Segoe UI, Helvetica, Arial, sans-serif">`,
			a11yAttr, W, H))
	} else {
		p.WriteString(fmt.Sprintf(
			`<svg class="pk-chart"%s xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Segoe UI, Helvetica, Arial, sans-serif">`,
			a11yAttr, W, H, W, H))
	}

	// Accessible description (screen readers; role="img" makes the chart one image).
	if a11yDesc != "" {
		p.WriteString(a11yDesc)
	}

	// Gradient / pattern defs (only present when a series needs them).
	if defs.Len() > 0 {
		p.WriteString(`<defs>`)
		p.WriteString(defs.String())
		p.WriteString(`</defs>`)
	}

	// Background (only when the theme sets one; light theme -> none).
	if theme.Background != "" {
		p.WriteString(fmt.Sprintf(
			`<rect class="pk-bg" x="0" y="0" width="%d" height="%d" fill="%s"/>`,
			W, H, theme.Background))
	}

	ty := 26
	if spec.Title != "" {
		p.WriteString(fmt.Sprintf(
			`<text class="pk-title" x="%s" y="%d" text-anchor="middle" font-size="17" font-weight="600" fill="%s">%s</text>`,
			f1(float64(W)/2), ty, theme.TitleColor, esc(spec.Title)))
		ty += 20
	}
	if spec.Subtitle != "" {
		p.WriteString(fmt.Sprintf(
			`<text class="pk-subtitle" x="%s" y="%d" text-anchor="middle" font-size="12" fill="%s">%s</text>`,
			f1(float64(W)/2), ty, theme.SubtitleColor, esc(spec.Subtitle)))
	}

	// Y gridlines + labels. Defaults reproduce the built-in look byte-for-byte.
	gridEnabled := spec.YAxis.gridEnabled()
	gridColor := spec.YAxis.gridColorOr(theme.GridColor)
	gridDashAttr := ""
	if da := dashArray(spec.YAxis.gridDashStyle()); da != "" {
		gridDashAttr = ` stroke-dasharray="` + da + `"`
	}
	p.WriteString(`<g class="pk-axis pk-axis-y">`)
	for _, tv := range yTicks {
		gy := ypix(tv)
		if gridEnabled {
			p.WriteString(fmt.Sprintf(
				`<line class="pk-gridline" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"%s/>`,
				f1(plotX), f1(gy), f1(plotX+plotW), f1(gy), gridColor, gridDashAttr))
		}
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" text-anchor="end" font-size="11" fill="%s">%s</text>`,
			f1(plotX-8), f1(gy+4), theme.AxisLabelColor, esc(fmtNum(tv))))
	}
	p.WriteString(`</g>`)

	// Axis line.
	p.WriteString(fmt.Sprintf(
		`<line class="pk-axis-line" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>`,
		f1(plotX), f1(plotY+plotH), f1(plotX+plotW), f1(plotY+plotH), theme.AxisLineColor))

	// X labels.
	p.WriteString(`<g class="pk-axis pk-axis-x">`)
	for i := 0; i < n && i < len(cats); i++ {
		lx := xpix(i)
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" text-anchor="middle" font-size="11" fill="%s">%s</text>`,
			f1(lx), f1(plotY+plotH+18), theme.AxisLabelColor, esc(cats[i])))
	}
	p.WriteString(`</g>`)

	// Axis titles.
	if spec.XAxis.Title != "" {
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%d" text-anchor="middle" font-size="12" fill="%s">%s</text>`,
			f1(plotX+plotW/2), H-6, theme.AxisTitleColor, esc(spec.XAxis.Title)))
	}
	if spec.YAxis.Title != "" {
		yc := plotY + plotH/2
		p.WriteString(fmt.Sprintf(
			`<text x="14" y="%s" text-anchor="middle" font-size="12" fill="%s" transform="rotate(-90 14 %s)">%s</text>`,
			f1(yc), theme.AxisTitleColor, f1(yc), esc(spec.YAxis.Title)))
	}

	// Crosshair (JS-driven).
	p.WriteString(fmt.Sprintf(
		`<line class="pk-crosshair" x1="0" y1="%s" x2="0" y2="%s" stroke="%s" stroke-width="1" stroke-dasharray="4 3" style="display:none"/>`,
		f1(plotY), f1(plotY+plotH), theme.CrosshairColor))

	// Series.
	for si, s := range spec.Series {
		st := styles[si]
		color := st.solid
		pts := make([][2]float64, len(s.Data))
		for i, v := range s.Data {
			pts[i] = [2]float64{xpix(i), ypix(v)}
		}
		var d string
		if s.Curve == "monotone" {
			d = splineD(pts)
		} else {
			d = pathD(pts, s.Step)
		}
		lineDashAttr := ""
		if da := dashArray(s.DashStyle); da != "" {
			lineDashAttr = ` stroke-dasharray="` + da + `"`
		}
		p.WriteString(fmt.Sprintf(`<g class="pk-series" data-series="%d">`, si))
		// Area fill (under the line, drawn first so the line sits on top).
		if st.areaFill != "" && len(pts) > 0 {
			base := ypix(0.0)
			areaD := d + " L" + f1(pts[len(pts)-1][0]) + " " + f1(base) +
				" L" + f1(pts[0][0]) + " " + f1(base) + " Z"
			p.WriteString(fmt.Sprintf(
				`<path class="pk-series-area" data-series="%d" d="%s" fill="%s"%s stroke="none"/>`,
				si, areaD, st.areaFill, st.areaOp))
		}
		p.WriteString(fmt.Sprintf(
			`<path class="pk-series-line" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"%s/>`,
			si, d, st.stroke, fmtNum(s.lineWidth()), lineDashAttr))
		if s.markerEnabled() {
			radius := s.markerRadius()
			radiusHover := radius + 2.5
			symbol := s.markerSymbol()
			for i, pt := range pts {
				xlabel := strconv.Itoa(i)
				if i < len(cats) {
					xlabel = cats[i]
				}
				common := fmt.Sprintf(
					`class="pk-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
					si, esc(s.Name), esc(xlabel), esc(fmtNum(s.Data[i])), color, fmtNum(radius), fmtNum(radiusHover))
				p.WriteString(markerSVG(symbol, pt[0], pt[1], radius, common, color, theme.MarkerHalo))
			}
		}
		p.WriteString(`</g>`)
	}

	// Legend.
	if legend && len(spec.Series) > 0 {
		gap := 22.0
		est := make([]float64, len(spec.Series))
		total := 0.0
		for i, s := range spec.Series {
			est[i] = float64(len(s.Name)*7 + 26)
			total += est[i]
		}
		total += gap * float64(len(spec.Series)-1)
		lx := plotX + (plotW-total)/2
		lyBase := 10
		if spec.XAxis.Title != "" {
			lyBase += 18
		}
		ly := float64(H - lyBase)
		p.WriteString(`<g class="pk-legend">`)
		for si, s := range spec.Series {
			color := styles[si].solid
			p.WriteString(fmt.Sprintf(`<g class="pk-legend-item" data-series="%d">`, si))
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
	return p.String()
}
