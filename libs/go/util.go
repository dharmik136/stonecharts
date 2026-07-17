package peakcharts

import (
	"math"
	"strconv"
	"strings"
)

// niceNum / niceTicks mirror libs/python/peakcharts/util.py exactly (Heckbert
// "nice numbers") so both languages land on identical axis ticks.
func niceNum(x float64, round bool) float64 {
	if x == 0 {
		return 0
	}
	exp := math.Floor(math.Log10(math.Abs(x)))
	frac := math.Abs(x) / math.Pow(10, exp)
	var nf float64
	if round {
		switch {
		case frac < 1.5:
			nf = 1
		case frac < 3:
			nf = 2
		case frac < 7:
			nf = 5
		default:
			nf = 10
		}
	} else {
		switch {
		case frac <= 1:
			nf = 1
		case frac <= 2:
			nf = 2
		case frac <= 5:
			nf = 5
		default:
			nf = 10
		}
	}
	return nf * math.Pow(10, exp)
}

func niceTicks(lo, hi float64, target int) (float64, float64, []float64) {
	if lo == hi {
		if lo == 0 {
			lo, hi = -1, 1
		} else {
			pad := math.Abs(lo) * 0.1
			lo, hi = lo-pad, hi+pad
		}
	}
	rng := niceNum(hi-lo, false)
	denom := target - 1
	if denom < 1 {
		denom = 1
	}
	step := niceNum(rng/float64(denom), true)
	if step == 0 {
		step = 1
	}
	axisMin := math.Floor(lo/step) * step
	axisMax := math.Ceil(hi/step) * step
	count := int(math.Round((axisMax - axisMin) / step))
	ticks := make([]float64, 0, count+1)
	for i := 0; i <= count; i++ {
		ticks = append(ticks, axisMin+float64(i)*step)
	}
	return axisMin, axisMax, ticks
}

func esc(s string) string {
	r := strings.NewReplacer("&", "&amp;", "<", "&lt;", ">", "&gt;", `"`, "&quot;")
	return r.Replace(s)
}

// fmtNum mirrors Python fmt_num: drop trailing .0, else shortest round-trip.
func fmtNum(v float64) string {
	if v == math.Trunc(v) {
		return strconv.Itoa(int(v))
	}
	return strconv.FormatFloat(v, 'g', -1, 64)
}

// f1 mirrors Python f"{v:.1f}".
func f1(v float64) string {
	return strconv.FormatFloat(v, 'f', 1, 64)
}
