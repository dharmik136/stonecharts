package stonecharts

import (
	"fmt"
	"math"
	"sort"
	"strings"
)

const bulletPad = 0.2
const bulletMeasureRatio = 0.4
const bulletTargetRatio = 0.6
const bulletTargetWidth = 2

var lightRangeShades = []string{"#cccccc", "#dddddd", "#eeeeee"}
var darkRangeShades = []string{"#3d3d55", "#2d2d42", "#1e1e30"}

func rangeFills(n int, isDark bool) []string {
	shades := lightRangeShades
	if isDark {
		shades = darkRangeShades
	}
	fills := make([]string, n)
	for k := 0; k < n; k++ {
		idx := k
		if idx >= len(shades) {
			idx = len(shades) - 1
		}
		fills[k] = shades[idx]
	}
	return fills
}

func renderBulletSVG(spec *ChartSpec) string {
	s2 := *spec
	s2.Series = make([]Series, len(spec.Series))
	copy(s2.Series, spec.Series)

	ranges := s2.BulletRanges
	target := s2.BulletTarget

	allVals := []float64{0.0}
	for _, s := range s2.Series {
		allVals = append(allVals, s.Data...)
	}
	if target != nil {
		allVals = append(allVals, *target)
	}
	allVals = append(allVals, ranges...)

	if s2.YAxis.Min == nil {
		mn := allVals[0]
		for _, v := range allVals[1:] {
			if v < mn {
				mn = v
			}
		}
		s2.YAxis.Min = &mn
	}
	if s2.YAxis.Max == nil {
		mx := allVals[0]
		for _, v := range allVals[1:] {
			if v > mx {
				mx = v
			}
		}
		s2.YAxis.Max = &mx
	}

	return renderCartesian(&s2, "Bullet", "band", bulletMarks, true, "horizontal")
}

func bulletMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}
	spec := f.spec
	ranges := spec.BulletRanges
	target := spec.BulletTarget
	isDark := f.theme.Name == "dark"
	targetColor := "#333333"
	if isDark {
		targetColor = "#cccccc"
	}

	bandHeight := f.bandHeight()
	groupH := bandHeight * (1 - bulletPad)
	stacked := f.stacking == "normal" || f.stacking == "percent"
	kSlots := len(f.spec.Series)
	if stacked || !f.spec.groupingOn() {
		kSlots = 1
	}
	if kSlots <= 0 {
		kSlots = 1
	}
	barH := groupH / float64(kSlots)
	measureH := barH * bulletMeasureRatio
	targetH := barH * bulletTargetRatio
	baseline := f.valueZero()

	if len(ranges) > 0 {
		sortedRanges := make([]float64, len(ranges))
		copy(sortedRanges, ranges)
		sort.Float64s(sortedRanges)
		fills := rangeFills(len(sortedRanges), isDark)
		for i := 0; i < f.n; i++ {
			cyBand := f.bandCenter(i)
			bandTop := cyBand - groupH/2
			prevX := baseline
			for k, rVal := range sortedRanges {
				rx := f.valuePix(rVal)
				x := math.Min(prevX, rx)
				w := math.Abs(rx - prevX)
				p.WriteString(fmt.Sprintf(
					`<rect class="sc-range" x="%s" y="%s" width="%s" height="%s" fill="%s"/>`,
					f1(x), f1(bandTop), f1(w), f1(groupH), fills[k]))
				prevX = rx
			}
		}
	}

	for si, s := range spec.Series {
		st := f.styles[si]
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))
		for i, raw := range s.Data {
			if i >= f.n {
				break
			}
			cyBand := f.bandCenter(i)
			slot := 0
			if f.spec.groupingOn() && !stacked {
				slot = si
			}
			slotTop := cyBand - groupH/2 + barH*float64(slot)
			measureTop := slotTop + (barH-measureH)/2

			xv := f.valuePix(raw)
			x := math.Min(baseline, xv)
			w := math.Abs(baseline - xv)
			tip := xv
			cy := measureTop + measureH/2

			ylabel := fmt.Sprintf("%d", i)
			if i < len(f.cats) {
				ylabel = f.cats[i]
			}
			common := fmt.Sprintf(
				`class="sc-bar sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="3.5" data-r-hover="6"`,
				si, esc(s.Name), esc(ylabel), esc(fmtNum(raw)), st.solid)
			p.WriteString(fmt.Sprintf(
				`<rect %s cx="%s" cy="%s" x="%s" y="%s" width="%s" height="%s" fill="%s"/>`,
				common, f1(tip), f1(cy), f1(x), f1(measureTop), f1(w), f1(measureH), st.fill))
		}
		p.WriteString(`</g>`)
	}

	if target != nil {
		tv := *target
		for i := 0; i < f.n; i++ {
			cyBand := f.bandCenter(i)
			targetTop := cyBand - targetH/2
			tx := f.valuePix(tv)
			p.WriteString(fmt.Sprintf(
				`<line class="sc-target" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%d"/>`,
				f1(tx), f1(targetTop), f1(tx), f1(targetTop+targetH), targetColor, bulletTargetWidth))
		}
	}
}
