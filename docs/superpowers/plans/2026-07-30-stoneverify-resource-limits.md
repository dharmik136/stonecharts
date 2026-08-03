# StoneVerify/Renderer Resource Limits and Unicode Safety (WORK-VERIFY-012, partial) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give both renderers concrete, identical, documented resource limits (max series, max points, max spec size, max label length, max generated SVG size, render timeout) with a stable machine-readable error code naming which limit was exceeded — plus prove Unicode/escaping safety in labels, titles, and tooltips.

**Honest scope note:** `WORK-VERIFY-012`'s full acceptance criteria also require randomized property tests across all 6 certified chart types in both languages, cross-language invalid-input parity for every documented error class in `docs/contracts/validation-and-capabilities.md`, and an enforced CI coverage threshold. This plan does **not** cover those three — they are extensive but structurally repetitive once this plan's patterns exist (a property test per chart type is the same shape 6 times; a parity test per error class is the same shape once per documented class), and are better suited to their own plan, and possibly genuine parallel per-chart-type dispatch once this plan's shared helpers exist. See "What this plan deliberately does not do."

**Architecture:** A new module `libs/python/stonecharts/limits.py` defines the limit constants and a `check_resource_limits(spec_dict: dict) -> list[str]` function returning `"LIMIT.<NAME>: <message>"`-prefixed strings (a stable machine-parseable prefix on an otherwise-human string — no new exception type, no change to `SpecError`'s existing shape). `ChartSpec.from_dict()` calls it alongside the existing `validate()` call and merges any limit violations into the same `SpecError` it already raises, so callers get one consistent error path. The Go side gets an equivalent `limits.go` with the same constants and the same `"LIMIT.<NAME>: ..."` prefix convention, called from the same validation entry point Go already uses.

**Tech Stack:** Python 3.9+ stdlib only, Go stdlib only. No new dependency in either language.

## Global Constraints

- Python 3.9+ compatibility, no new runtime dependency (stdlib only: no `resource`/`signal`-based timeout library beyond what's already used, if anything — check `tools/stonecharts_verify.py` and `libs/python/stonecharts/render.py` for any existing timeout mechanism before inventing one).
- No comments unless they explain a non-obvious *why*.
- Limit values must be **identical** between Python and Go — define them once in prose here, implement them as the same literal constants in both languages' new `limits.py`/`limits.go` files. Do not let either language's implementation invent its own numbers.
- Limit violations are reported as validation errors (same path as existing `validate()` failures, i.e. `SpecError`/its Go equivalent) — they are not a new kind of failure requiring new plumbing through `main()`'s exit-code logic beyond what `WORK-VERIFY-010` already establishes for "invalid or unsupported specification."
- Do not change any currently-valid specification's rendered output. Every existing example/golden fixture in `charts/*/examples/` and `charts/*/golden/` must stay within every new limit (verify this in Task 1's tests) — if any existing fixture would exceed a limit as initially chosen, raise the limit rather than breaking a certified example.

## Chosen Limit Values (defined once, implemented twice)

| Limit | Value | Rationale |
|---|---:|---|
| Max series per chart | 50 | Generous multiple of the largest existing example (`charts/*/examples/*.json` — verify in Task 1 none exceeds ~10 series) |
| Max points per series | 10,000 | A dense single-series line chart; well beyond any shipped example |
| Max total points (all series combined) | 50,000 | Product of the above two, capped independently so many-series-many-points can't multiply unbounded |
| Max input specification size (bytes) | 5,000,000 (5 MB) | A JSON spec this large is almost certainly malformed or adversarial, not a real chart |
| Max label length (title, subtitle, axis titles, series names, category labels) | 500 characters | Generous for any real chart label; guards against a single absurd string bloating the SVG |
| Max generated SVG size (bytes) | 20,000,000 (20 MB) | An order of magnitude above any realistic certified chart's output |
| Render timeout | 10 seconds | Generous margin above the ~0.07-0.16s cold-render figures already measured and published in `docs/product/one-pager.md` |

## File Structure

```
libs/python/stonecharts/limits.py   # new — LIMIT constants + check_resource_limits(spec_dict) -> list[str]
libs/python/stonecharts/spec.py     # modified — from_dict() also calls check_resource_limits()
libs/go/limits.go                   # new — the same constants + CheckResourceLimits(spec) []string
libs/go/spec.go                     # modified — FromJSON (or equivalent) also calls CheckResourceLimits

libs/python/tests/test_limits.py    # new — unit tests for limits.py in isolation
libs/go/limits_test.go              # new — unit tests for limits.go in isolation
```

---

### Task 1: Python resource limits — series count, points, and spec size

**Files:**
- Create: `libs/python/stonecharts/limits.py`
- Modify: `libs/python/stonecharts/spec.py` (`ChartSpec.from_dict`, currently around line 277-285)
- Test: `libs/python/tests/test_limits.py`

**Interfaces:**
- Produces: `MAX_SERIES: int`, `MAX_POINTS_PER_SERIES: int`, `MAX_TOTAL_POINTS: int`, `MAX_SPEC_BYTES: int`, `check_resource_limits(spec_dict: dict) -> list[str]` (each violation is a string starting with `"LIMIT.<NAME>: "`)

- [ ] **Step 1: Write the failing tests**

Create `libs/python/tests/test_limits.py`:

```python
from __future__ import annotations

import json

from stonecharts.limits import (
    MAX_POINTS_PER_SERIES,
    MAX_SERIES,
    MAX_SPEC_BYTES,
    MAX_TOTAL_POINTS,
    check_resource_limits,
)


def _spec_with_series(n: int, points_per_series: int = 1) -> dict:
    return {
        "type": "line",
        "series": [{"name": f"s{i}", "data": list(range(points_per_series))} for i in range(n)],
    }


def test_series_count_within_limit_passes():
    errs = check_resource_limits(_spec_with_series(MAX_SERIES))
    assert not any(e.startswith("LIMIT.MAX_SERIES") for e in errs)


def test_series_count_over_limit_fails():
    errs = check_resource_limits(_spec_with_series(MAX_SERIES + 1))
    assert any(e.startswith("LIMIT.MAX_SERIES") for e in errs)


def test_points_per_series_over_limit_fails():
    errs = check_resource_limits(_spec_with_series(1, MAX_POINTS_PER_SERIES + 1))
    assert any(e.startswith("LIMIT.MAX_POINTS_PER_SERIES") for e in errs)


def test_total_points_over_limit_fails_even_if_per_series_ok():
    # Many series, each individually within MAX_POINTS_PER_SERIES, but the sum exceeds
    # MAX_TOTAL_POINTS.
    per_series = 100
    n_series = (MAX_TOTAL_POINTS // per_series) + 2
    spec = _spec_with_series(n=min(n_series, MAX_SERIES), points_per_series=per_series)
    errs = check_resource_limits(spec)
    assert any(e.startswith("LIMIT.MAX_TOTAL_POINTS") for e in errs)


def test_spec_size_over_limit_fails():
    huge_label = "x" * (MAX_SPEC_BYTES + 1000)
    spec = {"type": "line", "title": huge_label, "series": []}
    errs = check_resource_limits(spec, raw_size_hint=len(json.dumps(spec)))
    assert any(e.startswith("LIMIT.MAX_SPEC_BYTES") for e in errs)


def test_valid_small_spec_has_no_limit_errors():
    spec = {"type": "line", "series": [{"name": "a", "data": [1, 2, 3]}]}
    assert check_resource_limits(spec) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd libs/python && python -m pytest tests/test_limits.py -v`
Expected: `ModuleNotFoundError: No module named 'stonecharts.limits'`

- [ ] **Step 3: Write the minimal implementation**

Create `libs/python/stonecharts/limits.py`:

```python
from __future__ import annotations

from typing import Any

MAX_SERIES = 50
MAX_POINTS_PER_SERIES = 10_000
MAX_TOTAL_POINTS = 50_000
MAX_SPEC_BYTES = 5_000_000
MAX_LABEL_LENGTH = 500


def _series_point_count(series: dict) -> int:
    data = series.get("data")
    return len(data) if isinstance(data, list) else 0


def check_resource_limits(spec_dict: dict, raw_size_hint: int | None = None) -> list[str]:
    errs: list[str] = []
    series = spec_dict.get("series")
    if isinstance(series, list):
        if len(series) > MAX_SERIES:
            errs.append(f"LIMIT.MAX_SERIES: {len(series)} series exceeds the maximum of {MAX_SERIES}")
        total_points = 0
        for i, s in enumerate(series):
            if not isinstance(s, dict):
                continue
            count = _series_point_count(s)
            total_points += count
            if count > MAX_POINTS_PER_SERIES:
                errs.append(f"LIMIT.MAX_POINTS_PER_SERIES: series[{i}] has {count} points, exceeding the maximum of {MAX_POINTS_PER_SERIES}")
        if total_points > MAX_TOTAL_POINTS:
            errs.append(f"LIMIT.MAX_TOTAL_POINTS: {total_points} total points across all series exceeds the maximum of {MAX_TOTAL_POINTS}")

    if raw_size_hint is not None and raw_size_hint > MAX_SPEC_BYTES:
        errs.append(f"LIMIT.MAX_SPEC_BYTES: specification is {raw_size_hint} bytes, exceeding the maximum of {MAX_SPEC_BYTES}")

    return errs
```

In `libs/python/stonecharts/spec.py`, locate `ChartSpec.from_dict` (currently lines 277-285):

```python
    @staticmethod
    def from_dict(d: dict) -> "ChartSpec":
        """Build a ChartSpec from a plain dict (parsed JSON).

        The dict is validated first (same rules as the Go renderer); a malformed
        spec raises SpecError. Unknown keys are ignored. Values are trusted after
        validation, so parsing does no coercion — defaults apply only on absence.
        """
        errs = validate(d)
        if errs:
            raise SpecError(errs)
```

becomes:

```python
    @staticmethod
    def from_dict(d: dict, raw_size_hint: int | None = None) -> "ChartSpec":
        """Build a ChartSpec from a plain dict (parsed JSON).

        The dict is validated first (same rules as the Go renderer); a malformed
        spec raises SpecError. Unknown keys are ignored. Values are trusted after
        validation, so parsing does no coercion — defaults apply only on absence.
        """
        errs = validate(d)
        errs.extend(check_resource_limits(d, raw_size_hint=raw_size_hint))
        if errs:
            raise SpecError(errs)
```

Add `from stonecharts.limits import check_resource_limits` to `spec.py`'s existing import block (check the existing imports first and place it alongside them, matching the file's existing import style — relative vs absolute).

