from __future__ import annotations

import json
from pathlib import Path

import pytest

from evidenceops.mission_demo import build_mission_demo
from scripts.report_public_counts import main as report_public_counts


def test_report_public_counts_accepts_validated_mission_snapshot(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    package = tmp_path / "mission-control.json"
    package.write_text(json.dumps(build_mission_demo()), encoding="utf-8")

    assert report_public_counts([str(package)]) == 0

    output = capsys.readouterr().out
    assert "## Sanitized Apple validation" in output
    assert "- data mode: SYNTHETIC DEMO DATA" in output
    assert "- baseline rule count: 98" in output
    assert "- raw or private evidence retained: no" in output
    assert "- human review required: yes" in output
