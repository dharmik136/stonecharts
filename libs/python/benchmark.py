"""Python benchmarking script for StoneCharts rendering.

Measures rendering time, throughput, memory footprint, and file sizes across
different data scopes (3, 10, 100, 1000 points) comparing basic, styled, markers, spline, and gradient layouts.
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

from stonecharts.spec import Axis, ChartSpec, GridLine, Series, Marker, Gradient, GradientStop, Pattern
from stonecharts.render import render_html, render_svg


def generate_spec(n_points: int, layout_type: str = "basic") -> ChartSpec:
    """Generate a deterministic ChartSpec with 2 series for benchmarking."""
    data1 = [round(50.0 + 50.0 * math.sin(i / 10.0), 2) for i in range(n_points)]
    data2 = [round(30.0 + 30.0 * math.cos(i / 10.0), 2) for i in range(n_points)]
    categories = [f"P{i}" for i in range(n_points)]

    if layout_type == "gradient":
        # New Phase 4 gradient layout: 2 series with gradient area and hatch pattern fills
        series = [
            Series(
                name="Series 1",
                data=data1,
                color=Gradient(
                    stops=[
                        GradientStop(offset=0.0, color="#2f7ed8"),
                        GradientStop(offset=1.0, color="#1aadce")
                    ]
                ),
                fill_opacity=0.25,
                curve="monotone",
            ),
            Series(
                name="Series 2",
                data=data2,
                color="#f45b5b",
                pattern=Pattern(type="hatch", color="#f45b5b", size=8.0, angle=45.0, stroke_width=1.5)
            )
        ]
        return ChartSpec(
            type="line",
            id="demo",
            title="Benchmark Gradient",
            subtitle=f"Responsive + Custom Grid + Gradients/Patterns ({n_points} pts)",
            x_axis=Axis(title="X Axis", categories=categories),
            y_axis=Axis(
                title="Y Axis",
                grid_line=GridLine(enabled=True, color="#d5d5e0", dash_style="dashed")
            ),
            series=series,
            responsive=True,
        )
    elif layout_type == "spline":
        series = [
            Series(name="Series 1", data=data1, curve="monotone"),
            Series(name="Series 2", data=data2, curve="monotone")
        ]
        return ChartSpec(
            type="line",
            title="Benchmark Spline",
            subtitle=f"Responsive + Custom Grid + Spline ({n_points} pts)",
            x_axis=Axis(title="X Axis", categories=categories),
            y_axis=Axis(
                title="Y Axis",
                grid_line=GridLine(enabled=True, color="#d5d5e0", dash_style="dashed")
            ),
            series=series,
            responsive=True,
        )
    elif layout_type == "markers":
        series = [
            Series(
                name="Series 1",
                data=data1,
                line_width=3.0,
                dash_style="dashed",
                step="center",
                marker=Marker(enabled=True, symbol="triangle", radius=4.0)
            ),
            Series(
                name="Series 2",
                data=data2,
                line_width=2.0,
                dash_style="dotted",
                step="after",
                marker=Marker(enabled=True, symbol="square", radius=4.0)
            )
        ]
        return ChartSpec(
            type="line",
            title="Benchmark Markers",
            subtitle=f"Responsive + Custom Grid + Markers ({n_points} pts)",
            x_axis=Axis(title="X Axis", categories=categories),
            y_axis=Axis(
                title="Y Axis",
                grid_line=GridLine(enabled=True, color="#d5d5e0", dash_style="dashed")
            ),
            series=series,
            responsive=True,
        )
    elif layout_type == "styled":
        series = [
            Series(name="Series 1", data=data1),
            Series(name="Series 2", data=data2)
        ]
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
        series = [
            Series(name="Series 1", data=data1),
            Series(name="Series 2", data=data2)
        ]
        return ChartSpec(
            type="line",
            title="Benchmark Basic",
            subtitle=f"Fixed + Default Grid ({n_points} pts)",
            x_axis=Axis(title="X Axis", categories=categories),
            y_axis=Axis(title="Y Axis"),
            series=series,
            responsive=False,
        )


def run_benchmark(n_points: int, layout_type: str, mode: str, runs: int = 1000):
    spec = generate_spec(n_points, layout_type)
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
    for _ in range(5):
        func()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # File size
    out_str = func()
    file_size = len(out_str.encode("utf-8"))

    return {
        "points": n_points,
        "layout": layout_type.capitalize(),
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
        if size <= 10:
            runs = 2000
        elif size <= 100:
            runs = 500
        else:
            runs = 50

        for layout_type in ["basic", "styled", "markers", "spline", "gradient"]:
            for mode in ["svg", "html"]:
                res = run_benchmark(size, layout_type, mode, runs)
                results.append(res)

    # Output Markdown Tables
    print("\n# Python Benchmark Results (Phase 4)\n")
    
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
