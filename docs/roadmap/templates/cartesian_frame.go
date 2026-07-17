// CartesianFrame Go Skeleton
package peakcharts

type cartesianFrame struct {
	spec                       *ChartSpec
	theme                      *Theme
	plotX, plotY, plotW, plotH float64
	n                          int
	cats                       []string
}

func (f *cartesianFrame) xpix(i int) float64 {
	return 0.0
}

func (f *cartesianFrame) ypix(v float64) float64 {
	return 0.0
}

func (f *cartesianFrame) bandWidth() float64 {
	return 0.0
}
