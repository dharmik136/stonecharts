from __future__ import annotations

import subprocess

import pytest

from tools import check_evidence_regression


def test_certified_example_discovery_covers_all_chart_directories() -> None:
    examples = check_evidence_regression.discover_certified_examples()

    chart_ids = {chart_id for chart_id, _ in examples}
    assert len(chart_ids) == check_evidence_regression.EXPECTED_CERTIFIED_CHARTS
    assert len(examples) >= len(chart_ids)


def test_required_command_propagates_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(["stoneverify"], 17, "partial output\n", "render failed\n")

    monkeypatch.setattr(check_evidence_regression.subprocess, "run", fail)

    with pytest.raises(
        check_evidence_regression.EvidenceRegressionError,
        match="exit code 17",
    ):
        check_evidence_regression.run_required(["stoneverify"], label="injected render")