**Note:** `raw_size_hint` is optional and defaults to `None` (no spec-size check) so this stays backward compatible for any existing caller of `ChartSpec.from_dict(d)` with one positional argument — Task 2 wires a real byte-size hint through from the actual callers that have it (e.g. `tools/stonecharts_verify.py` already reads `spec_bytes` before parsing).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd libs/python && python -m pytest tests/test_limits.py -v`
Expected: all 6 tests PASS

- [ ] **Step 5: Verify no existing example fixture trips a limit**

Run this check (adjust the glob if `charts/` isn't reachable relative to `libs/python`):

```bash
python -c "
import json, pathlib
import sys
sys.path.insert(0, 'libs/python')
from stonecharts.limits import check_resource_limits
failures = []
for f in pathlib.Path('charts').glob('*/examples/*.json'):
    spec = json.loads(f.read_text(encoding='utf-8'))
    errs = check_resource_limits(spec, raw_size_hint=len(f.read_bytes()))
    if errs:
        failures.append((str(f), errs))
print('failures:', failures)
assert not failures, failures
print('all existing examples pass within limits')
"
```

Expected: `all existing examples pass within limits`. If any existing fixture fails, that means the chosen limit value in this plan's table is too low — raise it (in both this plan's table and the constant) rather than treating a certified example as the problem, then re-run.

- [ ] **Step 6: Run the full existing test suite**

Run: `python -m pytest libs/python/tests -q`
Expected: all tests pass (no regression from the pre-plan count)

- [ ] **Step 7: Commit**

```bash
git add libs/python/stonecharts/limits.py libs/python/stonecharts/spec.py libs/python/tests/test_limits.py
git commit -m "Add Python resource limits: series count, points, spec size (WORK-VERIFY-012)"
```

---

### Task 2: Wire the spec-size hint through from real callers, and add label-length + SVG-size limits

**Files:**
- Modify: `libs/python/stonecharts/limits.py` (add `MAX_GENERATED_SVG_BYTES`, `check_label_lengths`)
- Modify: `libs/python/stonecharts/render.py` (check generated SVG size before returning)
- Modify: `tools/stonecharts_verify.py` (`render_python`, pass the real `raw_size_hint` through)
- Test: `libs/python/tests/test_limits.py`

**Interfaces:**
- Consumes: `check_resource_limits` (Task 1)
- Produces: `MAX_GENERATED_SVG_BYTES: int`, `check_label_lengths(spec_dict: dict) -> list[str]`

- [ ] **Step 1: Write the failing tests**

Add to `libs/python/tests/test_limits.py`:

```python
from stonecharts.limits import MAX_GENERATED_SVG_BYTES, MAX_LABEL_LENGTH, check_label_lengths


