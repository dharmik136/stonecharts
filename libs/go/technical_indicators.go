package stonecharts

import (
	"fmt"
	"math"
	"strings"
)

// ---------- transforms (pure math, parity-critical) ----------

func tiSMA(data []float64, period int) []*float64 {
	n := len(data)
	out := make([]*float64, n)
	for i := period - 1; i < n; i++ {
		s := 0.0
		for j := i - period + 1; j <= i; j++ {
			s += data[j]
		}
		v := s / float64(period)
		out[i] = &v
	}
	return out
}

func tiEMA(data []float64, period int) []*float64 {
	n := len(data)
	out := make([]*float64, n)
	if n < period {
		return out
	}
	s := 0.0
	for j := 0; j < period; j++ {
		s += data[j]
	}
	seed := s / float64(period)
	out[period-1] = &seed
	alpha := 2.0 / float64(period+1)
	prev := seed
	for i := period; i < n; i++ {
		val := alpha*data[i] + (1-alpha)*prev
		v := val
		out[i] = &v
		prev = val
	}
	return out
}

func tiBollinger(data []float64, period int, k float64) ([]*float64, []*float64, []*float64) {
	n := len(data)
	mid := tiSMA(data, period)
	upper := make([]*float64, n)
	lower := make([]*float64, n)
	for i := period - 1; i < n; i++ {
		m := *mid[i]
		variance := 0.0
		for j := i - period + 1; j <= i; j++ {
			d := data[j] - m
			variance += d * d
		}
		variance = variance / float64(period)
		if variance < 0 {
			variance = 0.0
		}
		sigma := math.Sqrt(variance)
		u := m + k*sigma
		l := m - k*sigma
		upper[i] = &u
		lower[i] = &l
	}
	return mid, upper, lower
}

func tiVWAP(data []float64, volume []float64) []*float64 {
	n := len(data)
	if len(volume) < n {
		n = len(volume)
	}
	out := make([]*float64, len(data))
	cumPV := 0.0
	cumVol := 0.0
	for i := 0; i < n; i++ {
		cumPV += data[i] * volume[i]
		cumVol += volume[i]
		if cumVol == 0.0 {
			out[i] = nil
		} else {
			v := cumPV / cumVol
			out[i] = &v
		}
	}
	return out
}

func tiRSI(data []float64, period int) []*float64 {
	n := len(data)
	out := make([]*float64, n)
	if n < period+1 {
		return out
	}
	gains := make([]float64, n)
	losses := make([]float64, n)
	for i := 1; i < n; i++ {
		d := data[i] - data[i-1]
		if d > 0 {
			gains[i] = d
		}
		if d < 0 {
			losses[i] = -d
		}
	}
	sumGain := 0.0
	sumLoss := 0.0
	for j := 1; j <= period; j++ {
		sumGain += gains[j]
		sumLoss += losses[j]
	}
	avgGain := sumGain / float64(period)
	avgLoss := sumLoss / float64(period)
	if avgLoss == 0.0 {
		v := 100.0
		out[period] = &v
	} else {
		rs := avgGain / avgLoss
		v := 100.0 - 100.0/(1.0+rs)
		out[period] = &v
	}
	for i := period + 1; i < n; i++ {
		avgGain = (avgGain*float64(period-1) + gains[i]) / float64(period)
		avgLoss = (avgLoss*float64(period-1) + losses[i]) / float64(period)
		if avgLoss == 0.0 {
			v := 100.0
			out[i] = &v
		} else {
			rs := avgGain / avgLoss
			v := 100.0 - 100.0/(1.0+rs)
			out[i] = &v
		}
	}
	return out
}

