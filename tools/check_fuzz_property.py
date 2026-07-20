#!/usr/bin/env python3
"""Run a deterministic fuzz/property qualification pass across Python and Go."""

from __future__ import annotations

import hashlib
import json
import random
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "releases" / "0.0.0.1" / "evidence" / "rc.1"
SEED = 20260719
CASES = 48

sys.path.insert(0, str(ROOT / "libs" / "python"))
from stonecharts import ChartSpec  # noqa: E402
from stonecharts.render import render_svg  # noqa: E402


def rand_hex(rng: random.Random) -> str:
    return "#" + "".join(rng.choice("0123456789abcdef") for _ in range(6))


def safe_text(rng: random.Random, base: str) -> str:
    suffixes = ["", " v2", " Ω", " Q4 2026", " - North", " / East"]
    return f"{base}{rng.choice(suffixes)}"


def build_specs() -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    specs: list[dict[str, Any]] = []
    for i in range(CASES):
        chart_type = rng.choice(["line", "column"])
        series_count = rng.randint(1, 4)
        point_count = rng.randint(1, 8)
        categories = [safe_text(rng, f"Cat {j + 1}") for j in range(rng.randint(0, point_count + 2))]
        series: list[dict[str, Any]] = []
        for s in range(series_count):
            if chart_type == "column":
                if rng.random() < 0.25:
                    data = [float(rng.randint(0, 30)) for _ in range(point_count)]
                else:
                    data = [float(rng.randint(0, 60)) for _ in range(point_count)]
            else:
                data = [round(rng.uniform(-40, 120), 4) for _ in range(point_count)]
            item: dict[str, Any] = {
                "name": safe_text(rng, f"Series {s + 1}"),
                "data": data,
            }
            if rng.random() < 0.4:
                item["color"] = rand_hex(rng)
            elif rng.random() < 0.7:
                item["color"] = {
                    "type": "linearGradient",
                    "x1": 0,
                    "y1": 0,
                    "x2": 0,
                    "y2": 1,
                    "stops": [
                        {"offset": 0, "color": rand_hex(rng)},
                        {"offset": 1, "color": rand_hex(rng)},
                    ],
                }
            if chart_type == "line" and rng.random() < 0.3:
                item["pattern"] = {
                    "type": "hatch",
                    "color": rand_hex(rng),
                    "background": rand_hex(rng),
                }
            if rng.random() < 0.5:
                item["dashStyle"] = rng.choice(["solid", "dashed", "dotted"])
            if chart_type == "line" and rng.random() < 0.3:
                item["curve"] = rng.choice(["linear", "monotone"])
            if chart_type == "line" and rng.random() < 0.2:
                item["step"] = rng.choice(["before", "after", "center"])
            if rng.random() < 0.3:
                item["marker"] = {
                    "symbol": rng.choice(["circle", "square", "triangle", "diamond"]),
                    "radius": round(rng.uniform(2.5, 6.5), 2),
                }
            series.append(item)

        spec: dict[str, Any] = {
            "type": chart_type,
            "title": safe_text(rng, f"Fuzz {i + 1}"),
            "subtitle": safe_text(rng, "Deterministic fuzz corpus"),
            "series": series,
            "theme": rng.choice(["light", "dark"]),
        }
        if categories and rng.random() < 0.85:
            spec["xAxis"] = {"categories": categories}
        if rng.random() < 0.4:
            spec["xAxis"] = {**spec.get("xAxis", {}), "title": safe_text(rng, "X axis")}
        if rng.random() < 0.35:
            spec["yAxis"] = {"title": safe_text(rng, "Y axis")}
        if rng.random() < 0.35:
            spec["legend"] = rng.choice([True, False])
        if rng.random() < 0.25:
            spec["responsive"] = rng.choice([True, False])
        if chart_type == "column" and rng.random() < 0.4:
            spec["grouping"] = rng.choice([True, False])
        if chart_type == "column" and rng.random() < 0.3:
            spec["stacking"] = rng.choice(["normal", "percent"])
        if rng.random() < 0.35:
            spec["layout"] = {"margin": {
                "left": rng.randint(40, 120),
                "right": rng.randint(20, 60),
                "top": rng.randint(20, 60),
                "bottom": rng.randint(30, 80),
            }}
        if rng.random() < 0.2:
            spec["a11y"] = rng.choice([True, False])
        specs.append(spec)
    return specs


