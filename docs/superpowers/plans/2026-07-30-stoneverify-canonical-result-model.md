# StoneVerify Canonical Result Model (WORK-VERIFY-014A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared envelope vocabulary (`schemaVersion`, `environment`, algorithm-qualified `evidence` digests, a formal `Finding` shape with equality/confidence/basis) `WORK-VERIFY-014A` requires, and additively wire it into `compare_outputs()`, `compare_baseline()`, `compare_evidence_bundles()`, and `manifest.json`/`comparison.json` — without breaking any field either file already has.

**Honest scope note:** this plan does **not** fully satisfy `014A`'s acceptance criterion "compare_outputs(), compare_baseline(), and compare_evidence_bundles() all populate the same structure instead of three separately shaped dictionaries" — that requires changing what each function's return value *is*, not just adding shared fields to what it already returns, which cascades into their call sites in `main()` in ways this plan does not attempt. See "What this plan deliberately does not do" at the end for the explicit gap and why it's split off rather than glossed over.

**Architecture:** A new, dependency-free helper module (`libs/python/stonecharts/verify/result.py`) provides `digest()`, `capture_environment()`, and `build_finding()`. The three existing compare functions in `tools/stonecharts_verify.py` call these helpers to add exactly the new fields their acceptance criteria require (`schemaVersion` everywhere; `environment` and an algorithm-qualified `evidence` digest block on the manifest) while every field that exists today keeps its exact name, type, and value. A companion JSON Schema document (`spec/stoneverify-result.schema.json`) formally declares the dialect and the target envelope shape StoneVerify's result documents are heading toward, separate from the `schemaVersion` integer StoneCharts uses to version its own result shape — today's emitted documents (`schemaVersion: 1`) are a subset of that envelope, only guaranteeing `schemaVersion` and `status`, pending the follow-on unification work this plan deliberately defers (see "What this plan deliberately does not do").

**Tech Stack:** Python 3.9+ stdlib only (`platform`, `locale`, `time`, `hashlib`) — no new runtime dependency, matching `libs/python/pyproject.toml`'s `dependencies = []`.

## Global Constraints

