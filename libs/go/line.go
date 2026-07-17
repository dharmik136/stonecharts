package peakcharts

import (
	"fmt"
	"strconv"
	"strings"
)

var palette = []string{
	"#2f7ed8", "#f45b5b", "#8bbc21", "#e4a812",
	"#1aadce", "#8e44ad", "#f28f43", "#77a1e5",
}

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

// markerSVG renders one data-point marker. `common` = shared class + data-* attrs.
// Non-circle shapes carry cx/cy attrs so the JS runtime (crosshair) still works.
func markerSVG(symbol string, x, y, r float64, common, color string) string {
	fs := fmt.Sprintf(`fill="%s" stroke="#fff" stroke-width="1"`, color)
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

// renderLineSVG mirrors libs/python/peakcharts/charts/line.py exactly so the two
// libraries emit byte-identical SVG for the same spec (see charts/line-basic/golden).
func renderLineSVG(spec *ChartSpec) string {
	W, H := spec.Width, spec.Height

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

	var p strings.Builder
	if spec.Responsive {
		p.WriteString(fmt.Sprintf(
			`<svg class="pk-chart" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid meet" width="100%%" font-family="Segoe UI, Helvetica, Arial, sans-serif">`,
			W, H))
	} else {
		p.WriteString(fmt.Sprintf(
			`<svg class="pk-chart" xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Segoe UI, Helvetica, Arial, sans-serif">`,
			W, H, W, H))
	}

	ty := 26
	if spec.Title != "" {
		p.WriteString(fmt.Sprintf(
			`<text class="pk-title" x="%s" y="%d" text-anchor="middle" font-size="17" font-weight="600" fill="#1a1a2e">%s</text>`,
			f1(float64(W)/2), ty, esc(spec.Title)))
		ty += 20
	}
	if spec.Subtitle != "" {
		p.WriteString(fmt.Sprintf(
			`<text class="pk-subtitle" x="%s" y="%d" text-anchor="middle" font-size="12" fill="#6b6b80">%s</text>`,
			f1(float64(W)/2), ty, esc(spec.Subtitle)))
	}

	// Y gridlines + labels. Defaults reproduce the built-in look byte-for-byte.
	gridEnabled := spec.YAxis.gridEnabled()
	gridColor := spec.YAxis.gridColor()
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
			`<text x="%s" y="%s" text-anchor="end" font-size="11" fill="#6b6b80">%s</text>`,
			f1(plotX-8), f1(gy+4), esc(fmtNum(tv))))
	}
	p.WriteString(`</g>`)

	// Axis line.
	p.WriteString(fmt.Sprintf(
		`<line class="pk-axis-line" x1="%s" y1="%s" x2="%s" y2="%s" stroke="#b6b6c2" stroke-width="1"/>`,
		f1(plotX), f1(plotY+plotH), f1(plotX+plotW), f1(plotY+plotH)))

	// X labels.
	p.WriteString(`<g class="pk-axis pk-axis-x">`)
	for i := 0; i < n && i < len(cats); i++ {
		lx := xpix(i)
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%s" text-anchor="middle" font-size="11" fill="#6b6b80">%s</text>`,
			f1(lx), f1(plotY+plotH+18), esc(cats[i])))
	}
	p.WriteString(`</g>`)

	// Axis titles.
	if spec.XAxis.Title != "" {
		p.WriteString(fmt.Sprintf(
			`<text x="%s" y="%d" text-anchor="middle" font-size="12" fill="#4a4a5a">%s</text>`,
			f1(plotX+plotW/2), H-6, esc(spec.XAxis.Title)))
	}
	if spec.YAxis.Title != "" {
		yc := plotY + plotH/2
		p.WriteString(fmt.Sprintf(
			`<text x="14" y="%s" text-anchor="middle" font-size="12" fill="#4a4a5a" transform="rotate(-90 14 %s)">%s</text>`,
			f1(yc), f1(yc), esc(spec.YAxis.Title)))
	}

	// Crosshair (JS-driven).
	p.WriteString(fmt.Sprintf(
		`<line class="pk-crosshair" x1="0" y1="%s" x2="0" y2="%s" stroke="#c0c0cc" stroke-width="1" stroke-dasharray="4 3" style="display:none"/>`,
		f1(plotY), f1(plotY+plotH)))

	// Series.
	for si, s := range spec.Series {
		color := s.Color
		if color == "" {
			color = palette[si%len(palette)]
		}
		pts := make([][2]float64, len(s.Data))
		for i, v := range s.Data {
			pts[i] = [2]float64{xpix(i), ypix(v)}
		}
		d := pathD(pts, s.Step)
		lineDashAttr := ""
		if da := dashArray(s.DashStyle); da != "" {
			lineDashAttr = ` stroke-dasharray="` + da + `"`
		}
		p.WriteString(fmt.Sprintf(`<g class="pk-series" data-series="%d">`, si))
		p.WriteString(fmt.Sprintf(
			`<path class="pk-series-line" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"%s/>`,
			si, d, color, fmtNum(s.lineWidth()), lineDashAttr))
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
				p.WriteString(markerSVG(symbol, pt[0], pt[1], radius, common, color))
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
			color := s.Color
			if color == "" {
				color = palette[si%len(palette)]
			}
			p.WriteString(fmt.Sprintf(`<g class="pk-legend-item" data-series="%d">`, si))
			p.WriteString(fmt.Sprintf(
				`<rect x="%s" y="%s" width="14" height="4" rx="2" fill="%s"/>`,
				f1(lx), f1(ly-9), color))
			p.WriteString(fmt.Sprintf(
				`<text x="%s" y="%s" font-size="12" fill="#33334d">%s</text>`,
				f1(lx+20), f1(ly-2), esc(s.Name)))
			p.WriteString(`</g>`)
			lx += est[si] + gap
		}
		p.WriteString(`</g>`)
	}

	p.WriteString(`</svg>`)
	return p.String()
}