func tiMACD(data []float64, fast, slow, signalPeriod int) ([]*float64, []*float64, []*float64) {
	emaFast := tiEMA(data, fast)
	emaSlow := tiEMA(data, slow)
	n := len(data)
	macdLine := make([]*float64, n)
	for i := 0; i < n; i++ {
		if emaFast[i] != nil && emaSlow[i] != nil {
			v := *emaFast[i] - *emaSlow[i]
			macdLine[i] = &v
		}
	}
	var defined []float64
	for _, v := range macdLine {
		if v != nil {
			defined = append(defined, *v)
		}
	}
	var sigVals []*float64
	if len(defined) > 0 {
		sigVals = tiEMA(defined, signalPeriod)
	} else {
		sigVals = make([]*float64, n)
	}
	signalLine := make([]*float64, n)
	di := 0
	for i := 0; i < n; i++ {
		if macdLine[i] != nil {
			if di < len(sigVals) {
				signalLine[i] = sigVals[di]
			}
			di++
		}
	}
	hist := make([]*float64, n)
	for i := 0; i < n; i++ {
		if macdLine[i] != nil && signalLine[i] != nil {
			v := *macdLine[i] - *signalLine[i]
			hist[i] = &v
		}
	}
	return macdLine, signalLine, hist
}

// ---------- renderer ----------

const paneGap = 24.0

func renderTechnicalIndicatorsSVG(spec *ChartSpec) string {
	hasOsc := false
	for _, s := range spec.Series {
		for _, ind := range s.Indicators {
			if ind.Type == "macd" || ind.Type == "rsi" {
				hasOsc = true
			}
		}
	}
	_ = hasOsc

	var allOverlayVals []float64
	for _, s := range spec.Series {
		if len(s.Data) > 0 {
			allOverlayVals = append(allOverlayVals, s.Data...)
		}
		for _, ind := range s.Indicators {
			vals := tiComputeIndicatorValues(&s, &ind)
			for _, v := range vals {
				if v != nil {
					allOverlayVals = append(allOverlayVals, *v)
				}
			}
		}
	}

	if len(allOverlayVals) > 0 {
		lo := allOverlayVals[0]
		hi := allOverlayVals[0]
		for _, v := range allOverlayVals[1:] {
			if v < lo {
				lo = v
			}
			if v > hi {
				hi = v
			}
		}
		if spec.YAxis.Min == nil {
			spec.YAxis.Min = &lo
		}
		if spec.YAxis.Max == nil {
			spec.YAxis.Max = &hi
		}
	}

	return renderCartesian(spec, "Technical indicators", "point", tiMarks, false)
}

func tiComputeIndicatorValues(s *Series, ind *Indicator) []*float64 {
	data := s.Data
	period := 20
	if ind.Period != nil {
		period = *ind.Period
	}
	switch ind.Type {
	case "sma":
		return tiSMA(data, period)
	case "ema":
		return tiEMA(data, period)
	case "bollinger":
		k := 2.0
		if ind.Params != nil {
			if sd, ok := ind.Params["stdDev"]; ok {
				switch v := sd.(type) {
				case float64:
					k = v
				}
			}
		}
		mid, upper, lower := tiBollinger(data, period, k)
		var out []*float64
		out = append(out, mid...)
		out = append(out, upper...)
		out = append(out, lower...)
		return out
	case "vwap":
		vol := s.Volume
		if vol == nil {
			vol = []float64{}
		}
		return tiVWAP(data, vol)
	case "rsi":
		p := 14
		if ind.Period != nil {
			p = *ind.Period
		}
		return tiRSI(data, p)
	case "macd":
		fast := 12
		slow := 26
		sig := 9
		if ind.Params != nil {
			if v, ok := ind.Params["fast"]; ok {
				if f, ok2 := v.(float64); ok2 {
					fast = int(f)
				}
			}
			if v, ok := ind.Params["slow"]; ok {
				if f, ok2 := v.(float64); ok2 {
					slow = int(f)
				}
			}
			if v, ok := ind.Params["signal"]; ok {
				if f, ok2 := v.(float64); ok2 {
					sig = int(f)
				}
			}
		}
		ml, sl, h := tiMACD(data, fast, slow, sig)
		var out []*float64
		out = append(out, ml...)
		out = append(out, sl...)
		out = append(out, h...)
		return out
	}
	return nil
}