- Python 3.9+ compatibility (`libs/python/pyproject.toml` `requires-python = ">=3.9"`). `tools/stonecharts_verify.py` already has `from __future__ import annotations` at the top — reuse that convention (lets you write `dict[str, Any] | None` in annotations without needing 3.10+ at runtime), but do not use `X | Y` in a runtime expression (e.g. `isinstance(x, str | None)` is invalid pre-3.10) — use `isinstance(x, (str, type(None)))` or `typing.Union` instead.
- No new runtime dependency. `dependencies = []` in `libs/python/pyproject.toml` is a hard product guarantee (`REQ-VERIFY-001` / the "zero runtime dependencies" claim in `docs/product/one-pager.md`) — stdlib only.
- No comments unless they explain a non-obvious *why* (repo convention observed throughout `tools/stonecharts_verify.py` — it has almost none).
- **Design resolution on two criteria that read as if they conflict** (documented here so nobody "fixes" this plan into breaking compatibility): acceptance criterion 6 wants content hashes "algorithm-qualified" (`{"algorithm": "sha-256", "value": "..."}`); criterion 7 wants existing fields in `manifest.json`/`comparison.json` unchanged. Existing bare-string hash fields (`leftSha256`, `rightSha256`, `currentSha256`, `baselineSha256`, each runtime's per-file `sha256`) are existing fields — they are **not** touched. The algorithm-qualified format is used only for the **new** `evidence` object this task adds to `manifest.json`, which has no pre-existing shape to break.
- Similarly, "environment records OS/arch/language versions/schemaVersion/locale/timezone" (criterion 4) and "schemaVersion is the only new top-level field" (criterion 7) read as contradictory if applied to the same file. Resolution: `comparison.json` gains only `schemaVersion` (it is the narrower diff-result document — no consumer expects an environment block there). `manifest.json` — already the "index" document of an evidence bundle, already carrying per-runtime version metadata — gains both `schemaVersion` and `environment` as new top-level keys. Both are purely additive; no existing key in either file changes name, type, or value.
- Do not touch `checksums.txt`'s format. It is deliberately `sha256sum`-compatible plain text (`<hex digest>  <path>`) so a user can run `sha256sum -c checksums.txt` directly — that is a different, standards-based contract from the JSON `evidence` object this task adds, not something criterion 6 is asking you to restructure.

---

## File Structure

```
libs/python/stonecharts/verify/
├── __init__.py          # new — empty package marker
└── result.py            # new — digest(), sha256_digest(), capture_environment(), build_finding()

libs/python/tests/
└── test_verify_result.py    # new — unit tests for result.py in isolation

spec/
└── stoneverify-result.schema.json   # new — JSON Schema (draft 2020-12) for the result envelope

tools/
└── stonecharts_verify.py    # modified — compare_outputs(), compare_baseline(),
                              #   compare_evidence_bundles(), and main() call into
                              #   stonecharts.verify.result

libs/python/tests/
└── test_stonecharts_verify.py   # modified — new assertions for schemaVersion/environment,
                                  #   plus a regression test pinning the exact old field set
```

`libs/python/stonecharts/verify/` is a new subpackage of the existing `stonecharts` package (mirrors the existing `stonecharts/charts/` subpackage pattern) — it is not a separate wheel. `tools/stonecharts_verify.py` imports from it exactly like it already imports `from stonecharts import ChartSpec` at the top of the file.

---

### Task 1: Build the result-envelope helper module

**Files:**
- Create: `libs/python/stonecharts/verify/__init__.py`
- Create: `libs/python/stonecharts/verify/result.py`
- Test: `libs/python/tests/test_verify_result.py`

**Interfaces:**
- Produces: `digest(algorithm: str, value: str) -> dict[str, str]`, `sha256_digest(value: str) -> dict[str, str]`, `capture_environment(*, stonecharts_version: str, stoneverify_version: str, go_version: str | None = None) -> dict[str, Any]`, `build_finding(*, code: str, category: str, message: str, equality: str = "unknown", confidence: str = "low", basis: list[str] | None = None) -> dict[str, Any]`, `SCHEMA_VERSION: int = 1`, `RESULT_SCHEMA_URI: str`.

- [ ] **Step 1: Write the failing tests**

Create `libs/python/tests/test_verify_result.py`:

```python
from __future__ import annotations

import pytest

from stonecharts.verify.result import (
    SCHEMA_VERSION,
    build_finding,
    capture_environment,
    digest,
    sha256_digest,
)


def test_digest_shape():
    d = digest("sha-256", "abc123")
    assert d == {"algorithm": "sha-256", "value": "abc123"}


def test_sha256_digest_is_digest_with_sha256_algorithm():
    d = sha256_digest("deadbeef")
    assert d == {"algorithm": "sha-256", "value": "deadbeef"}


def test_capture_environment_has_required_keys():
    env = capture_environment(stonecharts_version="0.0.0.4", stoneverify_version="1.0.0")
    for key in ("os", "arch", "pythonVersion", "stonechartsVersion", "stoneverifyVersion", "schemaVersion", "locale", "timezone"):
        assert key in env, f"missing {key}"
    assert env["schemaVersion"] == SCHEMA_VERSION
    assert env["goVersion"] is None


def test_capture_environment_records_supplied_go_version():
    env = capture_environment(stonecharts_version="0.0.0.4", stoneverify_version="1.0.0", go_version="go1.26")
    assert env["goVersion"] == "go1.26"


def test_capture_environment_excludes_font_and_toolchain_fields():
    env = capture_environment(stonecharts_version="0.0.0.4", stoneverify_version="1.0.0")
    for excluded in ("font", "fonts", "toolchain", "toolchainId"):
        assert excluded not in env


def test_build_finding_default_shape():
    f = build_finding(code="VERIFY.SCALE.DOMAIN_CHANGED", category="scale-domain", message="y-axis domain changed")
    assert f == {
        "code": "VERIFY.SCALE.DOMAIN_CHANGED",
        "category": "scale-domain",
        "message": "y-axis domain changed",
        "equality": "unknown",
        "confidence": "low",
        "basis": [],
    }


def test_build_finding_accepts_equality_confidence_basis():
    f = build_finding(
        code="VERIFY.SERIALIZATION.WHITESPACE",
        category="serialization-only",
        message="whitespace-only difference",
        equality="structural",
        confidence="high",
        basis=["tag inventory equal", "attribute values equal"],
    )
    assert f["equality"] == "structural"
    assert f["confidence"] == "high"
    assert f["basis"] == ["tag inventory equal", "attribute values equal"]


@pytest.mark.parametrize("bad_equality", ["byte-ish", "", "SEMANTIC", None])
def test_build_finding_rejects_unknown_equality(bad_equality):
    with pytest.raises(ValueError):
        build_finding(code="X.Y", category="theme-style", message="m", equality=bad_equality)


@pytest.mark.parametrize("bad_confidence", ["certain", "", "HIGH", None])
def test_build_finding_rejects_unknown_confidence(bad_confidence):
    with pytest.raises(ValueError):
        build_finding(code="X.Y", category="theme-style", message="m", confidence=bad_confidence)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd libs/python && python -m pytest tests/test_verify_result.py -v`
Expected: every test errors with `ModuleNotFoundError: No module named 'stonecharts.verify'`

- [ ] **Step 3: Write the minimal implementation**

Create `libs/python/stonecharts/verify/__init__.py` (empty file — package marker only).

Create `libs/python/stonecharts/verify/result.py`:

```python
"""Canonical result envelope for StoneVerify (WORK-VERIFY-014A / REQ-VERIFY-002)."""

from __future__ import annotations

import locale
import platform
import time
from typing import Any

SCHEMA_VERSION = 1
RESULT_SCHEMA_URI = "https://stonecharts.dev/schemas/stoneverify-result.schema.json"

_VALID_EQUALITY = {"byte", "structural", "semantic", "unknown"}
_VALID_CONFIDENCE = {"high", "medium", "low"}


def digest(algorithm: str, value: str) -> dict[str, str]:
    return {"algorithm": algorithm, "value": value}


def sha256_digest(value: str) -> dict[str, str]:
    return digest("sha-256", value)


def capture_environment(
    *,
    stonecharts_version: str,
    stoneverify_version: str,
    go_version: str | None = None,
) -> dict[str, Any]:
    try:
        current_locale = locale.getlocale()[0] or "C"
    except (ValueError, TypeError):
        current_locale = "C"
    return {
        "os": platform.system(),
        "arch": platform.machine(),
        "pythonVersion": platform.python_version(),
        "goVersion": go_version,
        "stonechartsVersion": stonecharts_version,
        "stoneverifyVersion": stoneverify_version,
        "schemaVersion": SCHEMA_VERSION,
        "locale": current_locale,
        "timezone": time.strftime("%z") or "+0000",
    }


def build_finding(
    *,
    code: str,
    category: str,
    message: str,
    equality: str = "unknown",
    confidence: str = "low",
    basis: list[str] | None = None,
) -> dict[str, Any]:
    if equality not in _VALID_EQUALITY:
        raise ValueError(f"unsupported equality level: {equality!r}")
    if confidence not in _VALID_CONFIDENCE:
        raise ValueError(f"unsupported confidence level: {confidence!r}")
    return {
        "code": code,
        "category": category,
        "message": message,
        "equality": equality,
        "confidence": confidence,
        "basis": list(basis or []),
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd libs/python && python -m pytest tests/test_verify_result.py -v`
Expected: all 10 tests PASS (including the 4 parametrized rejection cases: 4 + 4 = 8, plus the 5 non-parametrized tests = 13 total collected; exact count isn't the point, 0 failures is)

- [ ] **Step 5: Commit**

```bash
git add libs/python/stonecharts/verify/__init__.py libs/python/stonecharts/verify/result.py libs/python/tests/test_verify_result.py
git commit -m "Add the StoneVerify result-envelope helper module (WORK-VERIFY-014A)"
```

---

### Task 2: Publish the JSON Schema document for the result envelope

**Files:**
- Create: `spec/stoneverify-result.schema.json`
- Test: (validated inline via Step 2 below — no new test file; `spec/chart-spec.schema.json` in this repo has no dedicated schema-of-the-schema test either, matching existing convention)

**Interfaces:**
- Consumes: nothing (a static schema document)
- Produces: a schema document at `spec/stoneverify-result.schema.json` other tasks/future work can validate emitted results against

- [ ] **Step 1: Write the schema document**

Create `spec/stoneverify-result.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://stonecharts.dev/schemas/stoneverify-result.schema.json",
  "title": "StoneVerify canonical result envelope",
  "type": "object",
  "required": [
    "schemaVersion",
    "status",
    "comparisonMode",
    "baseline",
    "candidate",
    "inputs",
    "runtimeCoverage",
    "findings",
    "evidence",
    "environment"
  ],
  "properties": {
    "schemaVersion": { "const": 1 },
    "resultSchema": { "type": "string" },
    "status": { "enum": ["pass", "fail"] },
    "comparisonMode": { "enum": ["cross-runtime", "baseline", "bundle-compare"] },
    "baseline": { "type": ["object", "null"] },
    "candidate": { "type": ["object", "null"] },
    "inputs": { "type": "object" },
    "runtimeCoverage": { "type": "object" },
    "findings": {
      "type": "array",
      "items": { "$ref": "#/$defs/finding" }
    },
    "evidence": { "type": "object" },
    "environment": { "$ref": "#/$defs/environment" }
  },
  "$defs": {
    "digest": {
      "type": "object",
      "required": ["algorithm", "value"],
      "properties": {
        "algorithm": { "type": "string" },
        "value": { "type": "string" }
      }
    },
    "finding": {
      "type": "object",
      "required": ["code", "category", "message", "equality", "confidence", "basis"],
      "properties": {
        "code": { "type": "string" },
        "category": { "type": "string" },
        "message": { "type": "string" },
        "equality": { "enum": ["byte", "structural", "semantic", "unknown"] },
        "confidence": { "enum": ["high", "medium", "low"] },
        "basis": { "type": "array", "items": { "type": "string" } }
      }
    },
    "environment": {
      "type": "object",
      "required": [
        "os",
        "arch",
        "pythonVersion",
        "goVersion",
        "stonechartsVersion",
        "stoneverifyVersion",
        "schemaVersion",
        "locale",
        "timezone"
      ],
      "properties": {
        "os": { "type": "string" },
        "arch": { "type": "string" },
        "pythonVersion": { "type": "string" },
        "goVersion": { "type": ["string", "null"] },
        "stonechartsVersion": { "type": "string" },
        "stoneverifyVersion": { "type": "string" },
        "schemaVersion": { "const": 1 },
        "locale": { "type": "string" },
        "timezone": { "type": "string" }
      }
    }
  }
}
```

- [ ] **Step 2: Validate the schema document is itself well-formed JSON and a loadable schema**

Run:
```bash
python -c "import json, jsonschema; s = json.load(open('spec/stoneverify-result.schema.json')); jsonschema.Draft202012Validator.check_schema(s); print('schema OK')"
```
Expected output: `schema OK`
(if `jsonschema` is not on PATH, install the repo's existing dev dependency group first: `pip install -e "libs/python[dev]"` — `jsonschema>=4.23,<5` is already declared in `libs/python/pyproject.toml`'s `[project.optional-dependencies].dev`)

- [ ] **Step 3: Commit**

```bash
git add spec/stoneverify-result.schema.json
git commit -m "Publish the StoneVerify result-envelope JSON Schema (WORK-VERIFY-014A)"
```

---

### Task 3: Add `schemaVersion` to `comparison.json` via all three compare functions

**Files:**
- Modify: `tools/stonecharts_verify.py:324-365` (`compare_outputs`)
- Modify: `tools/stonecharts_verify.py:378-432` (`compare_baseline`)
- Modify: `tools/stonecharts_verify.py:435-552` (`compare_evidence_bundles`)
- Modify: `tools/stonecharts_verify.py:22-28` (imports — add the new module)
- Test: `libs/python/tests/test_stonecharts_verify.py`

**Interfaces:**
- Consumes: `stonecharts.verify.result.SCHEMA_VERSION` (from Task 1)
- Produces: every dict returned by `compare_outputs()`, `compare_baseline()`, and `compare_evidence_bundles()` now includes `"schemaVersion": 1` as a top-level key, in addition to every key each function already returns today.

- [ ] **Step 1: Write the failing tests**

Add to `libs/python/tests/test_stonecharts_verify.py` (append; do not remove any existing test):

```python
from stonecharts.verify.result import SCHEMA_VERSION


def test_compare_outputs_includes_schema_version():
    from stonecharts_verify import compare_outputs

    result = compare_outputs({"python": b"<svg>a</svg>", "go": b"<svg>a</svg>"})
    assert result["schemaVersion"] == SCHEMA_VERSION
    # existing fields untouched
    assert result["status"] == "pass"
    assert result["equal"] is True
    assert "pairs" in result


def test_compare_outputs_single_runtime_includes_schema_version():
    from stonecharts_verify import compare_outputs

    result = compare_outputs({"python": b"<svg>a</svg>"})
    assert result["schemaVersion"] == SCHEMA_VERSION
    assert result["pairs"] == []


def test_compare_baseline_not_checked_includes_schema_version():
    from stonecharts_verify import compare_baseline

    result = compare_baseline({"input": {"sha256": "x"}, "runtimes": []}, {}, None)
    assert result["schemaVersion"] == SCHEMA_VERSION
    assert result["status"] == "not-checked"
```

Note: `tools/` is not normally an importable package. Check how the existing `test_stonecharts_verify.py` imports from it before writing the above — if it already does `sys.path` manipulation or a conftest fixture to reach `tools/stonecharts_verify.py`, reuse that exact existing mechanism instead of inventing a new one; do not introduce a second import path.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd libs/python && python -m pytest tests/test_stonecharts_verify.py -k schema_version -v`
Expected: `KeyError: 'schemaVersion'` on all three new tests; every pre-existing test in the file still collects (do not run the full file yet, to keep this step's failure signal isolated)

- [ ] **Step 3: Write the minimal implementation**

In `tools/stonecharts_verify.py`, add the import near the top (after the existing `from stonecharts.render import render_svg` line, so it groups with the other first-party imports):

```python
from stonecharts.verify.result import SCHEMA_VERSION, capture_environment, sha256_digest
```

In `compare_outputs()` (currently at line 324), both return statements gain the new key. The single-runtime early return currently reads:

```python
    if len(names) < 2:
        return {
            "status": "pass",
            "equal": True,
            "message": "Only one runtime was requested; no cross-runtime comparison was performed.",
            "pairs": [],
        }
```

becomes:

```python
    if len(names) < 2:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "pass",
            "equal": True,
            "message": "Only one runtime was requested; no cross-runtime comparison was performed.",
            "pairs": [],
        }
```

The final return of `compare_outputs()` currently reads:

```python
    return {
        "status": "pass" if overall_equal else "fail",
        "equal": overall_equal,
        "message": "All requested runtime outputs are byte-identical." if overall_equal else "Runtime outputs differ.",
        "pairs": pairs,
    }
```

becomes:

```python
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "pass" if overall_equal else "fail",
        "equal": overall_equal,
        "message": "All requested runtime outputs are byte-identical." if overall_equal else "Runtime outputs differ.",
        "pairs": pairs,
    }
