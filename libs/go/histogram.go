package stonecharts

import (
	"fmt"
	"math"
	"strings"
)

func renderHistogramSVG(spec *ChartSpec) string {
	edges, heights, counts, totals := computeHistBins(spec)
	mod := prepareHistSpec(spec, edges, heights)
	marks := func(f *cartesianFrame, p *strings.Builder) {
		histogramMarks(f, p, edges, heights, counts, totals, spec)
	}
	return renderCartesian(mod, "Histogram", "linear", marks, true)
}

func computeHistBins(spec *ChartSpec) (edges []float64, heights [][]float64, counts [][]float64, totals []int) {
	if spec.PreBinned {
		edges = make([]float64, len(spec.XAxis.BinEdges))
		copy(edges, spec.XAxis.BinEdges)
		k := len(edges) - 1
		if k <= 0 {
			return []float64{0, 1}, [][]float64{{0}}, [][]float64{{0}}, []int{0}
		}
		for _, s := range spec.Series {
			sc := make([]float64, k)
			for b := 0; b < k && b < len(s.Data); b++ {
				sc[b] = s.Data[b]
			}
			counts = append(counts, sc)
			n := 0.0
			for _, c := range sc {
				n += c
			}
			totals = append(totals, int(n))
			if spec.Normalization == "density" {
				h := make([]float64, k)
				for b := 0; b < k; b++ {
					w := edges[b+1] - edges[b]
					nw := n * w
					if nw == 0 {
						h[b] = 0
					} else {
						h[b] = sc[b] / nw
					}
				}
				heights = append(heights, h)
			} else {
				h := make([]float64, k)
				copy(h, sc)
				heights = append(heights, h)
			}
		}
		return
	}

	// Raw mode
	var allSamples []float64
	for _, s := range spec.Series {
		allSamples = append(allSamples, s.Data...)
	}
	if len(allSamples) == 0 {
		empty := make([][]float64, len(spec.Series))
		emptyT := make([]int, len(spec.Series))
		for i := range spec.Series {
			empty[i] = []float64{0}
		}
		return []float64{0, 1}, empty, empty, emptyT
	}

	lo := allSamples[0]
	hi := allSamples[0]
	for _, v := range allSamples[1:] {
		if v < lo {
			lo = v
		}
		if v > hi {
			hi = v
		}
	}
	dataHi := hi
	nTotal := len(allSamples)

	var k int
	bn := spec.Binning
	if bn != nil && bn.Count != nil {
		k = *bn.Count
	} else if bn != nil && bn.Width != nil {
		if hi > lo {
			k = int(math.Max(1, math.Ceil((hi-lo) / *bn.Width)))
		} else {
			k = 1
		}
	} else {
		k = int(math.Max(1, math.Ceil(math.Sqrt(float64(nTotal)))))
	}

	var w float64
	if bn != nil && bn.Width != nil {
		w = *bn.Width
	} else {
		if k > 0 && hi > lo {
			w = (hi - lo) / float64(k)
		} else {
			w = 1.0
		}
	}

	if bn != nil && bn.Start != nil && bn.Width != nil {
		lo = *bn.Start
	}

	edges = make([]float64, k+1)
	for i := 0; i <= k; i++ {
		edges[i] = lo + w*float64(i)
	}

	for si := range spec.Series {
		s := &spec.Series[si]
		sc := make([]float64, k)
		for _, v := range s.Data {
			var b int
			if v == dataHi {
				b = k - 1
			} else {
				b = int(math.Floor((v - lo) / w))
				if b < 0 {
					b = 0
				}
				if b > k-1 {
					b = k - 1
				}
			}
			sc[b] += 1.0
		}
		counts = append(counts, sc)
		ns := len(s.Data)
		totals = append(totals, ns)
		if spec.Normalization == "density" {
			h := make([]float64, k)
			for b := 0; b < k; b++ {
				nw := float64(ns) * w
				if nw == 0 {
					h[b] = 0
				} else {
					h[b] = sc[b] / nw
				}
			}
			heights = append(heights, h)
		} else {
			h := make([]float64, k)
			copy(h, sc)
			heights = append(heights, h)
		}
	}

	return
}

func prepareHistSpec(spec *ChartSpec, edges []float64, heights [][]float64) *ChartSpec {
	mod := *spec
	mod.XAxis.Min = &edges[0]
	last := edges[len(edges)-1]
	mod.XAxis.Max = &last

	allH := 0.0
	for _, hs := range heights {
		for _, h := range hs {
			if h > allH {
				allH = h
			}
		}
	}
	if allH == 0 {
		allH = 1.0
	}

	if mod.YAxis.Min == nil {
		zero := 0.0
		mod.YAxis.Min = &zero
	}
	if mod.YAxis.Max == nil {
		mod.YAxis.Max = &allH
	}

	if spec.Overlay == "pareto" {
		zero := 0.0
		hundred := 100.0
		mod.SecondaryYAxis = &Axis{
			Title: "Cumulative %",
			Min:   &zero,
			Max:   &hundred,
		}
	}

	return &mod
}

