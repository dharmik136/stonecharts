package stonecharts

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

func histogramLabels(edges []float64) []string {
	labels := make([]string, 0, len(edges)-1)
	for i := 0; i < len(edges)-1; i++ {
		labels = append(labels, fmtNum(edges[i])+"–"+fmtNum(edges[i+1]))
	}
	return labels
}

func histogramEdges(spec *ChartSpec, values []float64) []float64 {
	if len(values) == 0 {
		return []float64{0, 1}
	}
	lo, hi := values[0], values[0]
	for _, v := range values[1:] {
		if v < lo {
			lo = v
		}
		if v > hi {
			hi = v
		}
	}
	if spec.PreBinned && spec.XAxis.BinEdges != nil && len(spec.XAxis.BinEdges) >= 2 {
		edges := make([]float64, len(spec.XAxis.BinEdges))
		copy(edges, spec.XAxis.BinEdges)
		return edges
	}
	if spec.Binning != nil && spec.Binning.Width != nil {
		width := *spec.Binning.Width
		if width <= 0 {
			width = 1
		}
		start := lo
		if spec.Binning.Start != nil {
			start = *spec.Binning.Start
		}
		count := int(math.Ceil((hi - start) / width))
		if count < 1 {
			count = 1
		}
		edges := make([]float64, count+1)
		for i := 0; i <= count; i++ {
			edges[i] = start + width*float64(i)
		}
		return edges
	}
	count := 0
	if spec.Binning != nil && spec.Binning.Count != nil && *spec.Binning.Count > 0 {
		count = *spec.Binning.Count
	} else {
		count = int(math.Ceil(math.Sqrt(float64(len(values)))))
		if count < 1 {
			count = 1
		}
	}
	width := (hi - lo) / float64(count)
	if width == 0 {
		width = 1
	}
	edges := make([]float64, count+1)
	for i := 0; i <= count; i++ {
		edges[i] = lo + width*float64(i)
	}
	return edges
}

func histogramCounts(values []float64, edges []float64) []float64 {
	bins := make([]float64, len(edges)-1)
	if len(edges) < 2 {
		return bins
	}
	lo := edges[0]
	hi := edges[len(edges)-1]
	width := edges[1] - edges[0]
	if width == 0 {
		width = 1
	}
	for _, v := range values {
		if v == hi {
			bins[len(bins)-1]++
			continue
		}
		idx := int(math.Floor((v - lo) / width))
		if idx < 0 {
			idx = 0
		}
		if idx >= len(bins) {
			idx = len(bins) - 1
		}
		bins[idx]++
	}
	return bins
}

func histogramDensity(counts []float64, total float64, edges []float64) []float64 {
	vals := make([]float64, len(counts))
	for i, c := range counts {
		w := edges[i+1] - edges[i]
		if total == 0 || w == 0 {
			vals[i] = 0
		} else {
			vals[i] = c / (total * w)
		}
	}
	return vals
}

func histogramBell(values []float64, edges []float64, density bool) []float64 {
	if len(values) == 0 {
		return make([]float64, len(edges)-1)
	}
	n := float64(len(values))
	mean := 0.0
	for _, v := range values {
		mean += v
	}
	mean /= n
	variance := 0.0
	for _, v := range values {
		d := v - mean
		variance += d * d
	}
	variance /= n
	if variance <= 0 {
		return make([]float64, len(edges)-1)
	}
	sigma := math.Sqrt(variance)
	if sigma == 0 {
		return make([]float64, len(edges)-1)
	}
	scale := 1.0
	if !density {
		span := edges[len(edges)-1] - edges[0]
		step := span / float64(max(1, len(edges)-1))
		scale = n * step
	}
	out := make([]float64, len(edges)-1)
	for i := 0; i < len(edges)-1; i++ {
		x := (edges[i] + edges[i+1]) / 2
		z := (x - mean) / sigma
		pdf := math.Exp(-0.5*z*z) / (sigma * math.Sqrt(2*math.Pi))
		out[i] = pdf * scale
	}
	return out
}

