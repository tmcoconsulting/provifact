from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import cast

import pytest

from evidenceops.domain import JsonValue
from evidenceops.evidence import load_public_mission_snapshot, validate_public_mission_snapshot
from evidenceops.evidence.mission import build_public_mission_snapshot
from evidenceops.mission_demo import MISSION_PSEUDONYM_KEY, _collection, build_mission_demo
from scripts.promote_live_mission import promote_live_mission
from scripts.verify_cloudflare_deployment import verify_active_deployment
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
        "service": "Provifact narrative boundary",
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


def test_previous_public_loader_rejects_private_synthetic_and_linked_inputs(
    tmp_path: Path,
) -> None:
    live = tmp_path / "live.json"
    live.write_text(json.dumps(_live_mission()), encoding="utf-8")
    assert load_public_mission_snapshot(live, require_live=True)["data_mode"] == (
        "LIVE SANITIZED TENANT DATA"
    )

    synthetic = tmp_path / "synthetic.json"
    synthetic.write_text(json.dumps(build_mission_demo()), encoding="utf-8")
    with pytest.raises(ValueError, match="live sanitized"):
        load_public_mission_snapshot(synthetic, require_live=True)

    private = tmp_path / "private.json"
    private.write_text(json.dumps({"document_type": "private"}), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        load_public_mission_snapshot(private, require_live=True)

    link = tmp_path / "link.json"
    link.symlink_to(live)
    with pytest.raises(ValueError, match="regular file"):
        load_public_mission_snapshot(link, require_live=True)


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
        expected_source_snapshot_id=cast(str, mission["snapshot_id"]),
    )

    wrong = copy.deepcopy(status)
    wrong["intune_write_capability"] = True
    with pytest.raises(ValueError, match="intune_write_capability"):
        verify_runtime_status(
            wrong,
            expected_data_mode=cast(str, mission["data_mode"]),
            expected_narrative_mode="fixture",
            expected_source_snapshot_id=cast(str, mission["snapshot_id"]),
        )


def test_runtime_status_rejects_wrong_mode_unknown_fields_and_unsafe_values() -> None:
    mission = _live_mission()
    status = _status(mission)
    with pytest.raises(ValueError, match="data_mode"):
        verify_runtime_status(
            status,
            expected_data_mode="SYNTHETIC DEMO DATA",
            expected_narrative_mode="fixture",
            expected_source_snapshot_id=cast(str, mission["snapshot_id"]),
        )

    unknown = copy.deepcopy(status)
    unknown["raw_tenant_export"] = "not permitted"
    with pytest.raises(ValueError, match="unknown field"):
        verify_runtime_status(
            unknown,
            expected_data_mode="LIVE SANITIZED TENANT DATA",
            expected_narrative_mode="fixture",
            expected_source_snapshot_id=cast(str, mission["snapshot_id"]),
        )

    unsafe = copy.deepcopy(status)
    unsafe["source_snapshot_id"] = "github_pat_" + "a" * 40
    with pytest.raises(ValueError, match="GitHub token"):
        verify_runtime_status(
            unsafe,
            expected_data_mode="LIVE SANITIZED TENANT DATA",
            expected_narrative_mode="fixture",
            expected_source_snapshot_id=cast(str, mission["snapshot_id"]),
        )

    with pytest.raises(ValueError, match="does not match"):
        verify_runtime_status(
            status,
            expected_data_mode="LIVE SANITIZED TENANT DATA",
            expected_narrative_mode="fixture",
            expected_source_snapshot_id="mission-" + "0" * 24,
        )


def _cloudflare_control_plane() -> tuple[list[object], list[object], str]:
    message = "evidenceops-snapshot:mission-" + "a" * 24
    versions: list[object] = [
        {
            "id": "version-old",
            "metadata": {"created_on": "2026-07-19T20:00:00Z", "source": "wrangler"},
            "annotations": {"workers/triggered_by": "version_upload"},
        },
        {
            "id": "version-reviewed",
            "metadata": {"created_on": "2026-07-19T20:42:02Z", "source": "wrangler"},
            "annotations": {
                "workers/message": message,
                "workers/triggered_by": "version_upload",
            },
        },
    ]
    deployments: list[object] = [
        {
            "source": "wrangler",
            "annotations": {"workers/triggered_by": "deployment"},
            "created_on": "2026-07-19T20:42:03Z",
            "versions": [{"version_id": "version-reviewed", "percentage": 100}],
        }
    ]
    return versions, deployments, message


def test_cloudflare_control_plane_proves_reviewed_version_is_fully_active() -> None:
    versions, deployments, message = _cloudflare_control_plane()
    verify_active_deployment(versions, deployments, expected_message=message)


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("missing-message", "reviewed snapshot version is absent"),
        ("wrong-version", "not receiving 100 percent"),
        ("split-traffic", "single-version rollout"),
        ("wrong-source", "source is not Wrangler"),
        ("bad-timestamp", "timestamp is invalid"),
    ],
)
def test_cloudflare_control_plane_rejects_unreviewed_or_partial_deployments(
    mutation: str, error: str
) -> None:
    versions, deployments, message = _cloudflare_control_plane()
    reviewed = cast(dict[str, object], versions[1])
    active_deployment = cast(dict[str, object], deployments[0])
    if mutation == "missing-message":
        cast(dict[str, object], reviewed["annotations"])["workers/message"] = "different"
    elif mutation == "wrong-version":
        cast(list[dict[str, object]], active_deployment["versions"])[0]["version_id"] = (
            "version-old"
        )
    elif mutation == "split-traffic":
        cast(list[dict[str, object]], active_deployment["versions"]).append(
            {"version_id": "version-old", "percentage": 10}
        )
    elif mutation == "wrong-source":
        reviewed_metadata = cast(dict[str, object], reviewed["metadata"])
        reviewed_metadata["source"] = "dashboard"
    else:
        active_deployment["created_on"] = "not-a-timestamp"
    with pytest.raises(ValueError, match=error):
        verify_active_deployment(versions, deployments, expected_message=message)


def test_cloudflare_control_plane_rejects_invalid_snapshot_message() -> None:
    versions, deployments, _ = _cloudflare_control_plane()
    with pytest.raises(ValueError, match="message is invalid"):
        verify_active_deployment(
            versions,
            deployments,
            expected_message="evidenceops-snapshot:unclassified",
        )
