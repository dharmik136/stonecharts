#!/usr/bin/env python3
"""Build a self-contained internal StoneVerify evaluation kit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "dist" / "stoneverify-evaluation-kit"


def read_package_version() -> str:
    """Read the current StoneCharts version without adding a TOML dependency."""
    pyproject = ROOT / "libs" / "python" / "pyproject.toml"
    in_project = False
    for raw_line in pyproject.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            in_project = line == "[project]"
            continue
        if in_project and line.startswith("version"):
            key, separator, value = line.partition("=")
            if separator and key.strip() == "version":
                version = value.strip().strip('"')
                if version:
                    return version
    raise RuntimeError(f"unable to read [project].version from {pyproject}")


KIT_VERSION = read_package_version()
RELEASE_EVIDENCE = ROOT / "docs" / "releases" / KIT_VERSION / "evidence" / "rc.1"


def run(args: list[str], *, cwd: Path = ROOT) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_clean_dir(path: Path) -> None:
    resolved = path.resolve()
    dist_root = (ROOT / "dist").resolve()
    if resolved != dist_root and dist_root not in resolved.parents:
        raise ValueError(f"refusing to remove output outside dist/: {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def build_python_wheel(packages_dir: Path) -> Path:
    qualified_wheels = sorted((RELEASE_EVIDENCE / "packages").glob(f"stonecharts-{KIT_VERSION}-*.whl"))
    if len(qualified_wheels) > 1:
        raise RuntimeError(f"expected at most one qualified StoneCharts wheel, found {qualified_wheels}")
    if qualified_wheels:
        destination = packages_dir / qualified_wheels[0].name
        copy_file(qualified_wheels[0], destination)
        return destination

    run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(packages_dir),
            str(ROOT / "libs" / "python"),
        ]
    )
    wheels = sorted(packages_dir.glob("stonecharts-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected exactly one stonecharts wheel, found {wheels}")
    return wheels[0]


def assert_go_source_matches_release() -> None:
    if not RELEASE_EVIDENCE.exists():
        return
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            KIT_VERSION,
            "--",
            "libs/go",
            "runtime",
            "spec",
        ],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Go adapter inputs differ from qualified release tag {KIT_VERSION}; "
            "build the pilot kit from the qualified source"
        )


def build_go_adapter(bin_dir: Path) -> Path:
    assert_go_source_matches_release()
    exe = "stoneverify-go-render.exe" if os.name == "nt" else "stoneverify-go-render"
    output = bin_dir / exe
    output.parent.mkdir(parents=True, exist_ok=True)
    run(["go", "build", "-o", str(output), "./cmd/stoneverify-go-render"], cwd=ROOT / "libs" / "go")
    return output


def write_kit_readme(kit: Path, wheel: Path, adapter: Path) -> None:
    write_text(
        kit / "README.md",
        f"""\
        # StoneVerify Evaluation Kit

        Version: `{KIT_VERSION}`

        **Internal/build-only artifact.** This kit is for internal review of the
        StoneVerify pilot workflow. It does not authorize external distribution,
        a paid pilot, or commercial terms; DEC-018 and SC-CON-020 still govern
        those decisions separately.

        ## Contents

        - `packages/{wheel.name}`: built StoneCharts Python wheel containing the
          `stoneverify` console script.
        - `bin/{adapter.name}`: prebuilt Go renderer adapter used by
          `stoneverify --runtime go`.
        - `sample-specs/bubble-basic.json`: small certified demo fixture.
        - `schemas/`: chart-spec and StoneVerify result schemas.
        - `docs/`: quickstart, limits, capability, robustness, security, and
          supply-chain notes copied from the governed repository docs.
        - `release-evidence/`: the qualified release manifest, hashes, SBOM,
          provenance, package-install matrix, and qualification checklist.
        - `LICENSE`, `SUPPORT.md`, and `SECURITY.md`: the active proprietary,
          support, and vulnerability-reporting boundaries.
        - `scripts/run_demo.py`: installs from the local wheel only and runs a
          deliberate demo-drift proof.

        ## Run The Demo

        From the extracted kit directory:

        ```bash
        python scripts/run_demo.py
        ```

        The script creates a local `.demo-venv`, installs StoneCharts from
        `packages/` with `--no-index`, points `STONEVERIFY_GO_BINARY` at `bin/`,
        and runs:

        ```bash
        stoneverify sample-specs/bubble-basic.json \\
          --runtime python --runtime go \\
          --demo-drift text \\
          --evidence demo-output/drift
        ```

        The expected command exit is `1` because the drift is intentional. A
        successful demo means StoneVerify produced a reviewable failing evidence
        bundle using only the packaged kit artifacts.

        To prove the kit against a fixture outside the repository examples, pass
        a separate spec path:

        ```bash
        python scripts/run_demo.py --spec /path/to/external-fixture.json
        ```

        ## Known Limits And Environments

        Do not restate limits from this README. Use:

        - `docs/guarantees-and-limits.md`
        - `docs/robustness.md`
        - `docs/stoneverify-quickstart.md`

        ## No Network Requirement

        The demo install uses `pip install --no-index --find-links packages`, so
        Python package installation does not contact package indexes. StoneVerify
        itself renders locally and does not send chart data anywhere.
        """,
    )


def write_demo_runner(kit: Path) -> None:
    runner = """\
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import os
        import shutil
        import subprocess
        import sys
        from pathlib import Path


        ROOT = Path(__file__).resolve().parents[1]
        VENV = ROOT / ".demo-venv"
        OUTPUT = ROOT / "demo-output" / "drift"


        def run(args: list[str], *, expected: int = 0) -> None:
            completed = subprocess.run(args, cwd=ROOT, env=os.environ.copy())
            if completed.returncode != expected:
                raise SystemExit(f"{args!r} exited {completed.returncode}, expected {expected}")


        def main() -> int:
            parser = argparse.ArgumentParser(description="Run the StoneVerify evaluation-kit demo.")
            parser.add_argument(
                "--spec",
                type=Path,
                default=ROOT / "sample-specs" / "bubble-basic.json",
                help="Chart spec to verify. Defaults to the included sample spec.",
            )
            args = parser.parse_args()
            spec_path = args.spec.resolve()
            if not spec_path.exists():
                raise SystemExit(f"spec does not exist: {spec_path}")

            if VENV.exists():
                shutil.rmtree(VENV)
            if OUTPUT.parent.exists():
                shutil.rmtree(OUTPUT.parent)
            run([sys.executable, "-m", "venv", str(VENV)])

            if os.name == "nt":
                python = VENV / "Scripts" / "python.exe"
                stoneverify = VENV / "Scripts" / "stoneverify.exe"
                adapter = ROOT / "bin" / "stoneverify-go-render.exe"
            else:
                python = VENV / "bin" / "python"
                stoneverify = VENV / "bin" / "stoneverify"
                adapter = ROOT / "bin" / "stoneverify-go-render"

            run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--find-links",
                    str(ROOT / "packages"),
                    "stonecharts==__STONECHARTS_VERSION__",
                ]
            )

            env = os.environ.copy()
            env["STONEVERIFY_GO_BINARY"] = str(adapter)
            completed = subprocess.run(
                [
                    str(stoneverify),
                    str(spec_path),
                    "--runtime",
                    "python",
                    "--runtime",
                    "go",
                    "--demo-drift",
                    "text",
                    "--evidence",
                    str(OUTPUT),
                ],
                cwd=ROOT,
                env=env,
            )
            if completed.returncode != 1:
                raise SystemExit(f"demo drift exited {completed.returncode}, expected 1")

            required = [
                OUTPUT / "manifest.json",
                OUTPUT / "comparison.json",
                OUTPUT / "report.html",
                OUTPUT / "checksums.txt",
                OUTPUT / "python-output.svg",
                OUTPUT / "go-output.svg",
            ]
            missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
            if missing:
                raise SystemExit("demo output missing: " + ", ".join(missing))
            print("StoneVerify evaluation-kit demo PASS: intentional drift produced reviewable evidence.")
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        """
    write_text(
        kit / "scripts" / "run_demo.py",
        runner.replace("__STONECHARTS_VERSION__", KIT_VERSION),
    )


def copy_go_adapter_docs(kit: Path) -> None:
    write_text(
        kit / "bin" / "README.md",
        """\
        # Go Adapter

        `stoneverify-go-render` is the prebuilt adapter used by StoneVerify for
        `--runtime go`. StoneVerify resolves it from `--go-binary`,
        `STONEVERIFY_GO_BINARY`, or `PATH`.

        Contract:

        ```bash
        stoneverify-go-render <spec.json>
        stoneverify-go-render --version
        ```
        """,
    )


def write_manifest(kit: Path, files: list[Path]) -> None:
    payload = {
        "kit": "stoneverify-evaluation-kit",
        "version": KIT_VERSION,
        "status": "internal-build-only",
        "distributionAuthorized": False,
        "files": [
            {
                "path": str(path.relative_to(kit)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(files)
            if path.is_file()
        ],
    }
    write_text(kit / "manifest.json", json.dumps(payload, indent=2, sort_keys=True) + "\n")


def assert_clean_kit(kit: Path) -> None:
    forbidden_names = {"__pycache__", "build"}
    forbidden_suffixes = {".egg-info"}
    offenders: list[str] = []
    for path in kit.rglob("*"):
        rel = str(path.relative_to(kit)).replace("\\", "/")
        if any(part in forbidden_names for part in path.parts):
            offenders.append(rel)
        if any(part.endswith(suffix) for part in path.parts for suffix in forbidden_suffixes):
            offenders.append(rel)
        if path.name.endswith(".pyc"):
            offenders.append(rel)
    if offenders:
        raise RuntimeError("kit contains forbidden build/cache artifacts: " + ", ".join(sorted(offenders)))


def make_archive(kit: Path) -> Path:
    archive = kit.with_suffix(".zip")
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(kit.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(kit.parent))
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output kit directory under dist/")
    parser.add_argument("--no-archive", action="store_true", help="Skip writing the .zip archive")
    args = parser.parse_args()

    kit = args.out.resolve()
    ensure_clean_dir(kit)

    packages_dir = kit / "packages"
    bin_dir = kit / "bin"
    wheel = build_python_wheel(packages_dir)
    adapter = build_go_adapter(bin_dir)

    copy_file(ROOT / "charts" / "bubble" / "examples" / "basic.json", kit / "sample-specs" / "bubble-basic.json")
    copy_file(ROOT / "spec" / "chart-spec.schema.json", kit / "schemas" / "chart-spec.schema.json")
    copy_file(ROOT / "spec" / "stoneverify-result.schema.json", kit / "schemas" / "stoneverify-result.schema.json")
    copy_file(ROOT / "docs" / "quality" / "stoneverify-quickstart.md", kit / "docs" / "stoneverify-quickstart.md")
    copy_file(ROOT / "docs" / "contracts" / "guarantees-and-limits.md", kit / "docs" / "guarantees-and-limits.md")
    copy_file(ROOT / "docs" / "robustness.md", kit / "docs" / "robustness.md")
    copy_file(ROOT / "docs" / "security" / "threat-model.md", kit / "docs" / "threat-model.md")
    copy_file(ROOT / "docs" / "security" / "supply-chain.md", kit / "docs" / "supply-chain.md")
    copy_file(ROOT / "docs" / "product" / "capability-matrix.md", kit / "docs" / "capability-matrix.md")
    copy_file(ROOT / "LICENSE", kit / "LICENSE")
    copy_file(ROOT / "SUPPORT.md", kit / "SUPPORT.md")
    copy_file(ROOT / "SECURITY.md", kit / "SECURITY.md")

    if RELEASE_EVIDENCE.exists():
        for name in (
            "hashes.sha256",
            "manifest.json",
            "package-install-matrix.md",
            "provenance.json",
            "qualification-checklist.md",
            "sbom.spdx.json",
        ):
            copy_file(RELEASE_EVIDENCE / name, kit / "release-evidence" / name)

    write_kit_readme(kit, wheel, adapter)
    write_demo_runner(kit)
    copy_go_adapter_docs(kit)

    files = [path for path in kit.rglob("*") if path.is_file()]
    write_manifest(kit, files)
    assert_clean_kit(kit)
    archive = None if args.no_archive else make_archive(kit)

    print(f"StoneVerify evaluation kit: {kit}")
    if archive:
        print(f"archive: {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