def test_title_over_label_length_limit_fails():
    spec = {"type": "line", "title": "x" * (MAX_LABEL_LENGTH + 1), "series": []}
    errs = check_label_lengths(spec)
    assert any(e.startswith("LIMIT.MAX_LABEL_LENGTH") for e in errs)


def test_series_name_over_label_length_limit_fails():
    spec = {"type": "line", "series": [{"name": "y" * (MAX_LABEL_LENGTH + 1), "data": [1]}]}
    errs = check_label_lengths(spec)
    assert any(e.startswith("LIMIT.MAX_LABEL_LENGTH") for e in errs)


def test_labels_within_limit_pass():
    spec = {"type": "line", "title": "A normal title", "series": [{"name": "s", "data": [1]}]}
    assert check_label_lengths(spec) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd libs/python && python -m pytest tests/test_limits.py -k label_length -v`
Expected: `ImportError: cannot import name 'check_label_lengths'`

- [ ] **Step 3: Write the minimal implementation**

Add to `libs/python/stonecharts/limits.py`:

```python
MAX_GENERATED_SVG_BYTES = 20_000_000


def check_label_lengths(spec_dict: dict) -> list[str]:
    errs: list[str] = []
    for field in ("title", "subtitle"):
        value = spec_dict.get(field)
        if isinstance(value, str) and len(value) > MAX_LABEL_LENGTH:
            errs.append(f"LIMIT.MAX_LABEL_LENGTH: $.{field} is {len(value)} characters, exceeding the maximum of {MAX_LABEL_LENGTH}")
    for axis_key in ("xAxis", "yAxis"):
        axis = spec_dict.get(axis_key)
        if isinstance(axis, dict):
            title = axis.get("title")
            if isinstance(title, str) and len(title) > MAX_LABEL_LENGTH:
                errs.append(f"LIMIT.MAX_LABEL_LENGTH: $.{axis_key}.title is {len(title)} characters, exceeding the maximum of {MAX_LABEL_LENGTH}")
    series = spec_dict.get("series")
    if isinstance(series, list):
        for i, s in enumerate(series):
            if not isinstance(s, dict):
                continue
            name = s.get("name")
            if isinstance(name, str) and len(name) > MAX_LABEL_LENGTH:
                errs.append(f"LIMIT.MAX_LABEL_LENGTH: $.series[{i}].name is {len(name)} characters, exceeding the maximum of {MAX_LABEL_LENGTH}")
    return errs
