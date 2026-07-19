from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import cast

import pytest

from evidenceops.domain import JsonValue
from evidenceops.evidence import validate_public_mission_snapshot
from evidenceops.evidence.mission import build_public_mission_snapshot
from evidenceops.mission_demo import MISSION_PSEUDONYM_KEY, _collection, build_mission_demo
from scripts.promote_live_mission import promote_live_mission
from scripts.verify_runtime_status import verify_runtime_status


def _live_mission() -> dict[str, JsonValue]:
    return build_public_mission_snapshot(
        _collection(previous=False),
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=False,
        source_git_commit="a" * 40,
    )


def _status(mission: dict[str, JsonValue]) -> dict[str, JsonValue]:
    collection = cast(dict[str, JsonValue], mission["collection"])
    return {
        "schema_version": "1.0.0",
        "service": "EvidenceOps narrative boundary",
        "status": "ok",
        "narrative_mode": "fixture",
        "model": "gpt-5.6-terra",
        "model_configured": True,
        "narrative_available": True,
        "public_data_boundary": "synthetic-or-fail-closed-sanitized-only",
        "human_review_required": True,
        "data_mode": mission["data_mode"],
        "evidence_timestamp": collection["collected_at_utc"],
        "source_snapshot_id": mission["snapshot_id"],
        "live_intune_collection_performed": mission["data_mode"] == "LIVE SANITIZED TENANT DATA",
        "intune_write_capability": False,
        "byok_supported": False,
        "assistant_endpoint": "/api/ask",
    }


def test_live_mission_promotion_revalidates_and_writes_atomically(tmp_path: Path) -> None:
    mission = _live_mission()
    source = tmp_path / "mission-control.json"
    destination = tmp_path / "published" / "mission-control.json"
    source.write_text(json.dumps(mission), encoding="utf-8")

    promote_live_mission(source, destination)

    published = json.loads(destination.read_text(encoding="utf-8"))
    validate_public_mission_snapshot(published)
    assert published == mission
    assert not destination.with_suffix(".json.tmp").exists()


def test_live_mission_promotion_rejects_synthetic_or_tampered_packages(tmp_path: Path) -> None:
    source = tmp_path / "mission-control.json"
    destination = tmp_path / "published.json"
    source.write_text(json.dumps(build_mission_demo()), encoding="utf-8")
    with pytest.raises(ValueError, match="live sanitized"):
        promote_live_mission(source, destination)

    tampered = _live_mission()
    tampered["human_approval_status"] = "Approved"
    source.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        promote_live_mission(source, destination)
    assert not destination.exists()


def test_live_mission_promotion_rejects_symlinks_and_oversized_inputs(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text(json.dumps(_live_mission()), encoding="utf-8")
    source_link = tmp_path / "source.json"
    source_link.symlink_to(target)
    with pytest.raises(ValueError, match="regular file"):
        promote_live_mission(source_link, tmp_path / "out.json")

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b"{" + b" " * 2_000_000 + b"}")
    with pytest.raises(ValueError, match="package limit"):
        promote_live_mission(oversized, tmp_path / "out.json")


@pytest.mark.parametrize(
    "mission",
    [build_mission_demo(), _live_mission()],
    ids=("synthetic", "live-sanitized"),
)
def test_runtime_status_accepts_only_the_expected_reviewed_mode(
    mission: dict[str, JsonValue],
) -> None:
    status = _status(mission)
    verify_runtime_status(
        status,
        expected_data_mode=cast(str, mission["data_mode"]),
        expected_narrative_mode="fixture",
    )

    wrong = copy.deepcopy(status)
    wrong["intune_write_capability"] = True
    with pytest.raises(ValueError, match="intune_write_capability"):
        verify_runtime_status(
            wrong,
            expected_data_mode=cast(str, mission["data_mode"]),
            expected_narrative_mode="fixture",
        )


def test_runtime_status_rejects_wrong_mode_unknown_fields_and_unsafe_values() -> None:
    mission = _live_mission()
    status = _status(mission)
    with pytest.raises(ValueError, match="data_mode"):
        verify_runtime_status(
            status,
            expected_data_mode="SYNTHETIC DEMO DATA",
            expected_narrative_mode="fixture",
        )

    unknown = copy.deepcopy(status)
    unknown["raw_tenant_export"] = "not permitted"
    with pytest.raises(ValueError, match="unknown field"):
        verify_runtime_status(
            unknown,
            expected_data_mode="LIVE SANITIZED TENANT DATA",
            expected_narrative_mode="fixture",
        )

    unsafe = copy.deepcopy(status)
    unsafe["source_snapshot_id"] = "github_pat_" + "a" * 40
    with pytest.raises(ValueError, match="GitHub token"):
        verify_runtime_status(
            unsafe,
            expected_data_mode="LIVE SANITIZED TENANT DATA",
            expected_narrative_mode="fixture",
        )
