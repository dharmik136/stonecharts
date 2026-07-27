// Go benchmarking tool for StoneCharts rendering.
//
// Implements the workload matrix from docs/quality/benchmark-spec.md
// (SC-QUAL-002): Small/Business/Dense/Stress profiles, each with line,
// grouped-column, stacked-column, bar, and scatter variants. Records cold and warm
// timing (p50/p95/p99/min/max/stddev/count), peak allocation, output bytes,
// an approximate DOM element count, and the exact input spec bytes/SHA-256
// alongside every result.
//
// Deliberately out of scope for this pass (disclosed, not silently omitted):
// runtime initialization / first-interaction latency in the browser profile
// (that belongs to the TEST-RUNTIME-BROWSER harness, not a server-render
// benchmark) and exotic environment fields (container/virtualization
// detection, power mode) that have no portable, reliable reading on a
// personal development machine.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"sort"
	"strings"
	"time"

	"stonecharts"
)

const (
	seed               = 42
	generator          = "Go rand.New(rand.NewSource(seed)).Float64()*100"
	warmupIterations   = 5
	measuredIterations = 30
)

type workload struct {
	profile    string
	series     int
	categories int
}

var workloads = []workload{
	{"small", 1, 12},
	{"business", 8, 100},
	{"dense", 20, 1000},
	{"stress", 20, 5000},
}

var variants = []string{"line", "grouped-column", "stacked-column", "bar", "scatter"}
var modes = []string{"svg", "html"}

var domTagRE = regexp.MustCompile(`<(rect|circle|ellipse|line|polyline|polygon|path|text|g)\b`)

// generateSpec deterministically builds a ChartSpec for one (workload, variant)
// cell and returns it alongside the exact JSON bytes used to build it.
func generateSpec(nSeries, nCategories int, variant string) (*stonecharts.ChartSpec, []byte) {
	rng := rand.New(rand.NewSource(seed))
	categories := make([]string, nCategories)
	for i := range categories {
		categories[i] = fmt.Sprintf("C%d", i)
	}

	series := make([]map[string]interface{}, nSeries)
	if variant == "scatter" {
		// Point-model data (positional [x,y] pairs), exercising the linear
		// x-scale path, not just the bare-number fast path (§3.3 Rank 3).
		for s := 0; s < nSeries; s++ {
			data := make([][2]float64, nCategories)
			for i := range data {
				data[i] = [2]float64{
					math.Round(rng.Float64()*1000*100) / 100,
					math.Round(rng.Float64()*100*100) / 100,
				}
			}
			series[s] = map[string]interface{}{"name": fmt.Sprintf("Series %d", s), "data": data}
		}
	} else {
		for s := 0; s < nSeries; s++ {
			data := make([]float64, nCategories)
			for i := range data {
				data[i] = math.Round(rng.Float64()*100*100) / 100
			}
			series[s] = map[string]interface{}{"name": fmt.Sprintf("Series %d", s), "data": data}
		}
	}

	chartType := "line"
	if variant == "grouped-column" || variant == "stacked-column" {
		chartType = "column"
	} else if variant == "bar" {
		chartType = "bar"
	} else if variant == "scatter" {
		chartType = "scatter"
	}

	xAxis := map[string]interface{}{"title": "X Axis"}
	if variant != "scatter" {
		xAxis["categories"] = categories
	}
	specMap := map[string]interface{}{
		"type":   chartType,
		"title":  fmt.Sprintf("Benchmark %s", variant),
		"xAxis":  xAxis,
		"yAxis":  map[string]interface{}{"title": "Y Axis"},
		"series": series,
	}
	if variant == "stacked-column" {
		specMap["stacking"] = "normal"
	}

	specBytes, err := json.Marshal(specMap)
	if err != nil {
		panic(err)
	}
	spec, err := stonecharts.FromJSON(specBytes)
	if err != nil {
		panic(err)
	}
	return spec, specBytes
}

type percentiles struct {
	P50Ms     float64
	P95Ms     float64
	P99Ms     float64
	MinMs     float64
	MaxMs     float64
	StddevMs  float64
	SampleCnt int
}

func computePercentiles(samplesMs []float64) percentiles {
	ordered := append([]float64(nil), samplesMs...)
	sort.Float64s(ordered)
	n := len(ordered)

	pct := func(p float64) float64 {
		idx := int(math.Round(p * float64(n-1)))
		if idx < 0 {
			idx = 0
		}
		if idx > n-1 {
			idx = n - 1
		}
		return ordered[idx]
	}

	mean := 0.0
	for _, v := range ordered {
		mean += v
	}
	mean /= float64(n)
	variance := 0.0
	for _, v := range ordered {
		variance += (v - mean) * (v - mean)
	}
	variance /= float64(n)

	return percentiles{
		P50Ms:     pct(0.50),
		P95Ms:     pct(0.95),
		P99Ms:     pct(0.99),
		MinMs:     ordered[0],
		MaxMs:     ordered[n-1],
		StddevMs:  math.Sqrt(variance),
		SampleCnt: n,
	}
}

type result struct {
	Profile         string  `json:"profile"`
	Series          int     `json:"series"`
	Categories      int     `json:"categories"`
	Variant         string  `json:"variant"`
	Mode            string  `json:"mode"`
	ColdMs          float64 `json:"cold_ms"`
	P50Ms           float64 `json:"p50_ms"`
	P95Ms           float64 `json:"p95_ms"`
	P99Ms           float64 `json:"p99_ms"`
	MinMs           float64 `json:"min_ms"`
	MaxMs           float64 `json:"max_ms"`
	StddevMs        float64 `json:"stddev_ms"`
	SampleCount     int     `json:"sample_count"`
	ThroughputOpSec float64 `json:"throughput_ops_sec"`
	AllocBytesPerOp uint64  `json:"peak_mem_bytes"`
	OutputBytes     int     `json:"output_bytes"`
	DOMElementCount int     `json:"dom_element_count"`
	SpecBytes       int     `json:"spec_bytes"`
	SpecSHA256      string  `json:"spec_sha256"`
}