func histogramMarks(f *cartesianFrame, p *strings.Builder, edges []float64, heights [][]float64, counts [][]float64, totals []int, spec *ChartSpec) {
	k := len(edges) - 1
	if k <= 0 {
		return
	}

	for si := range spec.Series {
		s := &spec.Series[si]
		st := f.styles[si]
		baseline := f.ypix(0.0)
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
		for b := 0; b < k; b++ {
			xLeft := f.xpix(edges[b])
			xRight := f.xpix(edges[b+1])
			barW := xRight - xLeft
			hVal := heights[si][b]
			yTop := f.ypix(hVal)
			barH := baseline - yTop
			cx := (xLeft + xRight) / 2
			label := fmtNum(edges[b]) + "–" + fmtNum(edges[b+1])
			common := fmt.Sprintf(
				`class="sc-bar sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="3.5" data-r-hover="6"`,
				si, esc(s.Name), esc(label), esc(fmtNum(hVal)), st.solid)
			p.WriteString(fmt.Sprintf(
				`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" fill="%s"/>`,
				common, f1(cx), f1(yTop), f1(xLeft), f1(yTop), f1(barW), f1(barH), st.fill))
		}
		p.WriteString(`</g>`)
	}

	if spec.Overlay == "pareto" {
		emitHistPareto(f, p, edges, counts, totals, spec)
	} else if spec.Overlay == "bellcurve" {
		emitHistBellcurve(f, p, edges, counts, totals, spec)
	}
}

func emitHistPareto(f *cartesianFrame, p *strings.Builder, edges []float64, counts [][]float64, totals []int, spec *ChartSpec) {
	si := len(spec.Series)
	k := len(edges) - 1
	palette := f.theme.Palette
	color := palette[si%len(palette)]
	total := totals[0]
	if total <= 0 {
		return
	}

	cum := 0.0
	type pt struct{ x, y float64 }
	pts := make([]pt, 0, k)
	cumPcts := make([]float64, k)
	for b := 0; b < k; b++ {
		cum += counts[0][b]
		pct := 100.0 * cum / float64(total)
		cumPcts[b] = pct
		cx := f.xpix((edges[b] + edges[b+1]) / 2)
		cy := f.ypix2(pct)
		pts = append(pts, pt{cx, cy})
	}
	if len(pts) == 0 {
		return
	}

	var d strings.Builder
	d.WriteString("M")
	for i, pt := range pts {
		if i > 0 {
			d.WriteString(" L")
		}
		d.WriteString(f1(pt.x) + " " + f1(pt.y))
	}

	p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
	p.WriteString(fmt.Sprintf(
		`<path class="sc-series-line" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`,
		si, d.String(), color))
	for b := 0; b < k; b++ {
		label := fmtNum(edges[b]) + "–" + fmtNum(edges[b+1])
		common := fmt.Sprintf(
			`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="3.5" data-r-hover="6"`,
			si, esc("Cumulative %"), esc(label), esc(fmtNum(cumPcts[b])), color)
		p.WriteString(fmt.Sprintf(
			`<circle %s cx="%s" cy="%s" r="3.5" fill="%s" stroke="%s" stroke-width="1"/>`,
			common, f1(pts[b].x), f1(pts[b].y), color, f.theme.MarkerHalo))
	}
	p.WriteString(`</g>`)
}

func emitHistBellcurve(f *cartesianFrame, p *strings.Builder, edges []float64, counts [][]float64, totals []int, spec *ChartSpec) {
	si := len(spec.Series)
	k := len(edges) - 1
	palette := f.theme.Palette
	color := palette[si%len(palette)]

	var allSamples []float64
	for _, s := range spec.Series {
		allSamples = append(allSamples, s.Data...)
	}
	if len(allSamples) == 0 {
		return
	}

	n := len(allSamples)
	sum := 0.0
	for _, v := range allSamples {
		sum += v
	}
	mean := sum / float64(n)

	varSum := 0.0
	for _, v := range allSamples {
		d := v - mean
		varSum += d * d
	}
	variance := varSum / float64(n)
	std := math.Sqrt(variance)
	if std == 0 {
		return
	}

	w := 1.0
	if k > 0 {
		w = (edges[len(edges)-1] - edges[0]) / float64(k)
	}
	xLo := edges[0]
	xHi := edges[len(edges)-1]
	nPts := 200

	type pt struct{ x, y float64 }
	pts := make([]pt, 0, nPts)
	for i := 0; i < nPts; i++ {
		x := xLo + (xHi-xLo)*float64(i)/float64(nPts-1)
		z := (x - mean) / std
		pdf := math.Exp(-z*z/2) / (std * math.Sqrt(2*math.Pi))
		var y float64
		if spec.Normalization == "density" {
			y = pdf
		} else {
			y = float64(n) * w * pdf
		}
		px := f.xpix(x)
		py := f.ypix(y)
		pts = append(pts, pt{px, py})
	}
	if len(pts) == 0 {
		return
	}

	var d strings.Builder
	d.WriteString("M")
	for i, pt := range pts {
		if i > 0 {
			d.WriteString(" L")
		}
		d.WriteString(f1(pt.x) + " " + f1(pt.y))
	}

	p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
	p.WriteString(fmt.Sprintf(
		`<path class="sc-series-line" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`,
		si, d.String(), color))
	p.WriteString(`</g>`)
}
