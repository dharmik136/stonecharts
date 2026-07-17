package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"testing"

	"peakcharts"
)

// generateSpec creates a baseline or styled ChartSpec for benchmarking,
// then round-trips it through FromJSON to ensure all defaults are fully populated.
func generateSpec(nPoints int, styled bool) *peakcharts.ChartSpec {
	data := make([]float64, nPoints)
	categories := make([]string, nPoints)
	for i := 0; i < nPoints; i++ {
		data[i] = math.Round((50.0+50.0*math.Sin(float64(i)/10.0))*100) / 100
		categories[i] = fmt.Sprintf("P%d", i)
	}

	series := []peakcharts.Series{
		{Name: "Series 1", Data: data},
	}

	spec := &peakcharts.ChartSpec{
		Type:   "line",
		Series: series,
	}

	if styled {
		spec.Title = "Benchmark Styled"
		spec.Subtitle = fmt.Sprintf("Responsive + Custom Grid (%d pts)", nPoints)
		spec.XAxis = peakcharts.Axis{Title: "X Axis", Categories: categories}
		enabled := true
		spec.YAxis = peakcharts.Axis{
			Title: "Y Axis",
			GridLine: &peakcharts.GridLine{
				Enabled:   &enabled,
				Color:     "#d5d5e0",
				DashStyle: "dashed",
			},
		}
		spec.Responsive = true
	} else {
		spec.Title = "Benchmark Basic"
		spec.Subtitle = fmt.Sprintf("Fixed + Default Grid (%d pts)", nPoints)
		spec.XAxis = peakcharts.Axis{Title: "X Axis", Categories: categories}
		spec.YAxis = peakcharts.Axis{Title: "Y Axis"}
		spec.Responsive = false
	}

	// Round-trip to apply defaults
	b, err := json.Marshal(spec)
	if err != nil {
		panic(err)
	}
	finalSpec, err := peakcharts.FromJSON(b)
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
	// Set PEAKCHARTS_RUNTIME env var if not set so RenderHTML can find the JS file
	if os.Getenv("PEAKCHARTS_RUNTIME") == "" {
		// Look for runtime/chart-interactions.js up in the repo root
		path, _ := filepath.Abs("../../runtime/chart-interactions.js")
		if _, err := os.Stat(path); err == nil {
			os.Setenv("PEAKCHARTS_RUNTIME", path)
		}
	}

	sizes := []int{3, 10, 100, 1000}
	results := []BenchResult{}

	fmt.Println("Running Go benchmarks (please wait)...")

	for _, size := range sizes {
		for _, styled := range []bool{false, true} {
			layoutName := "Basic"
			if styled {
				layoutName = "Styled"
			}

			// 1. Benchmark SVG Rendering
			specSVG := generateSpec(size, styled)
			resSVG := testing.Benchmark(func(b *testing.B) {
				b.ReportAllocs()
				for i := 0; i < b.N; i++ {
					_ = peakcharts.RenderSVG(specSVG)
				}
			})
			svgContent := peakcharts.RenderSVG(specSVG)

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
			specHTML := generateSpec(size, styled)
			resHTML := testing.Benchmark(func(b *testing.B) {
				b.ReportAllocs()
				for i := 0; i < b.N; i++ {
					_ = peakcharts.RenderHTML(specHTML, "")
				}
			})
			htmlContent := peakcharts.RenderHTML(specHTML, "")

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
	fmt.Println("\n# Go Benchmark Results")

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