func runCase(w workload, variant, mode string) result {
	spec, specBytes := generateSpec(w.series, w.categories, variant)
	render := func() string {
		if mode == "svg" {
			s, err := stonecharts.RenderSVG(spec)
			if err != nil {
				panic(err)
			}
			return s
		}
		s, err := stonecharts.RenderHTML(spec, "")
		if err != nil {
			panic(err)
		}
		return s
	}

	coldStart := time.Now()
	output := render()
	coldMs := float64(time.Since(coldStart).Nanoseconds()) / 1e6

	for i := 0; i < warmupIterations; i++ {
		render()
	}

	samplesMs := make([]float64, 0, measuredIterations)
	for i := 0; i < measuredIterations; i++ {
		t0 := time.Now()
		render()
		samplesMs = append(samplesMs, float64(time.Since(t0).Nanoseconds())/1e6)
	}

	var memBefore, memAfter runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&memBefore)
	render()
	runtime.ReadMemStats(&memAfter)
	allocPerOp := memAfter.TotalAlloc - memBefore.TotalAlloc

	pcts := computePercentiles(samplesMs)
	sum := 0.0
	for _, v := range samplesMs {
		sum += v
	}
	mean := sum / float64(len(samplesMs))

	sha := sha256.Sum256(specBytes)

	return result{
		Profile:         w.profile,
		Series:          w.series,
		Categories:      w.categories,
		Variant:         variant,
		Mode:            strings.ToUpper(mode),
		ColdMs:          coldMs,
		P50Ms:           pcts.P50Ms,
		P95Ms:           pcts.P95Ms,
		P99Ms:           pcts.P99Ms,
		MinMs:           pcts.MinMs,
		MaxMs:           pcts.MaxMs,
		StddevMs:        pcts.StddevMs,
		SampleCount:     pcts.SampleCnt,
		ThroughputOpSec: 1000.0 / mean,
		AllocBytesPerOp: allocPerOp,
		OutputBytes:     len([]byte(output)),
		DOMElementCount: len(domTagRE.FindAllString(output, -1)),
		SpecBytes:       len(specBytes),
		SpecSHA256:      hex.EncodeToString(sha[:]),
	}
}

func gitOutput(args ...string) string {
	cmd := exec.Command("git", args...)
	cmd.Dir = "../.."
	out, err := cmd.Output()
	if err != nil {
		return "unknown"
	}
	return strings.TrimSpace(string(out))
}

type environment struct {
	Commit             string `json:"commit"`
	DirtyTree          bool   `json:"dirty_tree"`
	GoVersion          string `json:"go_version"`
	OS                 string `json:"os"`
	Architecture       string `json:"architecture"`
	CPUCount           int    `json:"cpu_count"`
	Seed               int    `json:"seed"`
	Generator          string `json:"generator"`
	WarmupIterations   int    `json:"warmup_iterations"`
	MeasuredIterations int    `json:"measured_iterations"`
	Command            string `json:"command"`
}

func buildEnvironment() environment {
	dirty := gitOutput("status", "--porcelain") != ""
	return environment{
		Commit:             gitOutput("rev-parse", "HEAD"),
		DirtyTree:          dirty,
		GoVersion:          runtime.Version(),
		OS:                 runtime.GOOS,
		Architecture:       runtime.GOARCH,
		CPUCount:           runtime.NumCPU(),
		Seed:               seed,
		Generator:          generator,
		WarmupIterations:   warmupIterations,
		MeasuredIterations: measuredIterations,
		Command:            "go run ./cmd/benchmark",
	}
}

type payload struct {
	Environment environment `json:"environment"`
	Results     []result    `json:"results"`
}

func main() {
	if os.Getenv("STONECHARTS_RUNTIME") == "" {
		path, _ := filepath.Abs("../../runtime/chart-interactions.js")
		if _, err := os.Stat(path); err == nil {
			os.Setenv("STONECHARTS_RUNTIME", path)
		}
	}

	fmt.Println("Running Go benchmarks (please wait)...")

	var results []result
	for _, w := range workloads {
		for _, variant := range variants {
			for _, mode := range modes {
				results = append(results, runCase(w, variant, mode))
			}
		}
	}

	fmt.Println("\n# Go Benchmark Results")
	fmt.Println("| Profile | Series | Categories | Variant | Mode | Cold (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Alloc/op (B) | Output (B) | DOM elems |")
	fmt.Println("|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|")
	for _, r := range results {
		fmt.Printf("| %s | %d | %d | %s | %s | %.3f | %.3f | %.3f | %.3f | %d | %d | %d |\n",
			r.Profile, r.Series, r.Categories, r.Variant, r.Mode,
			r.ColdMs, r.P50Ms, r.P95Ms, r.P99Ms, r.AllocBytesPerOp, r.OutputBytes, r.DOMElementCount)
	}

	out := payload{Environment: buildEnvironment(), Results: results}
	resultsJSON, err := json.MarshalIndent(out, "", "  ")
	if err == nil {
		_ = os.WriteFile("benchmark_results.json", resultsJSON, 0o644)
		fmt.Printf("\nResults saved to libs/go/benchmark_results.json\n")
	}
}
