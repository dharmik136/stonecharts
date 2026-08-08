"""Compare the active release corpus between Python and Go at the byte level."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "libs" / "python"))

from stonecharts import ChartSpec
from stonecharts.render import render_svg

ACTIVE = {
    "line-basic": [
        "basic",
        "styled",
        "markers",
        "spline",
        "gradient",
        "dark",
        "adversarial",
        "gradient-partial",
    ],
    "column": ["basic", "grouped", "stacked", "dark", "themed-dark", "adversarial"],
    "area": ["basic", "stacked", "percent", "themed-dark"],
    "bar": ["basic", "grouped", "stacked", "themed-dark", "adversarial"],
    "scatter": ["basic", "correlation", "regression", "themed-dark", "adversarial", "xy-points"],
    "bubble": ["basic", "multi-series", "themed-dark", "uniform-z", "adversarial"],
    "combo": ["basic", "dark", "dual-axis", "adversarial"],
    "histogram": ["basic", "prebinned", "pareto", "themed-dark", "adversarial"],
    "candlestick": ["basic", "ohlc", "heikin-ashi", "themed-dark", "adversarial"],
    "error-bar": ["basic", "overlay-grouped", "asymmetric", "themed-dark", "adversarial"],
}


GO_HELPER = """package main

import (
    "fmt"
    "os"

    stonecharts "stonecharts"
)

func main() {
    if len(os.Args) != 2 {
        fmt.Fprintln(os.Stderr, "usage: crossrender <spec.json>")
        os.Exit(2)
    }
    b, err := os.ReadFile(os.Args[1])
    if err != nil {
        panic(err)
    }
    spec, err := stonecharts.FromJSON(b)
    if err != nil {
        panic(err)
    }
    svg, err := stonecharts.RenderSVG(spec)
    if err != nil {
        panic(err)
    }
    fmt.Print(svg)
}
"""


def main() -> int:
    go_dir = ROOT / "libs" / "go"
    paths = [
        ROOT / "charts" / chart_dir / "examples" / f"{name}.json"
        for chart_dir, names in ACTIVE.items()
        for name in names
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        helper = pathlib.Path(tmpdir) / "crossrender.go"
        helper.write_text(GO_HELPER, encoding="utf-8")

        for path in paths:
            spec = json.loads(path.read_text(encoding="utf-8"))
            py = render_svg(ChartSpec.from_dict(spec)).encode("utf-8")
            proc = subprocess.run(
                ["go", "run", str(helper), str(path)],
                cwd=go_dir,
                capture_output=True,
            )
            if proc.returncode != 0:
                sys.stderr.write(proc.stderr.decode("utf-8", errors="replace"))
                return proc.returncode
            if py != proc.stdout:
                sys.stderr.write(f"mismatch: {path}\n")
                sys.stderr.write(f"python bytes: {len(py)}\n")
                sys.stderr.write(f"go bytes: {len(proc.stdout)}\n")
                return 1

    print(f"direct cross-render PASS: {len(paths)} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
