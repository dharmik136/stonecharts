package stonecharts

import (
	"fmt"
	"math"
	"strings"
	"unicode/utf8"
)

type hemicycleRow struct {
	radius float64
	cap    int
}

func hemicycleLayout(total int, rMin, rMax float64) ([]hemicycleRow, float64) {
	if total <= 0 {
		return nil, 2.0
	}

	nRows := int(math.Ceil((-rMin + math.Sqrt(rMin*rMin+2*(rMax-rMin)*float64(total)/math.Pi)) / (rMax - rMin)))
	if nRows < 1 {
		nRows = 1
	}
	if nRows > total {
		nRows = total
	}

	radii := make([]float64, nRows)
	if nRows == 1 {
		radii[0] = 0.5 * (rMin + rMax)
	} else {
		for k := 0; k < nRows; k++ {
			radii[k] = rMin + float64(k)*(rMax-rMin)/float64(nRows-1)
		}
	}

	rawCaps := make([]int, nRows)
	rawTotal := 0
	for k := 0; k < nRows; k++ {
		c := int(math.Floor(math.Pi * radii[k]))
		if c < 1 {
			c = 1
		}
		rawCaps[k] = c
		rawTotal += c
	}

	if rawTotal < total {
		scale := float64(total) / float64(rawTotal)
		if rawTotal == 0 {
			scale = 1
		}
		rawTotal = 0
		for k := 0; k < nRows; k++ {
			c := int(math.Ceil(float64(rawCaps[k]) * scale))
			if c < 1 {
				c = 1
			}
			rawCaps[k] = c
			rawTotal += c
		}
	}

	rows := make([]hemicycleRow, 0, nRows)
	assigned := 0
	for k := 0; k < nRows; k++ {
		cap := rawCaps[k]
		if k == nRows-1 {
			cap = total - assigned
		} else if cap > total-assigned {
			cap = total - assigned
		}
		if cap <= 0 {
			continue
		}
		rows = append(rows, hemicycleRow{radius: radii[k], cap: cap})
		assigned += cap
	}

	rowGap := (rMax - rMin) / float64(nRows)
	if nRows <= 1 {
		rowGap = rMax - rMin
	}
	dotR := rowGap * 0.35
	if dotR < 1.5 {
		dotR = 1.5
	}
	if dotR > 6.0 {
		dotR = 6.0
	}

	return rows, dotR
}

