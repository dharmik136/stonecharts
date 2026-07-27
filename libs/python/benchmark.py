"""Python benchmarking script for StoneCharts rendering.

Implements the workload matrix from docs/quality/benchmark-spec.md (SC-QUAL-002):
Small/Business/Dense/Stress profiles, each with line, grouped-column,
stacked-column, bar, and scatter variants. Records cold and warm timing (p50/p95/p99/
min/max/stddev/count), peak memory, output bytes, an approximate DOM element
count, and the exact input spec bytes/SHA-256 alongside every result.

Deliberately out of scope for this pass (disclosed, not silently omitted):
runtime initialization / first-interaction latency in the browser profile
(that belongs to the TEST-RUNTIME-BROWSER harness, not a server-render
benchmark) and exotic environment fields (container/virtualization
detection, power mode) that have no portable, reliable reading on a
personal development machine.
"""
from __future__ import annotations

import hashlib
import json
import platform
import random
import re
import statistics
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "libs" / "python"))

from stonecharts.spec import Axis, ChartSpec, Series  # noqa: E402
from stonecharts.render import render_html, render_svg  # noqa: E402

SEED = 42
GENERATOR = "python random.Random(seed).uniform(0, 100)"
WARMUP_ITERATIONS = 5
MEASURED_ITERATIONS = 30

WORKLOADS = [
    ("small", 1, 12),
    ("business", 8, 100),
    ("dense", 20, 1000),
    ("stress", 20, 5000),
]
VARIANTS = ["line", "grouped-column", "stacked-column", "bar", "scatter"]
MODES = ["svg", "html"]

_DOM_TAG_RE = re.compile(r"<(rect|circle|ellipse|line|polyline|polygon|path|text|g)\b")


def generate_spec(n_series: int, n_categories: int, variant: str) -> tuple[ChartSpec, bytes]:
    """Deterministically generate a ChartSpec for one (workload, variant) cell.

    Returns the spec plus the exact JSON bytes used to build it, so callers can
    record input spec bytes and SHA-256 alongside the measured results.
    """
    rng = random.Random(SEED)
    categories = [f"C{i}" for i in range(n_categories)]

    if variant == "scatter":
        # Point-model data (positional [x,y] pairs), exercising the linear
        # x-scale path, not just the bare-number fast path (§3.3 Rank 3).
        series = [
            {
                "name": f"Series {s}",
                "data": [
                    [round(rng.uniform(0, 1000), 2), round(rng.uniform(0, 100), 2)]
                    for _ in range(n_categories)
                ],
            }
            for s in range(n_series)
        ]
    else:
        series = [
            {
                "name": f"Series {s}",
                "data": [round(rng.uniform(0, 100), 2) for _ in range(n_categories)],
            }
            for s in range(n_series)
        ]

    if variant in ("grouped-column", "stacked-column"):
        chart_type = "column"
    elif variant == "bar":
        chart_type = "bar"
    elif variant == "scatter":
        chart_type = "scatter"
    else:
        chart_type = "line"
    spec_dict = {
        "type": chart_type,
        "title": f"Benchmark {variant}",
        "xAxis": {"title": "X Axis"},
        "yAxis": {"title": "Y Axis"},
        "series": series,
    }
    if variant != "scatter":
        spec_dict["xAxis"]["categories"] = categories
    if variant == "stacked-column":
        spec_dict["stacking"] = "normal"

    spec_bytes = json.dumps(spec_dict, sort_keys=True).encode("utf-8")
    spec = ChartSpec.from_dict(spec_dict)
    return spec, spec_bytes


def _percentiles(samples_ms: list[float]) -> dict:
    ordered = sorted(samples_ms)
    n = len(ordered)

    def pct(p: float) -> float:
        idx = min(n - 1, max(0, round(p * (n - 1))))
        return ordered[idx]

    return {
        "p50_ms": pct(0.50),
        "p95_ms": pct(0.95),
        "p99_ms": pct(0.99),
        "min_ms": ordered[0],
        "max_ms": ordered[-1],
        "stddev_ms": statistics.pstdev(ordered) if n > 1 else 0.0,
        "sample_count": n,
    }


def run_case(profile: str, n_series: int, n_categories: int, variant: str, mode: str) -> dict:
    spec, spec_bytes = generate_spec(n_series, n_categories, variant)
    func = (lambda: render_svg(spec)) if mode == "svg" else (lambda: render_html(spec))

    cold_start = time.perf_counter()
    output = func()
    cold_ms = (time.perf_counter() - cold_start) * 1000.0

    for _ in range(WARMUP_ITERATIONS):
        func()

    samples_ms = []
    for _ in range(MEASURED_ITERATIONS):
        t0 = time.perf_counter()
        func()
        samples_ms.append((time.perf_counter() - t0) * 1000.0)

    tracemalloc.start()
    tracemalloc.clear_traces()
    func()
    _, peak_mem_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "profile": profile,
        "series": n_series,
        "categories": n_categories,
        "variant": variant,
        "mode": mode.upper(),
        "cold_ms": cold_ms,
        **_percentiles(samples_ms),
        "throughput_ops_sec": 1000.0 / statistics.mean(samples_ms),
        "peak_mem_bytes": peak_mem_bytes,
        "output_bytes": len(output.encode("utf-8")),
        "dom_element_count": len(_DOM_TAG_RE.findall(output)),
        "spec_bytes": len(spec_bytes),
        "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
    }


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unknown"


def environment() -> dict:
    dirty = bool(_git("status", "--porcelain"))
    return {
        "commit": _git("rev-parse", "HEAD"),
        "dirty_tree": dirty,
        "python_version": platform.python_version(),
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "cpu_count": __import__("os").cpu_count(),
        "seed": SEED,
        "generator": GENERATOR,
        "warmup_iterations": WARMUP_ITERATIONS,
        "measured_iterations": MEASURED_ITERATIONS,
        "command": "python libs/python/benchmark.py",
    }


def main():
    print("Running Python benchmarks (please wait)...")
    results = []
    for profile, n_series, n_categories in WORKLOADS:
        for variant in VARIANTS:
            for mode in MODES:
                results.append(run_case(profile, n_series, n_categories, variant, mode))

    print("\n# Python Benchmark Results\n")
    print("| Profile | Series | Categories | Variant | Mode | Cold (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Peak Mem (B) | Output (B) | DOM elems |")
    print("|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        print(
            f"| {r['profile']} | {r['series']} | {r['categories']} | {r['variant']} | {r['mode']} "
            f"| {r['cold_ms']:.3f} | {r['p50_ms']:.3f} | {r['p95_ms']:.3f} | {r['p99_ms']:.3f} "
            f"| {r['peak_mem_bytes']} | {r['output_bytes']} | {r['dom_element_count']} |"
        )

    payload = {"environment": environment(), "results": results}
    out_file = ROOT / "libs" / "python" / "benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    main()
