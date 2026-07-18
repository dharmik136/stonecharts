package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"testing"

	"stonecharts"
)

// generateSpec creates a baseline, styled, markers, spline, or gradient ChartSpec for benchmarking,
// then round-trips it through FromJSON to ensure all defaults are fully populated.
func generateSpec(nPoints int, layoutType string) *stonecharts.ChartSpec {
	data1 := make([]float64, nPoints)
	data2 := make([]float64, nPoints)
	categories := make([]string, nPoints)
	for i := 0; i < nPoints; i++ {
		data1[i] = math.Round((50.0+50.0*math.Sin(float64(i)/10.0))*100) / 100
		data2[i] = math.Round((30.0+30.0*math.Cos(float64(i)/10.0))*100) / 100
		categories[i] = fmt.Sprintf("P%d", i)
	}

	series := []stonecharts.Series{
		{Name: "Series 1", Data: data1},
		{Name: "Series 2", Data: data2},
	}

	spec := &stonecharts.ChartSpec{
		Type:   "line",
		Series: series,
	}

	if layoutType == "gradient" {
		spec.ID = "demo"
		spec.Title = "Benchmark Gradient"
		spec.Subtitle = fmt.Sprintf("Responsive + Custom Grid + Gradients/Patterns (%d pts)", nPoints)
		spec.XAxis = stonecharts.Axis{Title: "X Axis", Categories: categories}
		enabled := true
		spec.YAxis = stonecharts.Axis{
			Title: "Y Axis",
			GridLine: &stonecharts.GridLine{
				Enabled:   &enabled,
				Color:     "#d5d5e0",
				DashStyle: "dashed",
			},
		}
		spec.Responsive = true
		spec.Series[0].Color = json.RawMessage(`{
			"type": "linearGradient",
			"x1": 0, "y1": 0, "x2": 0, "y2": 1,
			"stops": [
				{ "offset": 0, "color": "#2f7ed8" },
				{ "offset": 1, "color": "#1aadce" }
			]
		}`)
		spec.Series[0].FillOpacity = 0.25
		spec.Series[0].Curve = "monotone"

		spec.Series[1].Color = json.RawMessage(`"#f45b5b"`)
		spec.Series[1].Pattern = &stonecharts.Pattern{
			Type: "hatch",
			Color: "#f45b5b",
		}
	} else if layoutType == "spline" {
		spec.Title = "Benchmark Spline"
		spec.Subtitle = fmt.Sprintf("Responsive + Custom Grid + Spline (%d pts)", nPoints)
		spec.XAxis = stonecharts.Axis{Title: "X Axis", Categories: categories}
		enabled := true
		spec.YAxis = stonecharts.Axis{
			Title: "Y Axis",
			GridLine: &stonecharts.GridLine{
				Enabled:   &enabled,
				Color:     "#d5d5e0",
				DashStyle: "dashed",
			},
		}
		spec.Responsive = true
		spec.Series[0].Curve = "monotone"
		spec.Series[1].Curve = "monotone"
	} else if layoutType == "markers" {
		spec.Title = "Benchmark Markers"
		spec.Subtitle = fmt.Sprintf("Responsive + Custom Grid + Markers (%d pts)", nPoints)
		spec.XAxis = stonecharts.Axis{Title: "X Axis", Categories: categories}
		enabled := true
		spec.YAxis = stonecharts.Axis{
			Title: "Y Axis",
			GridLine: &stonecharts.GridLine{
				Enabled:   &enabled,
				Color:     "#d5d5e0",
				DashStyle: "dashed",
			},
		}
		spec.Responsive = true

		spec.Series[0].LineWidth = 3.0
		spec.Series[0].DashStyle = "dashed"
		spec.Series[0].Step = "center"
		spec.Series[0].Marker = &stonecharts.Marker{
			Enabled: &enabled,
			Symbol:  "triangle",
			Radius:  4.0,
		}

		spec.Series[1].LineWidth = 2.0
		spec.Series[1].DashStyle = "dotted"
		spec.Series[1].Step = "after"
		spec.Series[1].Marker = &stonecharts.Marker{
			Enabled: &enabled,
			Symbol:  "square",
			Radius:  4.0,
		}
	} else if layoutType == "styled" {
		spec.Title = "Benchmark Styled"
		spec.Subtitle = fmt.Sprintf("Responsive + Custom Grid (%d pts)", nPoints)
		spec.XAxis = stonecharts.Axis{Title: "X Axis", Categories: categories}
		enabled := true
		spec.YAxis = stonecharts.Axis{
			Title: "Y Axis",
			GridLine: &stonecharts.GridLine{
				Enabled:   &enabled,
				Color:     "#d5d5e0",
				DashStyle: "dashed",
			},
		}
		spec.Responsive = true
	} else {
		spec.Title = "Benchmark Basic"
		spec.Subtitle = fmt.Sprintf("Fixed + Default Grid (%d pts)", nPoints)
		spec.XAxis = stonecharts.Axis{Title: "X Axis", Categories: categories}
		spec.YAxis = stonecharts.Axis{Title: "Y Axis"}
		spec.Responsive = false
	}

	// Round-trip to apply defaults
	b, err := json.Marshal(spec)
	if err != nil {
		panic(err)
	}
	finalSpec, err := stonecharts.FromJSON(b)
	if err != nil {
		panic(err)
	}
	return finalSpec
}

