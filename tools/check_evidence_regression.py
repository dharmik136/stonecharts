#!/usr/bin/env python3
"""Generate and validate evidence for every certified chart example.

The certified chart registry is the source of truth. Any missing chart directory,
missing example, render failure, or evidence-validation failure makes this check fail.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "tools" / "stonecharts_verify.py"
EXPECTED_CERTIFIED_CHARTS = 36


class EvidenceRegressionError(RuntimeError):
    """Raised when the certification portfolio cannot be checked completely."""


def discover_certified_examples(root: Path = ROOT) -> list[tuple[str, Path]]:
    """Return every example for every certified chart, failing on coverage gaps."""
    registry = json.loads((root / "spec" / "capabilities.json").read_text(encoding="utf-8"))
    certified_ids = [item["id"] for item in registry["chartTypes"] if item.get("tier") == "certified"]
    if len(certified_ids) != EXPECTED_CERTIFIED_CHARTS:
        raise EvidenceRegressionError(
            f"expected {EXPECTED_CERTIFIED_CHARTS} certified chart types, found {len(certified_ids)}"
        )
    if len(certified_ids) != len(set(certified_ids)):
        raise EvidenceRegressionError("capability registry contains duplicate certified chart IDs")

    expected_directories = {"line-basic" if chart_id == "line" else chart_id for chart_id in certified_ids}
    actual_directories = {
        path.name for path in (root / "charts").iterdir() if path.is_dir() and path.name != "_cartesian"
    }
    missing_directories = sorted(expected_directories - actual_directories)
    unexpected_directories = sorted(actual_directories - expected_directories)
    if missing_directories or unexpected_directories:
        details = []
        if missing_directories:
            details.append("missing chart directories: " + ", ".join(missing_directories))
        if unexpected_directories:
            details.append("unregistered chart directories: " + ", ".join(unexpected_directories))
        raise EvidenceRegressionError("; ".join(details))

    examples: list[tuple[str, Path]] = []
    for chart_id in certified_ids:
        directory = "line-basic" if chart_id == "line" else chart_id
        chart_examples = sorted((root / "charts" / directory / "examples").glob("*.json"))
        if not chart_examples:
            raise EvidenceRegressionError(f"certified chart {chart_id!r} has no JSON examples")
        examples.extend((chart_id, example) for example in chart_examples)
    return examples


def run_required(command: list[str], *, label: str) -> subprocess.CompletedProcess[str]:
    """Run a command and turn every non-zero result into a concise hard failure."""
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        output = (result.stdout + result.stderr).strip()
        raise EvidenceRegressionError(
            f"{label} failed with exit code {result.returncode}" + (f":\n{output}" if output else "")
        )
    return result


def qualify_examples(examples: list[tuple[str, Path]], output_root: Path) -> list[Path]:
    """Render and independently validate each example's evidence bundle."""
    bundles: list[Path] = []
    for chart_id, example in examples:
        bundle = output_root / chart_id / example.stem
        relative_example = example.relative_to(ROOT)
        run_required(
            [
                sys.executable,
                str(VERIFY),
                str(relative_example),
                "--runtime",
                "python",
                "--profile",
                "certified",
                "--evidence",
                str(bundle),
            ],
            label=f"render {chart_id}/{example.name}",
        )
        if not bundle.is_dir():
            raise EvidenceRegressionError(
                f"render {chart_id}/{example.name} returned success without creating evidence"
            )
        run_required(
            [sys.executable, str(VERIFY), "--check-evidence", str(bundle)],
            label=f"validate {chart_id}/{example.name}",
        )
        bundles.append(bundle)
        print(f"PASS {chart_id}/{example.name}")
    return bundles


def prove_fail_closed(bundle: Path) -> None:
    """Corrupt a copied bundle and require the validator to reject it."""
    with tempfile.TemporaryDirectory(prefix="stonecharts-evidence-corrupt-") as temporary:
        corrupted = Path(temporary) / "evidence"
        shutil.copytree(bundle, corrupted)
        output = corrupted / "python-output.svg"
        output.write_bytes(output.read_bytes() + b"\n<!-- intentional CI corruption -->\n")
        result = subprocess.run(
            [sys.executable, str(VERIFY), "--check-evidence", str(corrupted)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            raise EvidenceRegressionError("corrupted evidence unexpectedly passed validation")
    print("PASS fail-closed corruption proof")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        help="Keep generated bundles below this path instead of using a temporary directory.",
    )
    parser.add_argument(
        "--prove-fail-closed",
        action="store_true",
        help="Corrupt a copied bundle and require evidence validation to reject it.",
    )
    args = parser.parse_args()

    try:
        examples = discover_certified_examples()
        chart_count = len({chart_id for chart_id, _ in examples})
        if args.output_root:
            output_root = args.output_root.resolve()
            output_root.mkdir(parents=True, exist_ok=True)
            bundles = qualify_examples(examples, output_root)
        else:
            with tempfile.TemporaryDirectory(prefix="stonecharts-evidence-regression-") as temporary:
                bundles = qualify_examples(examples, Path(temporary))
                if args.prove_fail_closed:
                    prove_fail_closed(bundles[0])
        if args.output_root and args.prove_fail_closed:
            prove_fail_closed(bundles[0])
    except (EvidenceRegressionError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"evidence regression FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"evidence regression PASS: {chart_count} charts, {len(examples)} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