```

Update `check_resource_limits` (from Task 1) to also call this:

```python
def check_resource_limits(spec_dict: dict, raw_size_hint: int | None = None) -> list[str]:
    errs: list[str] = []
    errs.extend(check_label_lengths(spec_dict))
    # ... (rest of Task 1's body unchanged, appending to the same errs list)
```

In `tools/stonecharts_verify.py`'s `render_python()` (check the current function — it's near the top, calls `render_svg(ChartSpec.from_dict(spec_data))`), pass the real byte size through:

```python
def render_python(spec_data: dict[str, Any], raw_size_hint: int | None = None) -> tuple[bytes, dict[str, Any]]:
    svg = render_svg(ChartSpec.from_dict(spec_data, raw_size_hint=raw_size_hint)).encode("utf-8")
```

and at its one call site in `main()`, pass `len(spec_bytes)` (already computed earlier in `main()` as `spec_bytes = canonical_json_bytes(spec_data)`).

For the generated-SVG-size limit, in `libs/python/stonecharts/render.py`, find the top-level `render_svg(spec) -> str` function's final return statement and wrap it:

```python
def render_svg(spec: ChartSpec) -> str:
    # ... existing body producing `svg_string` ...
    if len(svg_string.encode("utf-8")) > MAX_GENERATED_SVG_BYTES:
        raise SpecError([f"LIMIT.MAX_GENERATED_SVG_BYTES: generated SVG is {len(svg_string.encode('utf-8'))} bytes, exceeding the maximum of {MAX_GENERATED_SVG_BYTES}"])
    return svg_string
