package stonecharts

import (
	"fmt"
	"strings"
)

const dumbbellPad = 0.2

func renderDumbbellSVG(spec *ChartSpec) string {
	orientation := spec.Orientation
	if orientation == "" {
		orientation = "vertical"
	}
	return renderCartesian(spec, "Dumbbell", "band", dumbbellMarks, false, orientation)
}

func dumbbellMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}
	spec := f.spec
	horiz := f.orientation == "horizontal"
	K := len(spec.Series)
	if !spec.groupingOn() {
		K = 1
	}
	if K <= 0 {
		K = 1
	}
	halo := f.theme.MarkerHalo

	for si, s := range spec.Series {
		st := f.styles[si]
		symbol := "circle"
		r := 4.0
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
		lineDash := dashArray(s.DashStyle)
		dashAttr := ""
		if lineDash != "" {
			dashAttr = fmt.Sprintf(` stroke-dasharray="%s"`, lineDash)
		}
		highArr := s.High
		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))

		if horiz {
			bandSz := f.bandHeight()
			groupSz := bandSz * (1 - dumbbellPad)
			barSz := groupSz / float64(K)

			for i := 0; i < len(s.Data) && i < f.n; i++ {
				loVal := s.Data[i]
				hiVal := loVal
				if i < len(highArr) {
					hiVal = highArr[i]
				}
				slot := 0
				if spec.groupingOn() && K > 1 {
					slot = si
				}
				bandC := f.bandCenter(i)
				slotStart := bandC - groupSz/2 + barSz*float64(slot)
				dbY := slotStart + barSz/2
				loX := f.valuePix(loVal)
				hiX := f.valuePix(hiVal)
				p.WriteString(fmt.Sprintf(
					`<line class="sc-connector" data-series="%d" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s/>`,
					si, f1(loX), f1(dbY), f1(hiX), f1(dbY), st.stroke, fmtNum(lw), dashAttr))
			}

			for i := 0; i < len(s.Data) && i < f.n; i++ {
				loVal := s.Data[i]
				slot := 0
				if spec.groupingOn() && K > 1 {
					slot = si
				}
				bandC := f.bandCenter(i)
				slotStart := bandC - groupSz/2 + barSz*float64(slot)
				dbY := slotStart + barSz/2
				loX := f.valuePix(loVal)
				lowCommon := fmt.Sprintf(`class="sc-dumbbell-low" data-series="%d"`, si)
				p.WriteString(markerSVG(symbol, loX, dbY, r, lowCommon, st.solid, halo, 1.0))
			}

			for i := 0; i < len(s.Data) && i < f.n; i++ {
				loVal := s.Data[i]
				hiVal := loVal
				if i < len(highArr) {
					hiVal = highArr[i]
				}
				slot := 0
				if spec.groupingOn() && K > 1 {
					slot = si
				}
				bandC := f.bandCenter(i)
				slotStart := bandC - groupSz/2 + barSz*float64(slot)
				dbY := slotStart + barSz/2
				hiX := f.valuePix(hiVal)
				cat := fmt.Sprintf("%d", i)
				if i < len(f.cats) {
					cat = f.cats[i]
				}
				common := fmt.Sprintf(
					`class="sc-point sc-dumbbell-high" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-low="%s" data-high="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
					si, esc(s.Name), esc(cat), esc(fmtNum(hiVal)), esc(fmtNum(loVal)), esc(fmtNum(hiVal)), st.solid, fmtNum(r), fmtNum(rHover))
				p.WriteString(markerSVG(symbol, hiX, dbY, r, common, st.solid, halo, 1.0))
			}
		} else {
			bandSz := f.bandWidth()
			groupSz := bandSz * (1 - dumbbellPad)
			barSz := groupSz / float64(K)

			for i := 0; i < len(s.Data) && i < f.n; i++ {
				loVal := s.Data[i]
				hiVal := loVal
				if i < len(highArr) {
					hiVal = highArr[i]
				}
				slot := 0
				if spec.groupingOn() && K > 1 {
					slot = si
				}
				bandC := f.xpix(float64(i))
				slotStart := bandC - groupSz/2 + barSz*float64(slot)
				dbX := slotStart + barSz/2
				loY := f.ypix(loVal)
				hiY := f.ypix(hiVal)
				p.WriteString(fmt.Sprintf(
					`<line class="sc-connector" data-series="%d" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s/>`,
					si, f1(dbX), f1(loY), f1(dbX), f1(hiY), st.stroke, fmtNum(lw), dashAttr))
			}

			for i := 0; i < len(s.Data) && i < f.n; i++ {
				loVal := s.Data[i]
				slot := 0
				if spec.groupingOn() && K > 1 {
					slot = si
				}
				bandC := f.xpix(float64(i))
				slotStart := bandC - groupSz/2 + barSz*float64(slot)
				dbX := slotStart + barSz/2
				loY := f.ypix(loVal)
				lowCommon := fmt.Sprintf(`class="sc-dumbbell-low" data-series="%d"`, si)
				p.WriteString(markerSVG(symbol, dbX, loY, r, lowCommon, st.solid, halo, 1.0))
			}

			for i := 0; i < len(s.Data) && i < f.n; i++ {
				loVal := s.Data[i]
				hiVal := loVal
				if i < len(highArr) {
					hiVal = highArr[i]
				}
				slot := 0
				if spec.groupingOn() && K > 1 {
					slot = si
				}
				bandC := f.xpix(float64(i))
				slotStart := bandC - groupSz/2 + barSz*float64(slot)
				dbX := slotStart + barSz/2
				hiY := f.ypix(hiVal)
				cat := fmt.Sprintf("%d", i)
				if i < len(f.cats) {
					cat = f.cats[i]
				}
				common := fmt.Sprintf(
					`class="sc-point sc-dumbbell-high" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-low="%s" data-high="%s" data-color="%s" data-r="%s" data-r-hover="%s"`,
					si, esc(s.Name), esc(cat), esc(fmtNum(hiVal)), esc(fmtNum(loVal)), esc(fmtNum(hiVal)), st.solid, fmtNum(r), fmtNum(rHover))
				p.WriteString(markerSVG(symbol, dbX, hiY, r, common, st.solid, halo, 1.0))
			}
		}

		p.WriteString(`</g>`)
	}
}
