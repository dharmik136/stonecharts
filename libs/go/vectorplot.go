package stonecharts

import (
	"fmt"
	"math"
	"strings"
)

func renderVectorPlotSVG(spec *ChartSpec) string {
	mod := *spec
	mod.Series = make([]Series, len(spec.Series))
	copy(mod.Series, spec.Series)

	for i := range mod.Series {
		s := &mod.Series[i]
		xArr := s.X
		if len(xArr) == 0 {
			xArr = make([]float64, len(s.Data))
			for j := range s.Data {
				xArr[j] = float64(j)
			}
		}
		n := len(xArr)
		if len(s.Data) < n {
			n = len(s.Data)
		}
		s.DataPoints = make([]Datum, n)
		for j := 0; j < n; j++ {
			s.DataPoints[j] = Datum{X: xArr[j], Y: s.Data[j]}
		}
	}
	return renderCartesian(&mod, "Vector plot", "linear", vectorPlotMarks, false)
}

const (
	vpHeadLen   = 6.0
	vpHeadAngle = 25.0
)

func vectorPlotMarks(f *cartesianFrame, p *strings.Builder) {
	if f.n <= 0 {
		return
	}

	vectorLength := fdef(f.spec.VectorLength, 20)
	rotationOrigin := f.spec.RotationOrigin
	if rotationOrigin == "" {
		rotationOrigin = "center"
	}

	lmax := 0.0
	for _, s := range f.spec.Series {
		for _, v := range s.Length {
			if v > lmax {
				lmax = v
			}
		}
	}

	arrowPx := func(length float64) float64 {
		if lmax <= 0.0 {
			return 0.0
		}
		return vectorLength * (length / lmax)
	}

	ha := vpHeadAngle * math.Pi / 180.0
	ca := math.Cos(ha)
	sa := math.Sin(ha)

	for si, s := range f.spec.Series {
		st := f.styles[si]

		xArr := s.X
		if len(xArr) == 0 {
			xArr = make([]float64, len(s.Data))
			for i := range s.Data {
				xArr[i] = float64(i)
			}
		}
		yArr := s.Data
		dirArr := s.Direction
		if len(dirArr) == 0 {
			dirArr = make([]float64, len(s.Data))
		}
		lenArr := s.Length
		if len(lenArr) == 0 {
			lenArr = make([]float64, len(s.Data))
		}

		nPts := len(xArr)
		if len(yArr) < nPts {
			nPts = len(yArr)
		}
		if len(dirArr) < nPts {
			nPts = len(dirArr)
		}
		if len(lenArr) < nPts {
			nPts = len(lenArr)
		}

		stroke := st.fill
		lineWidth := 1.5
		if s.LineWidth > 0 {
			lineWidth = s.LineWidth
		}

		p.WriteString(fmt.Sprintf(`<g class="sc-series" data-series="%d">`, si))

		for i := 0; i < nPts; i++ {
			xv := xArr[i]
			yv := yArr[i]
			dv := dirArr[i]
			lv := lenArr[i]

			cx := f.xpix(xv)
			cy := f.ypix(yv)

			rad := dv * math.Pi / 180.0
			ux := math.Sin(rad)
			uy := -math.Cos(rad)

			bigL := arrowPx(lv)
			half := bigL / 2.0

			var ax, ay float64
			switch rotationOrigin {
			case "start":
				ax, ay = cx, cy
			case "end":
				ax, ay = cx-ux*bigL, cy-uy*bigL
			default:
				ax, ay = cx-ux*half, cy-uy*half
			}

			tailx, taily := ax, ay
			headx, heady := ax+ux*bigL, ay+uy*bigL

			lbx := headx + vpHeadLen*((-ux)*ca-(-uy)*sa)
			lby := heady + vpHeadLen*((-ux)*sa+(-uy)*ca)
			rbx := headx + vpHeadLen*((-ux)*ca+(-uy)*sa)
			rby := heady + vpHeadLen*(-(-ux)*sa+(-uy)*ca)

			d := fmt.Sprintf("M%s %s L%s %s M%s %s L%s %s L%s %s",
				f1(tailx), f1(taily), f1(headx), f1(heady),
				f1(lbx), f1(lby), f1(headx), f1(heady), f1(rbx), f1(rby))

			p.WriteString(fmt.Sprintf(
				`<path class="sc-vector sc-point" data-series="%d" data-series-name="%s" data-x="%s" data-y="%s" data-direction="%s" data-length="%s" data-color="%s" data-r="%s" data-r-hover="%s" cx="%s" cy="%s" d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"/>`,
				si, esc(s.Name), esc(fmtNum(xv)), esc(fmtNum(yv)),
				esc(fmtNum(dv)), esc(fmtNum(lv)),
				st.solid, fmtNum(lineWidth), fmtNum(lineWidth),
				f1(cx), f1(cy), d, stroke, fmtNum(lineWidth)))
		}

		p.WriteString(`</g>`)
	}
}