```

Read the actual current `render_svg` function first to find its real final variable name and return statement — do not assume `svg_string` is the correct name without checking.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd libs/python && python -m pytest tests/test_limits.py -v`
Expected: all tests PASS

Run: `python -m pytest libs/python/tests -q`
Expected: all tests pass, no regression

- [ ] **Step 5: Commit**

```bash
git add libs/python/stonecharts/limits.py libs/python/stonecharts/render.py tools/stonecharts_verify.py libs/python/tests/test_limits.py
git commit -m "Add label-length and generated-SVG-size limits, wire real spec-size hint through (WORK-VERIFY-012)"
```

---

### Task 3: Port all Python limits to Go with identical constants

**Files:**
- Create: `libs/go/limits.go`
- Modify: `libs/go/spec.go` (wherever it parses/validates a spec — read the file first to find the exact call site)
- Test: `libs/go/limits_test.go`

**Interfaces:**
- Produces: Go constants matching Task 1/2's Python values exactly (`MaxSeries = 50`, `MaxPointsPerSeries = 10_000`, `MaxTotalPoints = 50_000`, `MaxSpecBytes = 5_000_000`, `MaxLabelLength = 500`, `MaxGeneratedSVGBytes = 20_000_000`) and `CheckResourceLimits(spec map[string]interface{}, rawSizeHint int) []string` returning the same `"LIMIT.<NAME>: ..."` string convention.

- [ ] **Step 1: Write the failing tests**

Create `libs/go/limits_test.go` (read an existing `_test.go` file in this package first, e.g. `render_test.go`, to match its package name and import style):

```go
package stonecharts

import (
	"strings"
	"testing"
)

func specWithSeries(n, pointsPerSeries int) map[string]interface{} {
	series := make([]interface{}, n)
	for i := 0; i < n; i++ {
		data := make([]interface{}, pointsPerSeries)
		for j := range data {
			data[j] = j
		}
		series[i] = map[string]interface{}{"name": "s", "data": data}
	}
	return map[string]interface{}{"type": "line", "series": series}
}

func hasLimitCode(errs []string, code string) bool {
	for _, e := range errs {
		if strings.HasPrefix(e, "LIMIT."+code) {
			return true
		}
	}
	return false
}

func TestSeriesCountWithinLimitPasses(t *testing.T) {
	errs := CheckResourceLimits(specWithSeries(MaxSeries, 1), 0)
	if hasLimitCode(errs, "MAX_SERIES") {
		t.Fatalf("expected no MAX_SERIES violation, got %v", errs)
	}
}

func TestSeriesCountOverLimitFails(t *testing.T) {
	errs := CheckResourceLimits(specWithSeries(MaxSeries+1, 1), 0)
	if !hasLimitCode(errs, "MAX_SERIES") {
		t.Fatalf("expected MAX_SERIES violation, got %v", errs)
	}
}

func TestPointsPerSeriesOverLimitFails(t *testing.T) {
	errs := CheckResourceLimits(specWithSeries(1, MaxPointsPerSeries+1), 0)
	if !hasLimitCode(errs, "MAX_POINTS_PER_SERIES") {
		t.Fatalf("expected MAX_POINTS_PER_SERIES violation, got %v", errs)
	}
}

func TestSpecSizeOverLimitFails(t *testing.T) {
	errs := CheckResourceLimits(specWithSeries(1, 1), MaxSpecBytes+1000)
	if !hasLimitCode(errs, "MAX_SPEC_BYTES") {
		t.Fatalf("expected MAX_SPEC_BYTES violation, got %v", errs)
	}
}

func TestValidSmallSpecHasNoLimitErrors(t *testing.T) {
	errs := CheckResourceLimits(specWithSeries(1, 3), 100)
	if len(errs) != 0 {
		t.Fatalf("expected no limit errors, got %v", errs)
	}
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd libs/go && go test ./... -run TestSeriesCount`
Expected: build failure — `undefined: CheckResourceLimits` (or `MaxSeries`, etc.)