func tiMarks(f *cartesianFrame, p *strings.Builder) {
	spec := f.spec
	theme := f.theme

	hasOsc := false
	oscFrac := 0.30
	for _, s := range spec.Series {
		for _, ind := range s.Indicators {
			if ind.Type == "macd" || ind.Type == "rsi" {
				hasOsc = true
			}
		}
	}
	if len(spec.Panes) > 1 {
		if spec.Panes[1].Height != nil {
			oscFrac = *spec.Panes[1].Height
		}
		if spec.Panes[0].Height != nil {
			oscFrac = 1.0 - *spec.Panes[0].Height
		}
	}

	baseTop := f.plotY
	var baseH, oscTop, oscH float64
	if hasOsc {
		baseH = (f.plotH - paneGap) * (1 - oscFrac)
		oscTop = f.plotY + baseH + paneGap
		oscH = (f.plotH - paneGap) * oscFrac
	} else {
		baseH = f.plotH
		oscTop = 0.0
		oscH = 0.0
	}

	baseYpix := func(v float64) float64 {
		if f.yMax == f.yMin {
			return baseTop + baseH/2
		}
		return baseTop + baseH - (v-f.yMin)/(f.yMax-f.yMin)*baseH
	}

	var baseYpixFn func(float64) float64
	if !hasOsc {
		baseYpixFn = f.ypix
	} else {
		baseYpixFn = baseYpix
	}

	tiEmitPlotBandsLines(f, p, baseYpixFn, baseTop, baseH)

	siGlobal := 0

	for si, s := range spec.Series {
		st := f.styles[si]
		pts := make([][2]float64, len(s.Data))
		for i, v := range s.Data {
			pts[i] = [2]float64{f.xpix(float64(i)), baseYpixFn(v)}
		}
		var d string
		if s.Curve == "monotone" {
			d = splineD(pts)
		} else {
			d = pathD(pts, s.Step)
		}
		lw := s.LineWidth
		if lw == 0 {
			lw = 2
		}
		lineDashAttr := ""
		if da := dashArray(s.DashStyle); da != "" {
			lineDashAttr = ` stroke-dasharray="` + da + `"`
		}

		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, siGlobal))

		if st.areaFill != "" && len(pts) > 0 {
			baseFloor := baseYpixFn(f.yMin)
			areaD := d + " L" + f1(pts[len(pts)-1][0]) + " " + f1(baseFloor) +
				" L" + f1(pts[0][0]) + " " + f1(baseFloor) + " Z"
			p.WriteString(fmt.Sprintf(
				`<path class="sc-series-area" data-series="%d" d="%s" fill="%s"%s stroke="none"/>`,
				siGlobal, areaD, st.areaFill, st.areaOp))
		}

		if s.Type != "area" || st.areaFill != "" {
			p.WriteString(fmt.Sprintf(
				`<path class="sc-series-line" data-series="%d" d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"%s/>`,
				siGlobal, d, st.stroke, fmtNum(lw), lineDashAttr))
		}

		mk := s.Marker
		if mk == nil {
			mk = &Marker{}
		}
		mkEnabled := mk.Enabled == nil || *mk.Enabled
		if mkEnabled {
			radius := mk.Radius
			if radius == 0 {
				radius = 3.5
			}
			radiusHover := radius + 2.5
			symbol := mk.Symbol
			if symbol == "" {
				symbol = "circle"
			}
			for i, pt := range pts {
				xlabel := fmt.Sprintf("%d", i)
				if i < len(f.cats) {
					xlabel = f.cats[i]
				}
				common := fmt.Sprintf(
					`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
					siGlobal, esc(s.Name), esc(xlabel), esc(fmtNum(s.Data[i])), st.solid, fmtNum(radius), fmtNum(radiusHover))
				p.WriteString(markerSVG(symbol, pt[0], pt[1], radius, common, st.solid, theme.MarkerHalo, 1.0))
			}
		}

		p.WriteString(`</g>`)
		siGlobal++

		for _, ind := range s.Indicators {
			if ind.Type == "macd" || ind.Type == "rsi" {
				continue
			}
			tiEmitOverlay(f, p, &s, &ind, siGlobal, baseYpixFn, theme)
			siGlobal++
		}
	}

	var oscIndicators []oscEntry
	for si := range spec.Series {
		for ii := range spec.Series[si].Indicators {
			ind := &spec.Series[si].Indicators[ii]
			if ind.Type == "macd" || ind.Type == "rsi" {
				oscIndicators = append(oscIndicators, oscEntry{si, &spec.Series[si], ind})
			}
		}
	}

	if hasOsc && len(oscIndicators) > 0 {
		tiEmitOscPane(f, p, oscIndicators, siGlobal, oscTop, oscH, theme)
		siGlobal += len(oscIndicators)
	}

	if len(spec.Flags) > 0 {
		tiEmitFlags(f, p, spec.Flags, siGlobal, baseYpixFn, baseTop, theme)
	}
}

func tiEmitPlotBandsLines(f *cartesianFrame, p *strings.Builder, ypixFn func(float64) float64, baseTop, baseH float64) {
	spec := f.spec

	for _, pb := range spec.XAxis.PlotBands {
		x1 := f.xpix(float64(int(pb.From)))
		x2 := f.xpix(float64(int(pb.To)))
		xl := math.Min(x1, x2)
		w := math.Abs(x2 - x1)
		opacityAttr := ""
		if pb.Opacity != nil {
			opacityAttr = fmt.Sprintf(` opacity="%s"`, fmtNum(*pb.Opacity))
		}
		p.WriteString(fmt.Sprintf(
			`<rect class="sc-plotband" x="%s" y="%s" width="%s" height="%s" fill="%s"%s/>`,
			f1(xl), f1(baseTop), f1(w), f1(baseH), esc(pb.Color), opacityAttr))
		if pb.Label != "" {
			p.WriteString(fmt.Sprintf(
				`<text class="sc-plotband-label" x="%s" y="%s" text-anchor="middle" font-size="10" fill="%s">%s</text>`,
				f1(xl+w/2), f1(baseTop+14), f.theme.AxisLabelColor, esc(pb.Label)))
		}
	}

	for _, pl := range spec.XAxis.PlotLines {
		gx := f.xpix(float64(int(pl.Value)))
		sw := 1.0
		if pl.Width != nil {
			sw = *pl.Width
		}
		ds := dashArray(pl.DashStyle)
		dsAttr := ""
		if ds != "" {
			dsAttr = ` stroke-dasharray="` + ds + `"`
		}
		p.WriteString(fmt.Sprintf(
			`<line class="sc-plotline" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s/>`,
			f1(gx), f1(baseTop), f1(gx), f1(baseTop+baseH), esc(pl.Color), fmtNum(sw), dsAttr))
		if pl.Label != "" {
			p.WriteString(fmt.Sprintf(
				`<text class="sc-plotline-label" x="%s" y="%s" font-size="10" fill="%s">%s</text>`,
				f1(gx+4), f1(baseTop+14), f.theme.AxisLabelColor, esc(pl.Label)))
		}
	}

	for _, pb := range spec.YAxis.PlotBands {
		y1 := ypixFn(pb.From)
		y2 := ypixFn(pb.To)
		yt := math.Min(y1, y2)
		h := math.Abs(y2 - y1)
		opacityAttr := ""
		if pb.Opacity != nil {
			opacityAttr = fmt.Sprintf(` opacity="%s"`, fmtNum(*pb.Opacity))
		}
		p.WriteString(fmt.Sprintf(
			`<rect class="sc-plotband" x="%s" y="%s" width="%s" height="%s" fill="%s"%s/>`,
			f1(f.plotX), f1(yt), f1(f.plotW), f1(h), esc(pb.Color), opacityAttr))
		if pb.Label != "" {
			p.WriteString(fmt.Sprintf(
				`<text class="sc-plotband-label" x="%s" y="%s" text-anchor="end" font-size="10" fill="%s">%s</text>`,
				f1(f.plotX+f.plotW-4), f1(yt+14), f.theme.AxisLabelColor, esc(pb.Label)))
		}
	}

	for _, pl := range spec.YAxis.PlotLines {
		gy := ypixFn(pl.Value)
		sw := 1.0
		if pl.Width != nil {
			sw = *pl.Width
		}
		ds := dashArray(pl.DashStyle)
		dsAttr := ""
		if ds != "" {
			dsAttr = ` stroke-dasharray="` + ds + `"`
		}
		p.WriteString(fmt.Sprintf(
			`<line class="sc-plotline" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s/>`,
			f1(f.plotX), f1(gy), f1(f.plotX+f.plotW), f1(gy), esc(pl.Color), fmtNum(sw), dsAttr))
		if pl.Label != "" {
			p.WriteString(fmt.Sprintf(
				`<text class="sc-plotline-label" x="%s" y="%s" text-anchor="end" font-size="10" fill="%s">%s</text>`,
				f1(f.plotX+f.plotW-4), f1(gy-4), f.theme.AxisLabelColor, esc(pl.Label)))
		}
	}
}

func tiEmitOverlay(f *cartesianFrame, p *strings.Builder, s *Series, ind *Indicator, si int, ypixFn func(float64) float64, theme *Theme) {
	data := s.Data
	period := 20
	if ind.Period != nil {
		period = *ind.Period
	}
	palette := f.theme.Palette
	color := ind.Color
	if color == "" {
		color = palette[si%len(palette)]
	}
	lw := 1.5
	ds := dashArray(ind.DashStyle)
	dsAttr := ""
	if ds != "" {
		dsAttr = ` stroke-dasharray="` + ds + `"`
	}
	indName := s.Name + " " + strings.ToUpper(ind.Type) + "(" + fmt.Sprintf("%d", period) + ")"

	switch ind.Type {
	case "sma":
		vals := tiSMA(data, period)
		var pts [][2]float64
		for i, v := range vals {
			if v != nil {
				pts = append(pts, [2]float64{f.xpix(float64(i)), ypixFn(*v)})
			}
		}
		if len(pts) > 0 {
			d := pathD(pts, "")
			p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
			p.WriteString(fmt.Sprintf(
				`<path class="sc-series-line sc-indicator" data-series="%d" data-indicator="sma" d="%s" fill="none" stroke="%s" stroke-width="%s"%s/>`,
				si, d, esc(color), fmtNum(lw), dsAttr))
			radius := 3.5
			radiusHover := 6.0
			for i, v := range vals {
				if v != nil {
					x := f.xpix(float64(i))
					y := ypixFn(*v)
					xlabel := fmt.Sprintf("%d", i)
					if i < len(f.cats) {
						xlabel = f.cats[i]
					}
					common := fmt.Sprintf(
						`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
						si, esc(indName), esc(xlabel), esc(fmtNum(*v)), esc(color), fmtNum(radius), fmtNum(radiusHover))
					p.WriteString(fmt.Sprintf(
						`<circle %s cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="1"/>`,
						common, f1(x), f1(y), fmtNum(radius), esc(color), theme.MarkerHalo))
				}
			}
			p.WriteString(`</g>`)
		}

	case "ema":
		vals := tiEMA(data, period)
		var pts [][2]float64
		for i, v := range vals {
			if v != nil {
				pts = append(pts, [2]float64{f.xpix(float64(i)), ypixFn(*v)})
			}
		}
		if len(pts) > 0 {
			d := pathD(pts, "")
			p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
			p.WriteString(fmt.Sprintf(
				`<path class="sc-series-line sc-indicator" data-series="%d" data-indicator="ema" d="%s" fill="none" stroke="%s" stroke-width="%s"%s/>`,
				si, d, esc(color), fmtNum(lw), dsAttr))
			radius := 3.5
			radiusHover := 6.0
			for i, v := range vals {
				if v != nil {
					x := f.xpix(float64(i))
					y := ypixFn(*v)
					xlabel := fmt.Sprintf("%d", i)
					if i < len(f.cats) {
						xlabel = f.cats[i]
					}
					common := fmt.Sprintf(
						`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
						si, esc(indName), esc(xlabel), esc(fmtNum(*v)), esc(color), fmtNum(radius), fmtNum(radiusHover))
					p.WriteString(fmt.Sprintf(
						`<circle %s cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="1"/>`,
						common, f1(x), f1(y), fmtNum(radius), esc(color), theme.MarkerHalo))
				}
			}
			p.WriteString(`</g>`)
		}

	case "bollinger":
		k := 2.0
		if ind.Params != nil {
			if sd, ok := ind.Params["stdDev"]; ok {
				if v, ok2 := sd.(float64); ok2 {
					k = v
				}
			}
		}
		midVals, upperVals, lowerVals := tiBollinger(data, period, k)
		type definedPoint struct {
			i    int
			u, l float64
		}
		var defined []definedPoint
		for i := 0; i < len(data); i++ {
			if upperVals[i] != nil && lowerVals[i] != nil {
				defined = append(defined, definedPoint{i, *upperVals[i], *lowerVals[i]})
			}
		}
		if len(defined) > 0 {
			upperPts := make([][2]float64, len(defined))
			for j, dp := range defined {
				upperPts[j] = [2]float64{f.xpix(float64(dp.i)), ypixFn(dp.u)}
			}
			upperD := pathD(upperPts, "")
			var lowerParts []string
			for j := len(defined) - 1; j >= 0; j-- {
				dp := defined[j]
				lx := f.xpix(float64(dp.i))
				ly := ypixFn(dp.l)
				lowerParts = append(lowerParts, "L"+f1(lx)+" "+f1(ly))
			}
			lowerD := strings.Join(lowerParts, " ")
			bandD := upperD + " " + lowerD + " Z"
			fillOpacity := 0.15
			p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
			p.WriteString(fmt.Sprintf(
				`<path class="sc-series-range sc-band sc-indicator" data-series="%d" data-indicator="bollinger" d="%s" fill="%s" fill-opacity="%s" stroke="none"/>`,
				si, bandD, esc(color), fmtNum(fillOpacity)))
			radius := 3.5
			radiusHover := 6.0
			bandName := s.Name + " Bollinger(" + fmt.Sprintf("%d", period) + "," + fmtNum(k) + ")"
			for _, dp := range defined {
				x := f.xpix(float64(dp.i))
				cy := ypixFn((dp.u + dp.l) / 2)
				xlabel := fmt.Sprintf("%d", dp.i)
				if dp.i < len(f.cats) {
					xlabel = f.cats[dp.i]
				}
				midVal := 0.0
				if midVals[dp.i] != nil {
					midVal = *midVals[dp.i]
				}
				common := fmt.Sprintf(
					`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-low="%s" data-high="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
					si, esc(bandName), esc(xlabel), esc(fmtNum(midVal)), esc(fmtNum(dp.l)), esc(fmtNum(dp.u)), esc(color), fmtNum(radius), fmtNum(radiusHover))
				p.WriteString(fmt.Sprintf(
					`<circle %s cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="1"/>`,
					common, f1(x), f1(cy), fmtNum(radius), esc(color), theme.MarkerHalo))
			}
			p.WriteString(`</g>`)
		}

	case "vwap":
		vol := s.Volume
		if vol == nil {
			vol = []float64{}
		}
		vals := tiVWAP(data, vol)
		indName = s.Name + " VWAP"
		var pts [][2]float64
		for i, v := range vals {
			if v != nil {
				pts = append(pts, [2]float64{f.xpix(float64(i)), ypixFn(*v)})
			}
		}
		if len(pts) > 0 {
			d := pathD(pts, "")
			p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
			p.WriteString(fmt.Sprintf(
				`<path class="sc-series-line sc-indicator" data-series="%d" data-indicator="vwap" d="%s" fill="none" stroke="%s" stroke-width="%s"%s/>`,
				si, d, esc(color), fmtNum(lw), dsAttr))
			radius := 3.5
			radiusHover := 6.0
			for i, v := range vals {
				if v != nil {
					x := f.xpix(float64(i))
					y := ypixFn(*v)
					xlabel := fmt.Sprintf("%d", i)
					if i < len(f.cats) {
						xlabel = f.cats[i]
					}
					common := fmt.Sprintf(
						`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
						si, esc(indName), esc(xlabel), esc(fmtNum(*v)), esc(color), fmtNum(radius), fmtNum(radiusHover))
					p.WriteString(fmt.Sprintf(
						`<circle %s cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="1"/>`,
						common, f1(x), f1(y), fmtNum(radius), esc(color), theme.MarkerHalo))
				}
			}
			p.WriteString(`</g>`)
		}
	}
}

type oscEntry struct {
	si  int
	s   *Series
	ind *Indicator
}

func tiEmitOscPane(f *cartesianFrame, p *strings.Builder, oscList []oscEntry, siStart int, oscTop, oscH float64, theme *Theme) {
	si := siStart
	for _, entry := range oscList {
		s := entry.s
		ind := entry.ind
		data := s.Data
		period := 14
		if ind.Period != nil {
			period = *ind.Period
		}
		palette := f.theme.Palette
		color := ind.Color
		if color == "" {
			color = palette[si%len(palette)]
		}
		ds := dashArray(ind.DashStyle)
		dsAttr := ""
		if ds != "" {
			dsAttr = ` stroke-dasharray="` + ds + `"`
		}

		if ind.Type == "rsi" {
			oscMin := 0.0
			oscMax := 100.0
			if len(f.spec.Panes) > 1 {
				pane := f.spec.Panes[1]
				if pane.Min != nil {
					oscMin = *pane.Min
				}
				if pane.Max != nil {
					oscMax = *pane.Max
				}
			}

			oscYpix := func(v float64) float64 {
				if oscMax == oscMin {
					return oscTop + oscH/2
				}
				return oscTop + oscH - (v-oscMin)/(oscMax-oscMin)*oscH
			}

			if len(f.spec.Panes) > 1 {
				pane := f.spec.Panes[1]
				for _, pb := range pane.PlotBands {
					y1 := oscYpix(pb.From)
					y2 := oscYpix(pb.To)
					yt := math.Min(y1, y2)
					h := math.Abs(y2 - y1)
					opacityAttr := ""
					if pb.Opacity != nil {
						opacityAttr = fmt.Sprintf(` opacity="%s"`, fmtNum(*pb.Opacity))
					}
					p.WriteString(fmt.Sprintf(
						`<rect class="sc-plotband" x="%s" y="%s" width="%s" height="%s" fill="%s"%s/>`,
						f1(f.plotX), f1(yt), f1(f.plotW), f1(h), esc(pb.Color), opacityAttr))
					if pb.Label != "" {
						p.WriteString(fmt.Sprintf(
							`<text class="sc-plotband-label" x="%s" y="%s" text-anchor="end" font-size="10" fill="%s">%s</text>`,
							f1(f.plotX+f.plotW-4), f1(yt+14), f.theme.AxisLabelColor, esc(pb.Label)))
					}
				}
				for _, pl := range pane.PlotLines {
					gy := oscYpix(pl.Value)
					sw := 1.0
					if pl.Width != nil {
						sw = *pl.Width
					}
					pds := dashArray(pl.DashStyle)
					pdsAttr := ""
					if pds != "" {
						pdsAttr = ` stroke-dasharray="` + pds + `"`
					}
					p.WriteString(fmt.Sprintf(
						`<line class="sc-plotline" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s/>`,
						f1(f.plotX), f1(gy), f1(f.plotX+f.plotW), f1(gy), esc(pl.Color), fmtNum(sw), pdsAttr))
				}
			}

			vals := tiRSI(data, period)
			indName := s.Name + " RSI(" + fmt.Sprintf("%d", period) + ")"
			var pts [][2]float64
			for i, v := range vals {
				if v != nil {
					pts = append(pts, [2]float64{f.xpix(float64(i)), oscYpix(*v)})
				}
			}
			if len(pts) > 0 {
				d := pathD(pts, "")
				p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
				p.WriteString(fmt.Sprintf(
					`<path class="sc-series-line sc-indicator" data-series="%d" data-indicator="rsi" d="%s" fill="none" stroke="%s" stroke-width="%s"%s/>`,
					si, d, esc(color), fmtNum(1.5), dsAttr))
				radius := 3.5
				radiusHover := 6.0
				for i, v := range vals {
					if v != nil {
						x := f.xpix(float64(i))
						y := oscYpix(*v)
						xlabel := fmt.Sprintf("%d", i)
						if i < len(f.cats) {
							xlabel = f.cats[i]
						}
						common := fmt.Sprintf(
							`class="sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
							si, esc(indName), esc(xlabel), esc(fmtNum(*v)), esc(color), fmtNum(radius), fmtNum(radiusHover))
						p.WriteString(fmt.Sprintf(
							`<circle %s cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="1"/>`,
							common, f1(x), f1(y), fmtNum(radius), esc(color), theme.MarkerHalo))
					}
				}
				p.WriteString(`</g>`)
			}
		}
		si++
	}
}