func histogramSeries(spec *ChartSpec) (*ChartSpec, []float64) {
	values := []float64{}
	for _, s := range spec.Series {
		values = append(values, s.Data...)
	}
	edges := histogramEdges(spec, values)
	labels := histogramLabels(edges)
	series := make([]Series, 0, len(spec.Series)+1)
	allCounts := make([]float64, len(edges)-1)
	for _, s := range spec.Series {
		counts := histogramCounts(s.Data, edges)
		if spec.PreBinned {
			counts = make([]float64, len(edges)-1)
			copy(counts, s.Data)
		}
		if spec.Normalization == "density" {
			counts = histogramDensity(counts, float64(len(s.Data)), edges)
		}
		for i, v := range counts {
			if i < len(allCounts) {
				allCounts[i] += v
			}
		}
		series = append(series, Series{Name: s.Name, Data: counts, Type: "column", YAxis: 0, Color: s.Color, FillOpacity: s.FillOpacity, Pattern: s.Pattern, LineWidth: s.LineWidth, DashStyle: s.DashStyle, Step: s.Step, Curve: s.Curve, Marker: s.Marker})
	}
	secondary := spec.SecondaryYAxis
	if spec.Overlay == "pareto" {
		pct := make([]float64, len(allCounts))
		cum := 0.0
		total := 0.0
		for _, v := range allCounts {
			total += v
		}
		if total == 0 {
			total = 1
		}
		for i, v := range allCounts {
			cum += v
			pct[i] = cum / total * 100
		}
		series = append(series, Series{Name: "Pareto", Data: pct, Type: "line", YAxis: 1, Marker: &Marker{Enabled: boolPtr(false)}})
		if secondary == nil {
			opp := true
			secondary = &Axis{Title: "Percent", Min: float64Ptr(0), Max: float64Ptr(100), Opposite: &opp}
		}
	} else if spec.Overlay == "bellcurve" {
		series = append(series, Series{Name: "Bell curve", Data: histogramBell(values, edges, spec.Normalization == "density"), Type: "line", Marker: &Marker{Enabled: boolPtr(false)}})
	}
	copySpec := *spec
	copySpec.Series = series
	copySpec.SecondaryYAxis = secondary
	copySpec.XAxis = spec.XAxis
	copySpec.XAxis.Categories = labels
	return &copySpec, allCounts
}

func float64Ptr(v float64) *float64 { return &v }

func boolPtr(v bool) *bool { return &v }

func renderHistogramSVG(spec *ChartSpec) string {
	derived, _ := histogramSeries(spec)
	return renderCartesian(derived, "Histogram", "band", histogramMarks, true)
}

func histogramMarks(f *cartesianFrame, p *strings.Builder) {
	for si, s := range f.spec.Series {
		st := f.styles[si]
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
		if s.Type == "line" {
			pts := make([][2]float64, len(s.Data))
			for i, v := range s.Data {
				if s.YAxis == 1 && f.secondaryAxis != nil {
					pts[i] = [2]float64{f.xpix(i), f.ypix2(v)}
				} else {
					pts[i] = [2]float64{f.xpix(i), f.ypix(v)}
				}
			}
			d := pathD(pts, s.Step)
			if s.Curve == "monotone" {
				d = splineD(pts)
			}
			p.WriteString(fmt.Sprintf(`<path class="sc-series-line" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"/>`, si, d, st.stroke, fmtNum(s.lineWidth())))
			if s.markerEnabled() {
				radius := s.markerRadius()
				radiusHover := radius + 2.5
				for i, pt := range pts {
					xlabel := strconv.Itoa(i)
					if i < len(f.cats) {
						xlabel = f.cats[i]
					}
					common := fmt.Sprintf(`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`, si, esc(s.Name), esc(xlabel), esc(fmtNum(s.Data[i])), st.solid, fmtNum(radius), fmtNum(radiusHover))
					p.WriteString(markerSVG(s.markerSymbol(), pt[0], pt[1], radius, common, st.solid, f.theme.MarkerHalo))
				}
			}
		} else {
			barW := f.bandWidth()
			for i, v := range s.Data {
				cx := f.xpix(i)
				x := cx - barW/2
				top := f.ypix(v)
				base := f.ypix(0)
				y := math.Min(base, top)
				h := math.Abs(base - top)
				xlabel := strconv.Itoa(i)
				if i < len(f.cats) {
					xlabel = f.cats[i]
				}
				common := fmt.Sprintf(`class="sc-bar sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="3.5" data-r-hover="6"`, si, esc(s.Name), esc(xlabel), esc(fmtNum(v)), st.solid)
				p.WriteString(fmt.Sprintf(`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" fill="%s"/>`, common, f1(cx), f1(top), f1(x), f1(y), f1(barW), f1(h), st.fill))
			}
		}
		p.WriteString(`</g>`)
	}
}
