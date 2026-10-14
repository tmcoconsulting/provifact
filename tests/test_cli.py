from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from evidenceops import cli
from evidenceops.domain import JsonValue, validate_evidence_object
from evidenceops.evidence import (
    build_public_mission_snapshot,
    private_collection_document,
    validate_public_mission_snapshot,
)
from evidenceops.evidence.matrix import validate_public_matrix
from evidenceops.mission_demo import MISSION_PSEUDONYM_KEY, _collection, build_mission_demo
from scripts.check_public_artifacts import scan as scan_public


def test_run_demo_reproduces_complete_public_flow(tmp_path: Path) -> None:
    output = tmp_path / "demo"
    assert cli.main(["run-demo", "--output-dir", str(output)]) == 0
    assert {path.name for path in output.iterdir()} == cli.STATIC_DEMO_FILENAMES
    assert scan_public(output) == []
    for path in output.glob("*.json"):
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if path.name == "mission-control.json":
            validate_public_mission_snapshot(loaded)
        elif path.name == "settings-matrix.json":
            mission = json.loads((output / "mission-control.json").read_text(encoding="utf-8"))
            validate_public_matrix(loaded, mission)
        else:
            validate_evidence_object(loaded)


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


def test_publish_mission_accepts_only_a_validated_prior_live_public_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private_path = tmp_path / "private-apple.json"
    private_path.write_text(
        json.dumps(
            private_collection_document(
                _collection(previous=False), delete_after_utc="2026-07-21T00:00:00Z"
            )
        ),
        encoding="utf-8",
    )
    previous = build_public_mission_snapshot(
        _collection(previous=True),
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=False,
        source_git_commit="a" * 40,
    )
    previous_path = tmp_path / "previous-live.json"
    previous_path.write_text(json.dumps(previous), encoding="utf-8")
    output = tmp_path / "current-live.json"
    monkeypatch.setenv("EVIDENCEOPS_PSEUDONYM_KEY", "fixture-pseudonym-key-at-least-32-bytes")
    monkeypatch.setattr(cli, "_git_commit_sha", lambda: "b" * 40)

    assert (
        cli.main(
            [
                "publish-mission",
                str(private_path),
                "--output",
                str(output),
                "--previous-public",
                str(previous_path),
            ]
        )
        == 0
    )
    published = validate_public_mission_snapshot(json.loads(output.read_text(encoding="utf-8")))
    changes = cast(dict[str, JsonValue], published["changes"])
    assert changes["previous_snapshot_id"] == previous["snapshot_id"]
    assert changes["history_state"] == "compared"

    synthetic_path = tmp_path / "previous-synthetic.json"
    synthetic_path.write_text(json.dumps(build_mission_demo()), encoding="utf-8")
    assert (
        cli.main(
            [
                "publish-mission",
                str(private_path),
                "--output",
                str(tmp_path / "rejected.json"),
                "--previous-public",
                str(synthetic_path),
            ]
        )
        == 2
    )