func tiEmitFlags(f *cartesianFrame, p *strings.Builder, flags []Flag, si int, ypixFn func(float64) float64, baseTop float64, theme *Theme) {
	palette := f.theme.Palette
	p.WriteString(fmt.Sprintf(`<g class="sc-series sc-flags" data-series="%d">`, si))
	for _, fl := range flags {
		x := f.xpix(float64(int(fl.X)))
		color := fl.Color
		if color == "" {
			color = palette[si%len(palette)]
		}
		flagY := baseTop
		title := fl.Title
		flagH := 14.0
		flagW := float64(len(title)) * 7.0
		if flagW < 20.0 {
			flagW = 20.0
		}

		xlabel := fmt.Sprintf("%d", int(fl.X))
		if int(fl.X) < len(f.cats) {
			xlabel = f.cats[int(fl.X)]
		}
		common := fmt.Sprintf(
			`class="sc-flag sc-point" data-series="%d" data-series-name="Events" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s" cx="%s" cy="%s"`,
			si, esc(xlabel), esc(title), esc(color), fmtNum(3.5), fmtNum(6), f1(x), f1(flagY))

		switch fl.Shape {
		case "circlepin":
			p.WriteString(fmt.Sprintf(`<g %s>`, common))
			p.WriteString(fmt.Sprintf(`<circle cx="%s" cy="%s" r="6" fill="%s" stroke="%s"/>`, f1(x), f1(flagY), esc(color), esc(color)))
			p.WriteString(fmt.Sprintf(
				`<text class="sc-flag-label" x="%s" y="%s" text-anchor="middle" font-size="9" fill="%s">%s</text>`,
				f1(x), f1(flagY-10), f.theme.AxisLabelColor, esc(title)))
			p.WriteString(`</g>`)
		case "squarepin":
			p.WriteString(fmt.Sprintf(`<g %s>`, common))
			p.WriteString(fmt.Sprintf(`<rect x="%s" y="%s" width="12" height="12" fill="%s"/>`, f1(x-6), f1(flagY-6), esc(color)))
			p.WriteString(fmt.Sprintf(
				`<text class="sc-flag-label" x="%s" y="%s" text-anchor="middle" font-size="9" fill="%s">%s</text>`,
				f1(x), f1(flagY-10), f.theme.AxisLabelColor, esc(title)))
			p.WriteString(`</g>`)
		default:
			stemBottom := flagY
			stemTop := flagY - flagH
			p.WriteString(fmt.Sprintf(`<g %s>`, common))
			p.WriteString(fmt.Sprintf(
				`<path class="sc-flag-glyph" d="M%s %s l0 %s l%s 0 l0 %s l%s 0 z" fill="%s" stroke="%s"/>`,
				f1(x), f1(stemBottom), f1(-flagH), f1(flagW), f1(flagH), f1(-flagW), esc(color), esc(color)))
			p.WriteString(fmt.Sprintf(
				`<text class="sc-flag-label" x="%s" y="%s" text-anchor="middle" font-size="9" fill="#ffffff">%s</text>`,
				f1(x+flagW/2), f1(stemTop+10), esc(title)))
			p.WriteString(`</g>`)
		}
	}
	p.WriteString(`</g>`)
}

func tiDataTable(spec *ChartSpec) string {
	var b strings.Builder
	b.WriteString(`<table class="sc-visually-hidden">`)
	if spec.Title != "" {
		b.WriteString("<caption>" + esc(spec.Title) + "</caption>")
	}
	b.WriteString(`<thead><tr><th scope="col">Category</th><th scope="col">Series</th><th scope="col">Value</th></tr></thead><tbody>`)
	cats := spec.XAxis.Categories
	for _, s := range spec.Series {
		for i, v := range s.Data {
			cat := fmt.Sprintf("%d", i)
			if i < len(cats) {
				cat = cats[i]
			}
			b.WriteString(`<tr><th scope="row">` + esc(cat) + `</th><td>` + esc(s.Name) + `</td><td>` + esc(fmtNum(v)) + `</td></tr>`)
		}
	}
	b.WriteString("</tbody></table>")
	return b.String()
}