def python_render(specs: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for spec in specs:
        out.append(render_svg(ChartSpec.from_dict(spec)))
    return out


def go_render(specs: list[dict[str, Any]]) -> list[str]:
    helper_dir = Path(tempfile.mkdtemp(prefix="stonecharts-fuzz-", dir=str(ROOT / "libs" / "go")))
    helper_main = helper_dir / "main.go"
    helper_main.write_text(
        """package main

import (
  "encoding/json"
  "fmt"
  "io"
  "os"
  sc "stonecharts"
)

func main() {
  b, err := io.ReadAll(os.Stdin)
  if err != nil { panic(err) }
  var raws []json.RawMessage
  if err := json.Unmarshal(b, &raws); err != nil { panic(err) }
  outs := make([]string, len(raws))
  for i, raw := range raws {
    spec, err := sc.FromJSON(raw)
    if err != nil { fmt.Fprintf(os.Stderr, "spec %d: %v\\n", i, err); os.Exit(1) }
    svg, err := sc.RenderSVG(spec)
    if err != nil { fmt.Fprintf(os.Stderr, "spec %d: %v\\n", i, err); os.Exit(1) }
    outs[i] = svg
  }
  if err := json.NewEncoder(os.Stdout).Encode(outs); err != nil { panic(err) }
}
""",
        encoding="utf-8",
    )
    proc = subprocess.run(
        ["go", "run", f"./{helper_dir.name}"],
        cwd=ROOT / "libs" / "go",
        input=json.dumps(specs),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        if proc.stdout:
            print(proc.stdout, file=sys.stderr, end="")
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")
        raise SystemExit(proc.returncode)
    try:
        return json.loads(proc.stdout)
    finally:
        shutil.rmtree(helper_dir, ignore_errors=True)


def main() -> int:
    specs = build_specs()
    py_svgs = python_render(specs)
    go_svgs = go_render(specs)

    if len(py_svgs) != len(go_svgs):
        raise SystemExit("fuzz corpus length mismatch")

    mismatches = []
    for idx, (spec, py_svg, go_svg) in enumerate(zip(specs, py_svgs, go_svgs)):
        if py_svg != go_svg:
            mismatches.append(idx)
        if "nan" in py_svg.lower() or "inf" in py_svg.lower():
            mismatches.append(idx)
        if "nan" in go_svg.lower() or "inf" in go_svg.lower():
            mismatches.append(idx)

    if mismatches:
        raise SystemExit(f"fuzz corpus mismatches at {sorted(set(mismatches))}")

    PACK.mkdir(parents=True, exist_ok=True)
    corpus_path = PACK / "fuzz-corpus.json"
    corpus_path.write_text(json.dumps(specs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report = f"""---
id: SC-REL-010
title: StoneCharts 0.0.0.1 Fuzz and Property Qualification
status: proposed
classification: informative
owner: maintainer
approver: product-owner
review_mode: self
applies_to: 0.0.0.1
requirements: [REQ-DET-001, REQ-SEC-001]
evidence: [TEST-FUZZ-PROPERTY]
last_reviewed: "2026-07-19"
review_due: "2026-08-18"
supersedes: null
superseded_by: null
---

# Fuzz And Property Qualification

- Seed: `{SEED}`
- Cases: `{CASES}`
- Result: PASS

This deterministic corpus exercised valid line and column specs across category-length,
series-count, theme, style, and layout combinations. Python and Go rendered the same
SVG bytes for every generated case, and no NaN/Inf escaped into output.
"""
    (PACK / "fuzz-property-report.md").write_text(report, encoding="utf-8")
    corpus_sha = hashlib.sha256(corpus_path.read_bytes()).hexdigest()
    print(f"fuzz property PASS: seed={SEED} cases={CASES} corpus={corpus_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
