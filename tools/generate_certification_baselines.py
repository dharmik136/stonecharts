#!/usr/bin/env python3
"""Generate or verify certified StoneVerify baselines for all 36 charts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "tools" / "stonecharts_verify.py"
RELEASE = "0.0.0.34"
GENERATED_AT = "2026-08-24T00:00:00+00:00"


def chart_directory(chart_id: str) -> str:
    return "line-basic" if chart_id == "line" else chart_id


def fixture_for(chart_id: str) -> Path:
    examples = ROOT / "charts" / chart_directory(chart_id) / "examples"
    basic = examples / "basic.json"
    if basic.exists():
        return basic
    preferred = {"xrange": "gantt.json"}.get(chart_id)
    if preferred and (examples / preferred).exists():
        return examples / preferred
    fixtures = sorted(examples.glob("*.json"))
    if not fixtures:
        raise RuntimeError(f"{chart_id}: no valid examples found")
    return fixtures[0]


def load_chart_ids() -> list[str]:
    registry = json.loads((ROOT / "spec" / "capabilities.json").read_text(encoding="utf-8"))
    return [item["id"] for item in registry["chartTypes"] if item["tier"] == "certified"]


def inspect_baseline(chart_id: str) -> list[str]:
    evidence = ROOT / "evidence-baselines" / chart_id
    manifest_path = evidence / "manifest.json"
    if not manifest_path.exists():
        return ["manifest missing"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"manifest unreadable: {exc}"]

    assurance = manifest.get("assurance", {})
    runtimes = manifest.get("runtimes", [])
    go_runtime = next((runtime for runtime in runtimes if runtime.get("runtime") == "go"), {})
    go_binary = str(go_runtime.get("goBinary", ""))
    source = str(manifest.get("input", {}).get("source", ""))
    checks = {
        "status is pass": manifest.get("status") == "pass",
        "certified profile": assurance.get("profile") == "certified",
        "certified tier": assurance.get("tier") == "certified",
        "certified guarantee eligible": assurance.get("eligibleForCertifiedGuarantee") is True,
        "chart type matches directory": assurance.get("chartType") == chart_id,
        "exactly Python and Go": len(runtimes) == 2
        and {runtime.get("runtime") for runtime in runtimes} == {"python", "go"},
        f"both runtimes are {RELEASE}": bool(runtimes)
        and all(runtime.get("stonechartsVersion") == RELEASE for runtime in runtimes),
        "runtime bytes are identical": len(runtimes) == 2 and len({runtime.get("sha256") for runtime in runtimes}) == 1,
        "source path is repository-relative": bool(source)
        and not Path(source).is_absolute()
        and not PureWindowsPath(source).is_absolute(),
        "Go adapter path is portable": bool(go_binary)
        and not Path(go_binary).is_absolute()
        and not PureWindowsPath(go_binary).is_absolute(),
        "Go adapter is content-addressed": len(str(go_runtime.get("goBinarySha256", ""))) == 64,
    }
    failures = [label for label, passed in checks.items() if not passed]
    check = subprocess.run(
        [sys.executable, str(VERIFY), "--check-evidence", str(evidence), "--output-format", "json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if check.returncode != 0:
        failures.append(f"bundle self-check failed: {(check.stdout + check.stderr).strip()}")
    return failures


def generate(chart_ids: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="stonecharts-baselines-") as temporary:
        binary = Path(temporary) / ("stoneverify-go-render.exe" if os.name == "nt" else "stoneverify-go-render")
        build = subprocess.run(
            ["go", "build", "-o", str(binary), "./cmd/stoneverify-go-render"],
            cwd=ROOT / "libs" / "go",
            text=True,
            capture_output=True,
        )
        if build.returncode != 0:
            raise RuntimeError(f"Go adapter build failed:\n{build.stdout}{build.stderr}")

        environment = os.environ.copy()
        environment["STONEVERIFY_GENERATED_AT"] = GENERATED_AT
        for index, chart_id in enumerate(chart_ids, start=1):
            fixture = fixture_for(chart_id).relative_to(ROOT).as_posix()
            evidence = (Path("evidence-baselines") / chart_id).as_posix()
            process = subprocess.run(
                [
                    sys.executable,
                    str(VERIFY),
                    fixture,
                    "--runtime",
                    "python",
                    "--runtime",
                    "go",
                    "--go-binary",
                    str(binary),
                    "--profile",
                    "certified",
                    "--evidence",
                    evidence,
                    "--output-format",
                    "json",
                ],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
            )
            if process.returncode != 0:
                raise RuntimeError(f"{chart_id}: baseline generation failed:\n{process.stdout}{process.stderr}")
            print(f"[{index:02d}/{len(chart_ids)}] generated {chart_id} from {fixture}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true", help="Regenerate all baseline bundles")
    parser.add_argument("--check", action="store_true", help="Verify all committed baseline bundles")
    args = parser.parse_args()
    chart_ids = load_chart_ids()
    if len(chart_ids) != 36:
        print(f"expected 36 certified charts, found {len(chart_ids)}", file=sys.stderr)
        return 1

    if args.generate:
        generate(chart_ids)
    if args.check or not args.generate:
        failures: list[str] = []
        for chart_id in chart_ids:
            failures.extend(f"{chart_id}: {message}" for message in inspect_baseline(chart_id))
        if failures:
            print("certification baselines FAILED", file=sys.stderr)
            for failure in failures:
                print(f"- {failure}", file=sys.stderr)
            return 1
        print(f"certification baselines PASS: {len(chart_ids)} certified dual-runtime bundles at {RELEASE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
