"""Python benchmarking script for PeakCharts rendering.

Measures rendering time, throughput, memory footprint, and file sizes across
different data scopes (3, 10, 100, 1000 points) comparing basic vs styled.
"""
from __future__ import annotations

import json
import math
import sys
import time
import tracemalloc
from pathlib import Path

# Add project root and python lib folder to path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "libs" / "python"))

from peakcharts.spec import Axis, ChartSpec, GridLine, Series
from peakcharts.render import render_html, render_svg


def generate_spec(n_points: int, styled: bool = False) -> ChartSpec:
    """Generate a deterministic ChartSpec for benchmarking."""
    data = [round(50.0 + 50.0 * math.sin(i / 10.0), 2) for i in range(n_points)]
    categories = [f"P{i}" for i in range(n_points)]
    series = [Series(name="Series 1", data=data)]

    if styled:
        return ChartSpec(
            type="line",
            title="Benchmark Styled",
            subtitle=f"Responsive + Custom Grid ({n_points} pts)",
            x_axis=Axis(title="X Axis", categories=categories),
            y_axis=Axis(
                title="Y Axis",
                grid_line=GridLine(enabled=True, color="#d5d5e0", dash_style="dashed")
            ),
            series=series,
            responsive=True,
        )
    else:
        return ChartSpec(
            type="line",
            title="Benchmark Basic",
            subtitle=f"Fixed + Default Grid ({n_points} pts)",
            x_axis=Axis(title="X Axis", categories=categories),
            y_axis=Axis(title="Y Axis"),
            series=series,
            responsive=False,
        )


def run_benchmark(n_points: int, styled: bool, mode: str, runs: int = 1000):
    spec = generate_spec(n_points, styled)
    func = lambda: render_svg(spec) if mode == "svg" else render_html(spec)

    # Warmup
    for _ in range(10):
        func()

    # Time measurement
    t0 = time.perf_counter()
    for _ in range(runs):
        func()
    t1 = time.perf_counter()
    elapsed = t1 - t0
    avg_time_ms = (elapsed / runs) * 1000.0
    throughput = runs / elapsed

    # Memory measurement
    tracemalloc.start()
    tracemalloc.clear_traces()
    # Run a few times to get a stable peak
    for _ in range(5):
        func()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # File size
    out_str = func()
    file_size = len(out_str.encode("utf-8"))

    return {
        "points": n_points,
        "layout": "Styled" if styled else "Basic",
        "mode": mode.upper(),
        "avg_time_ms": avg_time_ms,
        "throughput_ops_sec": throughput,
        "peak_mem_bytes": peak,
        "file_size_bytes": file_size,
    }


def main():
    sizes = [3, 10, 100, 1000]
    results = []

    print("Running Python benchmarks (please wait)...")
    for size in sizes:
        # Determine number of runs based on size to keep execution time reasonable
        if size <= 10:
            runs = 2000
        elif size <= 100:
            runs = 500
        else:
            runs = 50

        for styled in [False, True]:
            for mode in ["svg", "html"]:
                res = run_benchmark(size, styled, mode, runs)
                results.append(res)

    # Output Markdown Tables
    print("\n# Python Benchmark Results\n")
    
    # SVG Table
    print("## SVG Rendering Performance")
    print("| Points | Layout | Time (ms) | Throughput (ops/s) | Peak Mem (B) | Size (B) |")
    print("|-------:|:-------|----------:|-------------------:|-------------:|---------:|")
    for r in results:
        if r["mode"] == "SVG":
            print(f"| {r['points']} | {r['layout']} | {r['avg_time_ms']:.3f} ms | {r['throughput_ops_sec']:.1f} | {r['peak_mem_bytes']} B | {r['file_size_bytes']} B |")

    print("\n## HTML Rendering Performance (Full Bundle)")
    print("| Points | Layout | Time (ms) | Throughput (ops/s) | Peak Mem (B) | Size (B) |")
    print("|-------:|:-------|----------:|-------------------:|-------------:|---------:|")
    for r in results:
        if r["mode"] == "HTML":
            print(f"| {r['points']} | {r['layout']} | {r['avg_time_ms']:.3f} ms | {r['throughput_ops_sec']:.1f} | {r['peak_mem_bytes']} B | {r['file_size_bytes']} B |")

    # Save results to a json file for comparison/use
    out_file = ROOT / "libs" / "python" / "benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    main()
