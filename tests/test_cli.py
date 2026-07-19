from __future__ import annotations

import json
from pathlib import Path

import pytest

from evidenceops import cli
from evidenceops.domain import validate_evidence_object
from scripts.check_public_artifacts import scan as scan_public


def test_run_demo_reproduces_complete_public_flow(tmp_path: Path) -> None:
    output = tmp_path / "demo"
    assert cli.main(["run-demo", "--output-dir", str(output)]) == 0
    assert {path.name for path in output.iterdir()} == cli.STATIC_DEMO_FILENAMES
    assert scan_public(output) == []
    for path in output.glob("*.json"):
        validate_evidence_object(json.loads(path.read_text(encoding="utf-8")))


def test_run_demo_refuses_nonempty_directory(tmp_path: Path) -> None:
    output = tmp_path / "demo"
    output.mkdir()
    (output / "operator-file.txt").write_text("preserve", encoding="utf-8")
    assert cli.main(["run-demo", "--output-dir", str(output)]) == 2
    assert (output / "operator-file.txt").read_text(encoding="utf-8") == "preserve"


def test_live_collection_requires_explicit_auth_and_never_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("EVIDENCEOPS_GRAPH_ACCESS_TOKEN", raising=False)
    result = cli.main(["live-collect", "--auth", "environment-token"])
    assert result == 2


def test_cli_has_no_apply_or_remediation_command() -> None:
    parser = cli.build_parser()
    help_text = parser.format_help().lower()
    assert "apply" not in help_text
    assert "remediat" not in help_text


def test_static_demo_rebuild_writes_only_approved_synthetic_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "STATIC_DEMO_DATA_DIRECTORY", tmp_path)
    assert cli.main(["rebuild-static-demo"]) == 0
    assert {path.name for path in tmp_path.iterdir()} == cli.STATIC_DEMO_FILENAMES
    assert scan_public(tmp_path) == []


def test_retired_pages_command_remains_a_compatible_local_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "STATIC_DEMO_DATA_DIRECTORY", tmp_path)
    assert cli.main(["rebuild-pages-demo"]) == 0
    assert {path.name for path in tmp_path.iterdir()} == cli.STATIC_DEMO_FILENAMES