type BenchResult struct {
	Points      int
	Layout      string
	Mode        string
	AvgTimeMs   float64
	Throughput  float64
	AllocBytes  uint64
	AllocCounts uint64
	FileSize    int
}

func main() {
	// Set STONECHARTS_RUNTIME env var if not set so RenderHTML can find the JS file
	if os.Getenv("STONECHARTS_RUNTIME") == "" {
		// Look for runtime/chart-interactions.js up in the repo root
		path, _ := filepath.Abs("../../runtime/chart-interactions.js")
		if _, err := os.Stat(path); err == nil {
			os.Setenv("STONECHARTS_RUNTIME", path)
		}
	}

	sizes := []int{3, 10, 100, 1000}
	results := []BenchResult{}

	fmt.Println("Running Go benchmarks (please wait)...")

	for _, size := range sizes {
		for _, layoutType := range []string{"basic", "styled", "markers", "spline", "gradient"} {
			layoutName := "Basic"
			if layoutType == "styled" {
				layoutName = "Styled"
			} else if layoutType == "markers" {
				layoutName = "Markers"
			} else if layoutType == "spline" {
				layoutName = "Spline"
			} else if layoutType == "gradient" {
				layoutName = "Gradient"
			}

			// 1. Benchmark SVG Rendering
			specSVG := generateSpec(size, layoutType)
			resSVG := testing.Benchmark(func(b *testing.B) {
				b.ReportAllocs()
				for i := 0; i < b.N; i++ {
					if _, err := stonecharts.RenderSVG(specSVG); err != nil {
						panic(err)
					}
				}
			})
			svgContent, err := stonecharts.RenderSVG(specSVG)
			if err != nil {
				panic(err)
			}

			results = append(results, BenchResult{
				Points:      size,
				Layout:      layoutName,
				Mode:        "SVG",
				AvgTimeMs:   float64(resSVG.NsPerOp()) / 1e6,
				Throughput:  1e9 / float64(resSVG.NsPerOp()),
				AllocBytes:  resSVG.MemBytes / uint64(resSVG.N),
				AllocCounts: resSVG.MemAllocs / uint64(resSVG.N),
				FileSize:    len([]byte(svgContent)),
			})

			// 2. Benchmark HTML Rendering
			specHTML := generateSpec(size, layoutType)
			resHTML := testing.Benchmark(func(b *testing.B) {
				b.ReportAllocs()
				for i := 0; i < b.N; i++ {
					if _, err := stonecharts.RenderHTML(specHTML, ""); err != nil {
						panic(err)
					}
				}
			})
			htmlContent, err := stonecharts.RenderHTML(specHTML, "")
			if err != nil {
				panic(err)
			}

			results = append(results, BenchResult{
				Points:      size,
				Layout:      layoutName,
				Mode:        "HTML",
				AvgTimeMs:   float64(resHTML.NsPerOp()) / 1e6,
				Throughput:  1e9 / float64(resHTML.NsPerOp()),
				AllocBytes:  resHTML.MemBytes / uint64(resHTML.N),
				AllocCounts: resHTML.MemAllocs / uint64(resHTML.N),
				FileSize:    len([]byte(htmlContent)),
			})
		}
	}

	// Output Markdown Tables
	fmt.Println("\n# Go Benchmark Results (Phase 4)")

	fmt.Println("## SVG Rendering Performance")
	fmt.Println("| Points | Layout | Time (ms) | Throughput (ops/s) | Alloc Mem (B/op) | Alloc Count | Size (B) |")
	fmt.Println("|-------:|:-------|----------:|-------------------:|-----------------:|------------:|---------:|")
	for _, r := range results {
		if r.Mode == "SVG" {
			fmt.Printf("| %d | %s | %.4f ms | %.1f | %d B | %d | %d B |\n",
				r.Points, r.Layout, r.AvgTimeMs, r.Throughput, r.AllocBytes, r.AllocCounts, r.FileSize)
		}
	}

	fmt.Println("\n## HTML Rendering Performance (Full Bundle)")
	fmt.Println("| Points | Layout | Time (ms) | Throughput (ops/s) | Alloc Mem (B/op) | Alloc Count | Size (B) |")
	fmt.Println("|-------:|:-------|----------:|-------------------:|-----------------:|------------:|---------:|")
	for _, r := range results {
		if r.Mode == "HTML" {
			fmt.Printf("| %d | %s | %.4f ms | %.1f | %d B | %d | %d B |\n",
				r.Points, r.Layout, r.AvgTimeMs, r.Throughput, r.AllocBytes, r.AllocCounts, r.FileSize)
		}
	}

	// Save results to JSON file
	resultsJSON, err := json.MarshalIndent(results, "", "  ")
	if err == nil {
		_ = os.WriteFile("benchmark_results.json", resultsJSON, 0o644)
		fmt.Printf("\nResults saved to libs/go/benchmark_results.json\n")
	}
}
