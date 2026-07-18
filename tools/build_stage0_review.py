#!/usr/bin/env python3
"""Build a Stage 0 baseline review package from the governed repo state."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".agents" / "state"
REVIEW_PATH = STATE_DIR / "stage-0-review.md"


def run(command: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def git(*args: str) -> str:
    code, output = run(["git", *args])
    if code:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{output}")
    return output


def extract_open_decisions() -> list[str]:
    lines = (ROOT / "docs" / "project" / "decisions.md").read_text(encoding="utf-8").splitlines()
    in_open = False
    rows: list[str] = []
    for line in lines:
        if line.startswith("## Open decisions"):
            in_open = True
            continue
        if in_open and line.startswith("## Discussion order"):
            break
        if in_open and line.startswith("| ") and "Priority" not in line and "---" not in line:
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) >= 5:
                rows.append(f"- {parts[1]}: {parts[2]} -> {parts[3]} (decide before {parts[4]})")
    return rows


def extract_open_risks() -> list[str]:
    data = yaml.safe_load((ROOT / "docs" / "governance" / "risk-register.yaml").read_text(encoding="utf-8"))
    rows: list[str] = []
    for risk in data["risks"]:
        if risk["status"] in {"open", "mitigating"}:
            rows.append(f"- {risk['id']} ({risk['status']}): {risk['title']} -> {risk['mitigation']}")
    return rows


def extract_blockers() -> list[str]:
    backlog = yaml.safe_load((ROOT / "docs" / "project" / "backlog.yaml").read_text(encoding="utf-8"))
    items = {item["id"]: item for item in backlog["items"]}
    blockers: list[str] = []
    for item_id in ["WORK-S0-001", "GATE-S0"]:
        item = items[item_id]
        blockers.append(
            f"- {item_id} ({item['status']}): {item['title']} -> depends on {', '.join(item['dependencies']) or 'none'}"
        )
    return blockers


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    commit = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    status = git("status", "--short")
    docs_code, docs_output = run(["python", "tools/check_docs.py"])
    project_code, project_output = run(["python", "tools/check_github_project.py"])

    lines: list[str] = [
        "# Stage 0 Baseline Review Package",
        "",
        f"- Generated at: {generated_at}",
        f"- Commit: {commit}",
        f"- Branch: {branch}",
        f"- Working tree: {'clean' if not status else 'dirty'}",
        "",
        "## Working tree status",
        "",
        status or "Clean.",
        "",
        "## Verification",
        "",
        f"- `python tools/check_docs.py`: {'PASS' if docs_code == 0 else 'FAIL'}",
        "",
        "```",
        docs_output,
        "```",
        "",
        f"- `python tools/check_github_project.py`: {'PASS' if project_code == 0 else 'FAIL'}",
        "",
        "```",
        project_output,
        "```",
        "",
        "## Open decisions",
        "",
        *extract_open_decisions(),
        "",
        "## Open risks",
        "",
        *extract_open_risks(),
        "",
        "## Stage 0 blockers",
        "",
        *extract_blockers(),
        "",
        "## Review note",
        "",
        "Stage 0 is not yet ready to close because WORK-S0-001 and GATE-S0 remain open.",
    ]

    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(REVIEW_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