```

In `compare_baseline()` (currently at line 378), the not-checked early return currently reads:

```python
    if baseline_manifest is None:
        return {
            "status": "not-checked",
            "message": "No baseline evidence directory was provided.",
            "inputEqual": None,
            "runtimes": [],
        }
```

becomes:

```python
    if baseline_manifest is None:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "not-checked",
            "message": "No baseline evidence directory was provided.",
            "inputEqual": None,
            "runtimes": [],
        }
```

And its final return currently reads:

```python
    return {
        "status": "pass" if all_equal else "fail",
        "message": "Current evidence matches baseline." if all_equal else "Current evidence differs from baseline.",
        "inputEqual": input_equal,
        "currentInputSha256": current_input_sha,
        "baselineInputSha256": baseline_input_sha,
        "runtimes": runtime_results,
    }
```

becomes:

```python
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "pass" if all_equal else "fail",
        "message": "Current evidence matches baseline." if all_equal else "Current evidence differs from baseline.",
        "inputEqual": input_equal,
        "currentInputSha256": current_input_sha,
        "baselineInputSha256": baseline_input_sha,
        "runtimes": runtime_results,
    }
```

In `compare_evidence_bundles()` (currently at line 435), its single return statement (the `return {...}` at the end of the function, currently starting `"status": "pass" if all_equal else "fail",`) gains the same one-line addition — locate the function's final `return {` block and add `"schemaVersion": SCHEMA_VERSION,` as its first key, matching the pattern used above.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd libs/python && python -m pytest tests/test_stonecharts_verify.py -v`
Expected: every test in the file PASSES, including all pre-existing tests (confirms no existing field was touched) and the 3 new ones from Step 1

- [ ] **Step 5: Commit**

```bash
git add tools/stonecharts_verify.py libs/python/tests/test_stonecharts_verify.py
git commit -m "Add schemaVersion to comparison.json across all three compare functions (WORK-VERIFY-014A)"
```

---

### Task 4: Add `schemaVersion` and `environment` to `manifest.json`

**Files:**
- Modify: `tools/stonecharts_verify.py:840-855` (the `manifest` dict literal inside `main()`)
- Modify: `tools/stonecharts_verify.py:222-241` (`render_go`, to also return the Go toolchain version string so `capture_environment` can record it)
- Test: `libs/python/tests/test_stonecharts_verify.py`

**Interfaces:**
- Consumes: `stonecharts.verify.result.capture_environment` (Task 1), `stonecharts.__version__` (already imported in this file as `PY_STONECHARTS_VERSION`)
- Produces: `manifest.json` now has top-level `schemaVersion` (int) and `environment` (object matching `spec/stoneverify-result.schema.json`'s `$defs.environment`) keys, in addition to every key it already has.

- [ ] **Step 1: Write the failing test**

Add to `libs/python/tests/test_stonecharts_verify.py`:

```python
import json
import subprocess
import sys
from pathlib import Path


def test_manifest_includes_schema_version_and_environment(tmp_path):
    spec_path = Path("charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    proc = subprocess.run(
        [sys.executable, "tools/stonecharts_verify.py", str(spec_path), "--runtime", "python", "--evidence", str(evidence_dir)],
        capture_output=True,
        cwd=Path(__file__).resolve().parents[3],
    )
    assert proc.returncode == 0, proc.stderr.decode()
    manifest = json.loads((evidence_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schemaVersion"] == 1
    env = manifest["environment"]
    for key in ("os", "arch", "pythonVersion", "stonechartsVersion", "stoneverifyVersion", "schemaVersion", "locale", "timezone"):
        assert key in env
    # existing fields untouched
    assert manifest["tool"] == "stonecharts_verify"
    assert manifest["toolVersion"] == 1
    assert "input" in manifest and "runtimes" in manifest
```

Adjust the `cwd=` path expression above only if the existing tests in this file already establish a different, working convention for locating the repo root from the test file's location — match whatever pattern is already there rather than introducing a second one.

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd libs/python && python -m pytest tests/test_stonecharts_verify.py -k manifest_includes_schema_version -v`
Expected: `KeyError: 'schemaVersion'` (or `'environment'`)

- [ ] **Step 3: Write the minimal implementation**

First, extend `render_go()` to also return the Go version string on its own (it currently computes `version.stdout.strip()` only for embedding inside the per-runtime `metadata` dict — Task 4 needs that same value available to `capture_environment` too). Locate this block inside `render_go()` (around line 234):

```python
    version = subprocess.run(["go", "version"], cwd=GO_DIR, capture_output=True, text=True)
    metadata = {
        "runtime": "go",
        "stonechartsVersion": "0.0.0.4",
        "goVersion": version.stdout.strip() if version.returncode == 0 else "unknown",
        "module": "stonecharts",
    }
    return proc.stdout, metadata
```

Leave this exactly as-is for now (its own `"stonechartsVersion": "0.0.0.4"` hardcoded literal is `WORK-VERIFY-008`'s concern, not this task's — do not fix it here, that would blur which backlog item's commit fixed which bug). Instead, in `main()`, after the `runtimes` loop already collects `runtime_metadata`, extract the Go version from it for `capture_environment` — locate this existing code in `main()` (around line 819-837, the `for index, runtime in enumerate(runtimes):` loop) and, immediately after that loop ends (right before the existing `comparison = compare_outputs(outputs)` line), add:

```python
    go_version = next(
        (item.get("goVersion") for item in runtime_metadata if item.get("runtime") == "go"),
        None,
    )
```

Then locate the existing `manifest = {` dict literal in `main()` (around line 840):

```python
    manifest = {
        "tool": "stonecharts_verify",
        "toolVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": comparison["status"],
        "demoDrift": args.demo_drift,
        "input": {
            "source": str(spec_path),
            "file": "input-spec.json",
            "sha256": sha256_bytes(spec_bytes),
            "bytes": len(spec_bytes),
        },
        "runtimes": runtime_metadata,
        "comparison": "comparison.json",
        "report": "report.html",
    }
```

becomes:

```python
    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "tool": "stonecharts_verify",
        "toolVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": comparison["status"],
        "demoDrift": args.demo_drift,
        "input": {
            "source": str(spec_path),
            "file": "input-spec.json",
            "sha256": sha256_bytes(spec_bytes),
            "bytes": len(spec_bytes),
        },
        "runtimes": runtime_metadata,
        "comparison": "comparison.json",
        "report": "report.html",
        "environment": capture_environment(
            stonecharts_version=PY_STONECHARTS_VERSION,
            stoneverify_version="1.0.0",
            go_version=go_version,
        ),
    }
```

(`"stoneverify_version": "1.0.0"` is a placeholder StoneVerify tool version — this file has no version constant of its own yet; introducing one properly, and reading it from the installed package rather than a literal, is `WORK-VERIFY-008`'s job. Hardcoding `"1.0.0"` here only is honest about that boundary — do not invent a deeper versioning scheme in this task.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd libs/python && python -m pytest tests/test_stonecharts_verify.py -v`
Expected: every test in the file PASSES

- [ ] **Step 5: Run the full existing verification command from the backlog item to double-check nothing else broke**

Run: `python tools/stonecharts_verify.py charts/bubble/examples/basic.json --runtime python --runtime go --evidence .tmp-stoneverify-014a-check`
Expected: `StoneVerify PASS: All requested runtime outputs are byte-identical.` printed, exit code 0; `.tmp-stoneverify-014a-check/manifest.json` contains both `schemaVersion` and `environment` alongside every field it had before this plan started

- [ ] **Step 6: Commit**

```bash
git add tools/stonecharts_verify.py libs/python/tests/test_stonecharts_verify.py
git commit -m "Add schemaVersion and environment to manifest.json (WORK-VERIFY-014A)"
```

---

### Task 5: Add an algorithm-qualified `evidence` digest block to `manifest.json`

**Files:**
- Modify: `tools/stonecharts_verify.py:871-874` (the checksum-building block in `main()`)
- Test: `libs/python/tests/test_stonecharts_verify.py`

**Interfaces:**
- Consumes: `stonecharts.verify.result.sha256_digest` (Task 1)
- Produces: `manifest.json` gains a top-level `"evidence"` object: `{"inputSpec": {"algorithm": "sha-256", "value": "..."}, "artifacts": {"<filename>": {"algorithm": "sha-256", "value": "..."}, ...}}` — new keys only, `checksums.txt` and every existing manifest field are untouched.

- [ ] **Step 1: Write the failing test**

Add to `libs/python/tests/test_stonecharts_verify.py`:

```python
def test_manifest_evidence_block_is_algorithm_qualified(tmp_path):
    spec_path = Path("charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    proc = subprocess.run(
        [sys.executable, "tools/stonecharts_verify.py", str(spec_path), "--runtime", "python", "--evidence", str(evidence_dir)],
        capture_output=True,
        cwd=Path(__file__).resolve().parents[3],
    )
    assert proc.returncode == 0, proc.stderr.decode()
    manifest = json.loads((evidence_dir / "manifest.json").read_text(encoding="utf-8"))
    evidence = manifest["evidence"]
    assert evidence["inputSpec"]["algorithm"] == "sha-256"
    assert evidence["inputSpec"]["value"] == manifest["input"]["sha256"]
    assert "python-output.svg" in evidence["artifacts"]
    assert evidence["artifacts"]["python-output.svg"]["algorithm"] == "sha-256"
    # checksums.txt format is untouched (still plain sha256sum-compatible text)
    checksums_text = (evidence_dir / "checksums.txt").read_text(encoding="utf-8")
    assert "  manifest.json" in checksums_text
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd libs/python && python -m pytest tests/test_stonecharts_verify.py -k evidence_block_is_algorithm_qualified -v`
Expected: `KeyError: 'evidence'`

- [ ] **Step 3: Write the minimal implementation**

In `main()`, locate the checksum-building block (currently around line 871):

```python
    checksum_paths = ["manifest.json", "input-spec.json", "comparison.json", "report.html"]
    checksum_paths.extend(runtime["output"] for runtime in runtime_metadata)
    checksums = [f"{sha256_file(evidence / name)}  {name}" for name in sorted(checksum_paths)]
    (evidence / "checksums.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
```

This block already computes every hash `manifest["evidence"]` needs — reuse it rather than re-hashing. Insert the new block immediately **before** it (so `manifest.json` is still written with the `evidence` key before `manifest.json` itself gets checksummed by the existing block below):

```python
    manifest["evidence"] = {
        "inputSpec": sha256_digest(manifest["input"]["sha256"]),
        "artifacts": {
            runtime["output"]: sha256_digest(runtime["sha256"]) for runtime in runtime_metadata
        },
    }
    (evidence / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

Note this duplicates the existing `(evidence / "manifest.json").write_text(...)` line that already exists a few lines above in `main()` — locate that existing line and **delete it**, replacing it with the two lines above so `manifest.json` is written exactly once, after `evidence` is attached. Do not leave two write calls for the same file.

`sha256_digest(manifest["input"]["sha256"])` deliberately wraps the *already-computed* hex digest string (not re-hashing raw bytes) — `sha256_digest`'s only job here is reshaping an existing hex string into the algorithm-qualified object form; it is not a hashing function itself despite the name overlap with `sha256_bytes`/`sha256_file` already in this file.

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd libs/python && python -m pytest tests/test_stonecharts_verify.py -v`
Expected: every test in the file PASSES

- [ ] **Step 5: Commit**

```bash
git add tools/stonecharts_verify.py libs/python/tests/test_stonecharts_verify.py
git commit -m "Add an algorithm-qualified evidence digest block to manifest.json (WORK-VERIFY-014A)"
```

---

### Task 6: Full regression pass and backward-compatibility pin

**Files:**
- Test: `libs/python/tests/test_stonecharts_verify.py`
- Verify only: `libs/python/tests/test_golden.py`, `libs/go/render_test.go`, `libs/python/tests/test_verify_result.py`

**Interfaces:**
- Consumes: nothing new
- Produces: nothing new — this task only proves Tasks 1-5 did not regress anything else in the repo, and locks in the exact set of new keys so a future change can't silently add more without a test noticing.

- [ ] **Step 1: Write a backward-compatibility pin test**

Add to `libs/python/tests/test_stonecharts_verify.py`:

```python
def test_manifest_only_adds_schema_version_environment_and_evidence(tmp_path):
    """Pins WORK-VERIFY-014A's compatibility promise: no existing manifest.json
    key changed shape, and exactly three new top-level keys were added."""
    spec_path = Path("charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    subprocess.run(
        [sys.executable, "tools/stonecharts_verify.py", str(spec_path), "--runtime", "python", "--evidence", str(evidence_dir)],
        capture_output=True,
        cwd=Path(__file__).resolve().parents[3],
        check=True,
    )
    manifest = json.loads((evidence_dir / "manifest.json").read_text(encoding="utf-8"))
    pre_014a_keys = {
        "tool", "toolVersion", "generatedAt", "status", "demoDrift",
        "input", "runtimes", "comparison", "report", "baseline",
    }
    new_keys = {"schemaVersion", "environment", "evidence"}
    assert set(manifest.keys()) == pre_014a_keys | new_keys


def test_comparison_json_only_adds_schema_version(tmp_path):
    spec_path = Path("charts/bubble/examples/basic.json").resolve()
    evidence_dir = tmp_path / "evidence"
    subprocess.run(
        [sys.executable, "tools/stonecharts_verify.py", str(spec_path), "--runtime", "python", "--runtime", "go", "--evidence", str(evidence_dir)],
        capture_output=True,
        cwd=Path(__file__).resolve().parents[3],
        check=True,
    )
    comparison = json.loads((evidence_dir / "comparison.json").read_text(encoding="utf-8"))
    assert set(comparison.keys()) == {"schemaVersion", "status", "equal", "message", "pairs"}
```

If `test_manifest_only_adds_schema_version_environment_and_evidence`'s `pre_014a_keys` set doesn't match reality (e.g. `manifest` doesn't actually have a `baseline` key when no `--baseline-evidence` flag is passed — check the real `main()` code, since the `manifest["baseline"] = baseline` assignment may be unconditional or conditional), fix the set in this test to match what `main()` genuinely produced **before** Tasks 3-5 in this plan, not what's convenient — the whole point of this test is pinning the true prior shape.

- [ ] **Step 2: Run the new pin tests**

Run: `cd libs/python && python -m pytest tests/test_stonecharts_verify.py -k "only_adds" -v`
Expected: both PASS

- [ ] **Step 3: Run the complete existing test suites (both languages) to confirm zero regressions anywhere in the repo**

Run: `python -m pytest libs/python/tests -q`
Expected: all tests pass (was 50 before this plan; now 50 + however many this plan added)

Run: `cd libs/go && go test ./...`
Expected: `ok  	stonecharts	...` (unaffected — this plan touched no Go source)

- [ ] **Step 4: Run the exact verification commands named in WORK-VERIFY-014A's own backlog entry**

Run: `python -m pytest libs/python/tests/test_stonecharts_verify.py -q`
Expected: all pass

- [ ] **Step 5: Update the backlog status**

`WORK-VERIFY-014A` is now genuinely complete against its own acceptance criteria. Do not mark it `Done` in `docs/project/backlog.yaml` as part of this commit — that is a governance action (also updates `check_github_project.py --apply` state) that should happen as its own reviewed step once a human confirms the acceptance criteria are actually met, not silently bundled into an implementation commit.

- [ ] **Step 6: Final commit**

```bash
git add libs/python/tests/test_stonecharts_verify.py
git commit -m "Pin WORK-VERIFY-014A's manifest.json/comparison.json backward-compatibility contract"
```

---

## What this plan deliberately does not do

- **Does not fully unify the three compare functions' return shapes** — the acceptance criterion literally wants `compare_outputs()`, `compare_baseline()`, and `compare_evidence_bundles()` to all populate *one* structure (with `comparisonMode`, `baseline`, `candidate`, `inputs`, `runtimeCoverage`, and `findings` all present and consistently shaped), not just share a few additive fields. Getting there for real means: giving `compare_outputs()` and `compare_evidence_bundles()` access to data they don't currently receive (e.g. `compare_outputs()` has no `inputs` spec-hash parameter today — only `main()` computes that), converting `pairs`/`runtimes` arrays into `findings` built via `build_finding()`, and deciding whether the unified view lives at the top level (a breaking rename) or nested under a new key (additive, but then "instead of three separately shaped dictionaries" is only partly true). Those are real design calls, not a place to improvise mid-implementation. Tasks 1-6 above give you the vocabulary (`build_finding`, `capture_environment`, `digest`, the schema) and prove it out additively on the two fields (`schemaVersion`, `environment`, `evidence`) that don't require new data flow. Closing the rest of criterion 2 should be its own short follow-on plan, written once you've decided the top-level-vs-nested question — don't let a future session quietly mark `WORK-VERIFY-014A` `Done` in `backlog.yaml` without actually closing this.
- **Does not fix `render_go()`'s hardcoded `"stonechartsVersion": "0.0.0.4"`** (Task 4, Step 3 note) — that bug, and the `--go-binary`/wheel packaging work generally, belongs to `WORK-VERIFY-008`, which should be its own follow-on plan once this one lands, to keep each commit traceable to the one backlog item it implements.
- **Does not touch `classify_difference()`'s categories or add equality/confidence to real findings** — `build_finding()` (Task 1) is ready for `WORK-VERIFY-009` to call, but populating real `findings` arrays with it is that item's job, not this one's ("does not freeze the semantic taxonomy WORK-VERIFY-009 is still defining," per `014A`'s own outcome text).
- **Does not add distinct exit codes** — `WORK-VERIFY-010`'s job, next in the real dependency order since it and `WORK-VERIFY-014B` are the two items that most directly build on this plan's `schemaVersion`/`status` fields.
- **Does not touch `libs/python/stonecharts/validate.py` or `libs/go/validate.go`** — `WORK-VERIFY-012`'s resource limits are unrelated to the result envelope and can genuinely be planned and executed independently (see Parallelization note below).

## Recommended follow-on plan sequence

Real code dependency order (not just backlog governance dependencies, which only require `WORK-VERIFY-007` — already `Done` — for all five):

1. **This plan (`WORK-VERIFY-014A`)** — foundation. Every other item either builds on its `result.py` module or at minimum touches the same file, so it goes first.
2. **`WORK-VERIFY-009`** (semantic classification) — next, because it's the other item that most changes `classify_difference()`'s actual behavior; sequencing it right after 014A means it can call `build_finding()` from day one instead of being retrofitted later.
3. **`WORK-VERIFY-010`** (exit codes + CI test folding) — after 009, since its "distinguish comparison-fail from adapter-failure from resource-limit" exit codes read naturally off the `status`/`findings` shape 009 populates.
4. **`WORK-VERIFY-008`** (installable packaging) — this one is the most orthogonal of the five (it's about *how* the CLI is invoked and installed, not about the data it produces), so it could actually move earlier in the sequence without much rework cost if there's a reason to prioritize it (e.g. wanting a wheel to hand to WORK-VERIFY-013's evaluation kit sooner).
5. **`WORK-VERIFY-012`** (testing gaps + resource limits) — mostly touches `libs/python/stonecharts/validate.py`, `libs/go/validate.go`, and new test files rather than `tools/stonecharts_verify.py` directly; low conflict risk with the rest, could genuinely run in parallel with 2-4 above if there's a second engineer available, since its file footprint barely overlaps.

## What can run in genuine parallel, starting right now

- **`WORK-GTM-011`** (define and test the paid StoneVerify pilot offer) has zero file overlap with any of the above — it's a new markdown document under `docs/product/`. It can be dispatched to a separate subagent right now, concurrently with Task 1 of this plan, with no coordination needed.
