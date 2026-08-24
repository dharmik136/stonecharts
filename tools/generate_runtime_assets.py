#!/usr/bin/env python3
"""Generate or verify package-embedded copies of the canonical browser runtime."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runtime" / "chart-interactions.js"
TARGETS = [
    ROOT / "libs" / "python" / "stonecharts" / "_assets" / "chart-interactions.js",
    ROOT / "libs" / "go" / "runtime" / "chart-interactions.js",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    canonical = SOURCE.read_bytes()

    if args.generate:
        for target in TARGETS:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(canonical)
            print(f"generated {target.relative_to(ROOT).as_posix()}")

    if args.check or not args.generate:
        stale = [target for target in TARGETS if not target.exists() or target.read_bytes() != canonical]
        if stale:
            for target in stale:
                print(f"stale runtime asset: {target.relative_to(ROOT).as_posix()}", file=sys.stderr)
            print("run tools/generate_runtime_assets.py --generate", file=sys.stderr)
            return 1
        print(f"runtime assets PASS: {len(TARGETS)} package copies match the canonical source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
