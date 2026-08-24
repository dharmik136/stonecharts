#!/usr/bin/env python3
"""Build, inspect, install, and smoke-test StoneCharts package artifacts."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_PROJECT = ROOT / "libs" / "python"
RELEASE = "0.0.0.34"
RUNTIME_MEMBER = "stonecharts/_assets/chart-interactions.js"


def run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> str:
    process = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    output = process.stdout + process.stderr
    if process.returncode != 0:
        raise RuntimeError(f"command failed ({' '.join(command)}):\n{output}")
    return output


def python_in(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def inspect_archives(wheel: Path, source: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        if RUNTIME_MEMBER not in names:
            raise RuntimeError(f"wheel is missing {RUNTIME_MEMBER}")
        if not any(name.endswith(".dist-info/licenses/LICENSE") for name in names):
            raise RuntimeError("wheel is missing its proprietary LICENSE metadata")

    with tarfile.open(source, "r:gz") as archive:
        names = {member.name for member in archive.getmembers()}
        if not any(name.endswith(f"/{RUNTIME_MEMBER}") for name in names):
            raise RuntimeError(f"source distribution is missing {RUNTIME_MEMBER}")
        if not any(name.endswith("/README.md") for name in names):
            raise RuntimeError("source distribution is missing README.md")


SMOKE = r"""
import json
import pathlib
import sys

repo = pathlib.Path(sys.argv[1])
import stonecharts
from stonecharts import ChartSpec, render_html, render_svg

assert stonecharts.__version__ == "0.0.0.34"
assert repo not in pathlib.Path(stonecharts.__file__).parents
registry = json.loads((repo / "spec/capabilities.json").read_text(encoding="utf-8"))
chart_ids = [item["id"] for item in registry["chartTypes"] if item["tier"] == "certified"]
assert len(chart_ids) == 36
for chart_id in chart_ids:
    directory = "line-basic" if chart_id == "line" else chart_id
    examples = repo / "charts" / directory / "examples"
    fixture = examples / "basic.json"
    if not fixture.exists():
        fixture = sorted(examples.glob("*.json"), key=lambda path: path.stem)[0]
    spec = ChartSpec.from_dict(json.loads(fixture.read_text(encoding="utf-8")))
    svg = render_svg(spec)
    html = render_html(spec)
    assert svg.startswith("<svg"), chart_id
    assert "window.StoneCharts" in html, chart_id
    assert "runtime not found" not in html, chart_id
print(f"installed package PASS: {len(chart_ids)} charts, runtime embedded")
"""


def qualify(output_dir: Path) -> tuple[Path, Path]:
    if (PYTHON_PROJECT / "LICENSE").read_text(encoding="utf-8") != (ROOT / "LICENSE").read_text(encoding="utf-8"):
        raise RuntimeError("libs/python/LICENSE does not match the repository license")
    output_dir.mkdir(parents=True, exist_ok=True)
    build_output = run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--sdist",
            "--wheel",
            "--outdir",
            str(output_dir),
            str(PYTHON_PROJECT),
        ]
    )
    warning_markers = ("setuptoolsdeprecationwarning", "warning: file", "missing: ")
    lowered = build_output.lower()
    found = [marker for marker in warning_markers if marker in lowered]
    if found:
        raise RuntimeError(f"package build emitted warnings ({', '.join(found)}):\n{build_output}")

    wheels = sorted(output_dir.glob(f"stonecharts-{RELEASE}-*.whl"))
    sources = sorted(output_dir.glob(f"stonecharts-{RELEASE}.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise RuntimeError(f"expected one wheel and one sdist, found {wheels!r} and {sources!r}")
    wheel, source = wheels[0], sources[0]
    inspect_archives(wheel, source)

    with tempfile.TemporaryDirectory(prefix="stonecharts-install-") as temporary:
        venv_dir = Path(temporary) / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
        installed_python = python_in(venv_dir)
        environment = os.environ.copy()
        environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        run(
            [str(installed_python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)],
            cwd=Path(temporary),
            env=environment,
        )
        smoke_output = run(
            [str(installed_python), "-c", SMOKE, str(ROOT)],
            cwd=Path(temporary),
            env=environment,
        )
        print(smoke_output.strip())
    return wheel, source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, help="Keep artifacts in this directory")
    args = parser.parse_args()
    try:
        if args.outdir:
            output_dir = args.outdir if args.outdir.is_absolute() else ROOT / args.outdir
            wheel, source = qualify(output_dir)
            print(f"package qualification PASS: {wheel.name}, {source.name}")
        else:
            with tempfile.TemporaryDirectory(prefix="stonecharts-dist-") as temporary:
                wheel, source = qualify(Path(temporary))
                print(f"package qualification PASS: {wheel.name}, {source.name}")
    except RuntimeError as exc:
        print(f"package qualification FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