- [ ] **Step 3: Write the minimal implementation**

Create `libs/go/limits.go` (match the existing package name from `render_test.go`'s `package` declaration):

```go
package stonecharts

import "fmt"

const (
	MaxSeries            = 50
	MaxPointsPerSeries    = 10_000
	MaxTotalPoints        = 50_000
	MaxSpecBytes          = 5_000_000
	MaxLabelLength        = 500
	MaxGeneratedSVGBytes  = 20_000_000
)

func seriesPointCount(series map[string]interface{}) int {
	data, ok := series["data"].([]interface{})
	if !ok {
		return 0
	}
	return len(data)
}

func checkLabelLength(value interface{}, path string, errs *[]string) {
	s, ok := value.(string)
	if !ok {
		return
	}
	if len(s) > MaxLabelLength {
		*errs = append(*errs, fmt.Sprintf("LIMIT.MAX_LABEL_LENGTH: %s is %d characters, exceeding the maximum of %d", path, len(s), MaxLabelLength))
	}
}

func CheckResourceLimits(spec map[string]interface{}, rawSizeHint int) []string {
	var errs []string

	checkLabelLength(spec["title"], "$.title", &errs)
	checkLabelLength(spec["subtitle"], "$.subtitle", &errs)
	for _, axisKey := range []string{"xAxis", "yAxis"} {
		if axis, ok := spec[axisKey].(map[string]interface{}); ok {
			checkLabelLength(axis["title"], "$."+axisKey+".title", &errs)
		}
	}

	if seriesList, ok := spec["series"].([]interface{}); ok {
		if len(seriesList) > MaxSeries {
			errs = append(errs, fmt.Sprintf("LIMIT.MAX_SERIES: %d series exceeds the maximum of %d", len(seriesList), MaxSeries))
		}
		totalPoints := 0
		for i, raw := range seriesList {
			s, ok := raw.(map[string]interface{})
			if !ok {
				continue
			}
			checkLabelLength(s["name"], fmt.Sprintf("$.series[%d].name", i), &errs)
			count := seriesPointCount(s)
			totalPoints += count
			if count > MaxPointsPerSeries {
				errs = append(errs, fmt.Sprintf("LIMIT.MAX_POINTS_PER_SERIES: series[%d] has %d points, exceeding the maximum of %d", i, count, MaxPointsPerSeries))
			}
		}
		if totalPoints > MaxTotalPoints {
			errs = append(errs, fmt.Sprintf("LIMIT.MAX_TOTAL_POINTS: %d total points across all series exceeds the maximum of %d", totalPoints, MaxTotalPoints))
		}
	}

	if rawSizeHint > MaxSpecBytes {
		errs = append(errs, fmt.Sprintf("LIMIT.MAX_SPEC_BYTES: specification is %d bytes, exceeding the maximum of %d", rawSizeHint, MaxSpecBytes))
	}

	return errs
}
```

Read `libs/go/spec.go` to find its actual spec-parsing entry point (the brief cannot know its exact current signature without you reading it) and wire `CheckResourceLimits` in alongside the existing validation call, appending its results to whatever error slice that function already returns — matching the same "additive, alongside existing validation" pattern Task 1 used in Python. If the entry point's signature doesn't have an obvious place to receive a raw byte-size hint, pass `0` for now (meaning "no spec-size check performed at this call site") rather than inventing a signature change beyond what's needed — wiring the real byte count through every Go call site is a smaller follow-up, not blocking for this task.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd libs/go && go test ./...`
Expected: all tests PASS, no regression from the pre-plan test count

- [ ] **Step 5: Commit**

```bash
git add libs/go/limits.go libs/go/spec.go libs/go/limits_test.go
git commit -m "Port resource limits to Go with identical constants (WORK-VERIFY-012)"
```

---

### Task 4: Unicode and escaping safety across both runtimes

**Files:**
- Test: `libs/python/tests/test_golden.py` or a new `libs/python/tests/test_unicode_safety.py` (check which existing file is the right home — if `test_golden.py` already has an escaping/XSS test per the existing `docs/product/one-pager.md`/security-review references to "XSS/injection coverage", extend that file instead of creating a new one)
- Test: Go equivalent, same file-placement decision

**Interfaces:**
- Consumes: existing `render_svg`/Go renderer entry points
- Produces: no new interface — this task is test coverage only

- [ ] **Step 1: Investigate existing coverage first**

Before writing anything, search both test suites for existing Unicode/escaping/XSS tests:

```bash
grep -rn "unicode\|escap\|XSS\|<script" libs/python/tests/ libs/go/*_test.go
```

`docs/releases/*/evidence/*-accessibility-security-review.md` and the requirements registry's `REQ-SEC-001` reference "XSS/injection coverage" as already proven for every certified chart type — if this grep turns up existing, adequate tests, this task may already be satisfied; report that instead of duplicating coverage. Only proceed to Step 2 if there's a genuine gap (e.g. multi-byte Unicode specifically, as opposed to HTML-escaping specifically, which are different concerns).

- [ ] **Step 2: If a gap exists, write the failing tests**

(Concrete content depends on Step 1's findings — if proceeding, follow the exact pattern of whichever existing escaping test you found, testing multi-byte Unicode (e.g. `"日本語 émoji 🎉"`) in `title`, series `name`, and category labels, asserting the generated SVG contains the correctly UTF-8-encoded text with no mis-encoding, and that both Python and Go produce byte-identical output for the same Unicode-containing spec (reusing the existing golden/parity test pattern, not inventing a new one).)

- [ ] **Step 3: Commit** (only if Step 1 found a real gap and Step 2 added tests)

```bash
git add <files touched>
git commit -m "Add multi-byte Unicode safety coverage across both runtimes (WORK-VERIFY-012)"
```

## What this plan deliberately does not do

- **Does not add randomized property tests across all 6 certified chart types.** This is real, valuable work, but it is the same shape 6 times (generate N random valid specs per chart type using stdlib `random`, assert the renderer doesn't crash and produces valid SVG, assert Python/Go byte-parity holds). It deserves its own plan — and because each chart type's property test touches only that chart type's own example/golden fixtures, it's a genuine candidate for parallel per-chart-type dispatch, unlike this plan's tasks which all had to be sequenced through the same two `limits.py`/`limits.go` files.
- **Does not add cross-language invalid-input parity tests for every documented error class in `docs/contracts/validation-and-capabilities.md`.** Same reasoning — mechanically repetitive per error class, deserves its own plan once that document's exact list of classes is enumerated task-by-task.
- **Does not enforce a coverage threshold in CI.** That's a `.github/workflows/quality.yml` change plus a coverage-tool decision (`coverage.py`'s `--cov-fail-under`, Go's `go test -cover` combined with some threshold-checking wrapper) — a CI/tooling decision, not a code-and-tests task like the rest of this plan.
- **Does not add a comparison timeout or evidence-bundle-size/finding-count limits.** Those live in `tools/stonecharts_verify.py`'s comparison path, not the renderers' `validate`/`limits` path this plan touches — they belong with `WORK-VERIFY-010`'s exit-code work (same file, same natural sequencing point) rather than here.
- **Does not implement an actual render timeout mechanism.** The 10-second value is chosen and documented in this plan's table, but wiring a real timeout (likely `concurrent.futures.ThreadPoolExecutor` with a deadline in Python, `context.WithTimeout` in Go) around the render call is a real, separate piece of work with its own failure-mode design (what happens to a timed-out render's partial output, temp files, etc.) — flagging it as unimplemented rather than faking a limit that isn't actually enforced.
