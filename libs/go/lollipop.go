package stonecharts

import (
	"fmt"
	"strings"
)

const lollipopPad = 0.2

func renderLollipopSVG(spec *ChartSpec) string {
	orientation := spec.Orientation
	if orientation == "" {
		orientation = "vertical"
	}
	return renderCartesian(spec, "Lollipop", "band", lollipopMarks, true, orientation)
}

func lollipopMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}
	spec := f.spec
	horiz := f.orientation == "horizontal"
	stacked := f.stacking == "normal" || f.stacking == "percent"
	K := len(spec.Series)
	if stacked || !spec.groupingOn() {
		K = 1
	}
	if K <= 0 {
		K = 1
	}
	halo := f.theme.MarkerHalo

	for si, s := range spec.Series {
		st := f.styles[si]
		symbol := "circle"
		r := 3.5
		if s.Marker != nil {
			if s.Marker.Symbol != "" {
				symbol = s.Marker.Symbol
			}
			if s.Marker.Radius != 0 {
				r = s.Marker.Radius
			}
		}
		rHover := r * 1.5
		lw := 2.0
		if s.LineWidth != 0 {
			lw = s.LineWidth
		}
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))

		if horiz {
			bandSz := f.bandHeight()
			groupSz := bandSz * (1 - lollipopPad)
			barSz := groupSz / float64(K)
			baseline := f.valuePix(0.0)

			for i, v := range s.Data {
				if i >= f.n {
					break
				}
				slot := 0
				if spec.groupingOn() && !stacked {
					slot = si
				}
				bandC := f.bandCenter(i)
				slotStart := bandC - groupSz/2 + barSz*float64(slot)
				stemY := slotStart + barSz/2
				valX := f.valuePix(v)
				p.WriteString(fmt.Sprintf(
					`<line class="sc-stem" data-series="%d" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>`,
					si, f1(baseline), f1(stemY), f1(valX), f1(stemY), st.stroke, fmtNum(lw)))
			}

			for i, v := range s.Data {
				if i >= f.n {
					break
				}
				slot := 0
				if spec.groupingOn() && !stacked {
					slot = si
				}
				bandC := f.bandCenter(i)
				slotStart := bandC - groupSz/2 + barSz*float64(slot)
				stemY := slotStart + barSz/2
				valX := f.valuePix(v)
				cat := fmt.Sprintf("%d", i)
				if i < len(f.cats) {
					cat = f.cats[i]
				}
				common := fmt.Sprintf(
					`class="sc-point sc-lollipop-head" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
					si, esc(s.Name), esc(cat), esc(fmtNum(v)), st.solid, fmtNum(r), fmtNum(rHover))
				p.WriteString(markerSVG(symbol, valX, stemY, r, common, st.solid, halo, 1.0))
			}
		} else {
			bandSz := f.bandWidth()
			groupSz := bandSz * (1 - lollipopPad)
			barSz := groupSz / float64(K)
			baselineY := f.ypix(0.0)

			for i, v := range s.Data {
				if i >= f.n {
					break
				}
				slot := 0
				if spec.groupingOn() && !stacked {
					slot = si
				}
				bandC := f.xpix(float64(i))
				slotStart := bandC - groupSz/2 + barSz*float64(slot)
				stemX := slotStart + barSz/2
				valY := f.ypix(v)
				p.WriteString(fmt.Sprintf(
					`<line class="sc-stem" data-series="%d" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>`,
					si, f1(stemX), f1(baselineY), f1(stemX), f1(valY), st.stroke, fmtNum(lw)))
			}

			for i, v := range s.Data {
				if i >= f.n {
					break
				}
				slot := 0
				if spec.groupingOn() && !stacked {
					slot = si
				}
				bandC := f.xpix(float64(i))
				slotStart := bandC - groupSz/2 + barSz*float64(slot)
				stemX := slotStart + barSz/2
				valY := f.ypix(v)
				cat := fmt.Sprintf("%d", i)
				if i < len(f.cats) {
					cat = f.cats[i]
				}
				common := fmt.Sprintf(
					`class="sc-point sc-lollipop-head" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
					si, esc(s.Name), esc(cat), esc(fmtNum(v)), st.solid, fmtNum(r), fmtNum(rHover))
				p.WriteString(markerSVG(symbol, stemX, valY, r, common, st.solid, halo, 1.0))
			}
		}

		p.WriteString(`</g>`)
	}
}