func renderParliamentSVG(spec *ChartSpec) string {
	W := spec.Width
	H := spec.Height
	theme := spec.theme
	palette := theme.Palette

	cid := spec.ID
	if cid == "" {
		cid = "sc"
	}

	a11yAttr := ""
	a11yDesc := ""
	if spec.a11yOn() {
		sum := esc(a11ySummary(spec, "Parliament"))
		a11yAttr = fmt.Sprintf(` role="img" aria-label="%s"`, sum)
		a11yDesc = "<desc>" + sum + "</desc>"
	}

	mTop := 20.0
	if spec.Title != "" {
		mTop += 26
	}
	if spec.Subtitle != "" {
		mTop += 18
	}
	mLeft := 22.0
	mRight := 22.0
	mBottom := 28.0
	if spec.Legend == nil || *spec.Legend {
		mBottom += 18
	}
	if spec.Layout != nil && spec.Layout.Margin != nil {
		mm := spec.Layout.Margin
		if mm.Top != nil {
			mTop = *mm.Top
		}
		if mm.Left != nil {
			mLeft = *mm.Left
		}
		if mm.Right != nil {
			mRight = *mm.Right
		}
		if mm.Bottom != nil {
			mBottom = *mm.Bottom
		}
	}

	plotW := float64(W) - mLeft - mRight
	plotH := float64(H) - mTop - mBottom

	cx := mLeft + plotW/2
	cy := mTop + plotH*0.92

	rMax := math.Min(plotW/2, plotH*0.85)
	rMin := rMax * 0.35

	bg := "#ffffff"
	if theme.Background != "" {
		bg = theme.Background
	}
	fgTitle := theme.TitleColor
	fgSub := theme.SubtitleColor
	fgLegend := theme.LegendTextColor

	var data []float64
	var sName string
	if len(spec.Series) > 0 {
		data = spec.Series[0].Data
		sName = spec.Series[0].Name
	}
	_ = sName

	cats := spec.XAxis.Categories
	nCats := len(data)
	if len(cats) > nCats {
		nCats = len(cats)
	}
	for len(data) < nCats {
		data = append(data, 0)
	}
	for len(cats) < len(data) {
		cats = append(cats, fmt.Sprintf("%d", len(cats)))
	}

	intData := make([]int, nCats)
	total := 0
	for j := 0; j < nCats; j++ {
		v := int(math.Round(data[j]))
		if v < 0 {
			v = 0
		}
		intData[j] = v
		total += v
	}

	rows, dotR := hemicycleLayout(total, rMin, rMax)

	colors := make([]string, nCats)
	for j := 0; j < nCats; j++ {
		colors[j] = palette[j%len(palette)]
	}

	catAssignments := make([]int, 0, total)
	for j := 0; j < nCats; j++ {
		for c := 0; c < intData[j]; c++ {
			catAssignments = append(catAssignments, j)
		}
	}

	var p strings.Builder

	resp := ""
	if spec.Responsive {
		resp = fmt.Sprintf(` style="max-width:%dpx"`, W)
	}
	fmt.Fprintf(&p, `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" class="sc-chart" font-family="Segoe UI,Helvetica,Arial,sans-serif"%s%s>`, W, H, a11yAttr, resp)
	if a11yDesc != "" {
		p.WriteString(a11yDesc)
	}

	fmt.Fprintf(&p, `<defs><clipPath id="%s-clip"><rect x="0" y="0" width="%d" height="%d"/></clipPath></defs>`, esc(cid), W, H)

	fmt.Fprintf(&p, `<rect class="sc-bg" x="0" y="0" width="%d" height="%d" fill="%s"/>`, W, H, bg)

	ty := 18
	if spec.Title != "" {
		fmt.Fprintf(&p, `<text class="sc-title" x="%s" y="%d" text-anchor="middle" font-size="16" font-weight="600" fill="%s">%s</text>`,
			f1(float64(W)/2), ty, fgTitle, esc(spec.Title))
		ty += 20
	}
	if spec.Subtitle != "" {
		fmt.Fprintf(&p, `<text class="sc-subtitle" x="%s" y="%d" text-anchor="middle" font-size="12" fill="%s">%s</text>`,
			f1(float64(W)/2), ty, fgSub, esc(spec.Subtitle))
	}

	dotIdx := 0
	for _, row := range rows {
		for i := 0; i < row.cap; i++ {
			if dotIdx >= total {
				break
			}
			angle := math.Pi - (float64(i)+0.5)*math.Pi/float64(row.cap)
			dx := cx + row.radius*math.Cos(angle)
			dy := cy - row.radius*math.Sin(angle)
			catJ := catAssignments[dotIdx]
			fill := colors[catJ]
			fmt.Fprintf(&p, `<circle class="sc-parliament-dot sc-point" data-category="%d" data-index="%d" data-color="%s" cx="%.1f" cy="%.1f" r="%s" fill="%s"/>`,
				catJ, dotIdx, esc(fill), dx, dy, fmtNum(dotR), esc(fill))
			dotIdx++
		}
	}

	showLegend := spec.Legend == nil || *spec.Legend
	if showLegend {
		legendY := float64(H) - mBottom + 14
		totalLW := nCats * 80
		lx := (float64(W) - float64(totalLW)) / 2
		fmt.Fprintf(&p, `<g class="sc-legend" transform="translate(%.1f,%.1f)">`, lx, legendY)
		for j := 0; j < nCats; j++ {
			catLabel := cats[j]
			tLen := utf8.RuneCountInString(catLabel)
			_ = tLen
			fmt.Fprintf(&p, `<g class="sc-legend-item" data-series="%d" transform="translate(%d,0)">`, j, j*80)
			fmt.Fprintf(&p, `<rect x="0" y="0" width="10" height="10" rx="2" fill="%s"/>`, esc(colors[j]))
			fmt.Fprintf(&p, `<text x="14" y="9" font-size="11" fill="%s">%s</text>`, fgLegend, esc(catLabel))
			p.WriteString("</g>")
		}
		p.WriteString("</g>")
	}

	p.WriteString("</svg>")
	return p.String()
}
