from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

from evidenceops.baselines import (
    APPROVAL_RECORD,
    BASELINE_RULES,
    DEMO_RULE_MAPPINGS,
    EXTRACTED_INVENTORY_SHA256,
    verify_approved_baseline,
)
from evidenceops.domain import JsonValue, fingerprint
from evidenceops.evidence import validate_public_mission_snapshot
from evidenceops.evidence.mission import (
    DriftOutcome,
    _deterministic_outcome,
    build_public_mission_snapshot,
)
from evidenceops.evidence.mission_storage import (
    collection_from_private_document,
    load_private_collection,
    private_collection_document,
    validate_private_collection,
    write_private_collection,
)
from evidenceops.mission_demo import (
    MISSION_PSEUDONYM_KEY,
    _collection,
    build_mission_demo,
    fixture_finding_outcomes,
)


def test_pinned_mscp_inventory_and_approval_are_complete() -> None:
    verify_approved_baseline()
    rules = [rule for _, section_rules in BASELINE_RULES for rule in section_rules]
    assert len(rules) == len(set(rules)) == 98
    assert set(DEMO_RULE_MAPPINGS).issubset(rules)
    assert EXTRACTED_INVENTORY_SHA256 == (
        "5cced0709c90885ede600f00a640a35b0679aed933cda456db80ee629ee54d41"
    )
    assert APPROVAL_RECORD["approval_status"] == "internally approved demo baseline"
    assert "not CIS" in cast(list[str], APPROVAL_RECORD["limitations"])[0]
    approval_path = (
        Path(__file__).parents[1] / "baselines" / "tmco-macos-cis-level1-demo-approval.json"
    )
    assert json.loads(approval_path.read_text(encoding="utf-8")) == APPROVAL_RECORD


def test_baseline_approval_fails_closed_on_changed_record() -> None:
    changed = copy.deepcopy(APPROVAL_RECORD)
    changed["rule_count"] = 97
    with pytest.raises(ValueError, match="does not match"):
        verify_approved_baseline(changed)
    changed = copy.deepcopy(APPROVAL_RECORD)
    changed["unexpected"] = True
    with pytest.raises(ValueError, match="unexpected"):
        verify_approved_baseline(changed)
    changed = copy.deepcopy(APPROVAL_RECORD)
    changed["mscp_source_revision"] = "0" * 40
    with pytest.raises(ValueError, match="source revision"):
        verify_approved_baseline(changed)
    changed = copy.deepcopy(APPROVAL_RECORD)
    changed["approval_status"] = "draft"
    with pytest.raises(ValueError, match="not approved"):
        verify_approved_baseline(changed)


@pytest.mark.parametrize(
    ("observed", "expected_outcome"),
    [
        (899, DriftOutcome.ALIGNED),
        (900, DriftOutcome.ALIGNED),
        (901, DriftOutcome.VALUE_DRIFT),
        ("900", DriftOutcome.HUMAN_REVIEW),
        (True, DriftOutcome.HUMAN_REVIEW),
    ],
    ids=("below", "equal", "above", "invalid", "incomparable"),
)
def test_maximum_evaluation_is_numeric_and_inclusive(
    observed: JsonValue, expected_outcome: DriftOutcome
) -> None:
    outcome, returned = _deterministic_outcome(
        {"expected_value": 900, "evaluation_mode": "maximum"},
        [{"properties": {"normalized_value": observed}}],
        [{}],
    )
    assert outcome is expected_outcome
    assert returned == observed


def test_mission_fixture_is_deterministic_private_safe_and_complete() -> None:
    first = build_mission_demo()
    second = build_mission_demo()
    assert first == second
    validate_public_mission_snapshot(first)
    requirements = cast(list[dict[str, JsonValue]], first["requirements"])
    assert len(requirements) == 98
    assert sum(item["evaluation_included"] is True for item in requirements) == 5
    assert cast(dict[str, JsonValue], first["metrics"])["alignment_denominator"] == 5
    assert cast(dict[str, JsonValue], first["devices"])["by_platform"] == {
        "iOS": 1,
        "iPadOS": 1,
        "macOS": 1,
    }
    assert fixture_finding_outcomes(first) == {
        DriftOutcome.VALUE_DRIFT.value,
        DriftOutcome.ASSIGNMENT_DRIFT.value,
        DriftOutcome.CONFLICTING.value,
    }
    serialized = json.dumps(first)
    for private_marker in (
        "synthetic-device-mac",
        "synthetic-policy-filevault",
        '"private_display_name":',
        "source_object_id",
    ):
        assert private_marker not in serialized
    assert first["data_mode"] == "SYNTHETIC DEMO DATA"
    assert first["human_approval_status"] == "Human review required"


def test_ios_is_visible_but_never_scored_against_macos_baseline() -> None:
    snapshot = build_mission_demo()
    requirements = cast(list[dict[str, JsonValue]], snapshot["requirements"])
    assert {item["platform"] for item in requirements} == {"macOS"}
    resources = cast(list[dict[str, JsonValue]], snapshot["resources"])
    assert any("iOS" in cast(list[str], item["platforms"]) for item in resources)
    explanation = cast(dict[str, JsonValue], snapshot["metrics"])[
        "alignment_denominator_explanation"
    ]
    assert "iOS/iPadOS" in cast(str, explanation)


def test_mission_public_validator_rejects_unknown_and_tampered_fields() -> None:
    snapshot = build_mission_demo()
    changed = copy.deepcopy(snapshot)
    changed["tenant_id"] = "private"
    with pytest.raises(ValueError, match="unexpected"):
        validate_public_mission_snapshot(changed)
    changed = copy.deepcopy(snapshot)
    changed["data_mode"] = "live-ish"
    with pytest.raises(ValueError, match="unsupported"):
        validate_public_mission_snapshot(changed)
    changed = copy.deepcopy(snapshot)
    changed["content_fingerprint"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="identity mismatch"):
        validate_public_mission_snapshot(changed)
    changed = copy.deepcopy(snapshot)
    requirement = cast(list[dict[str, JsonValue]], changed["requirements"])[0]
    requirement["unknown_nested"] = True
    unsigned = {
        key: value
        for key, value in changed.items()
        if key not in {"snapshot_id", "content_fingerprint"}
    }
    digest = fingerprint(cast(JsonValue, unsigned))
    changed["content_fingerprint"] = digest
    changed["snapshot_id"] = f"mission-{digest[7:31]}"
    with pytest.raises(ValueError, match="invalid object"):
        validate_public_mission_snapshot(changed)


def test_mission_publication_requires_key_and_omits_private_names() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        build_public_mission_snapshot(
            _collection(previous=False),
            pseudonym_key=b"short",
            synthetic=False,
            source_git_commit="a" * 40,
        )
    live = build_public_mission_snapshot(
        _collection(previous=False),
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=False,
        source_git_commit="a" * 40,
    )
    assert live["data_mode"] == "LIVE SANITIZED TENANT DATA"
    assert "Synthetic macOS" not in json.dumps(live)


def test_private_mission_storage_is_ignored_restrictive_and_validated(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    document = private_collection_document(
        _collection(previous=False), delete_after_utc="2026-07-20T15:00:00Z"
    )
    validate_private_collection(document)
    restored = collection_from_private_document(document)
    assert restored.raw_response_persisted is False
    output = write_private_collection(
        document, directory=root / "artifacts" / "test", repository_root=root
    )
    try:
        assert output.stat().st_mode & 0o777 == 0o600
        assert load_private_collection(output) == document
        with pytest.raises(FileExistsError):
            write_private_collection(
                document, directory=root / "artifacts" / "test", repository_root=root
            )
    finally:
        output.unlink()

    changed = copy.deepcopy(document)
    record = cast(list[dict[str, JsonValue]], changed["records"])[0]
    cast(dict[str, JsonValue], record["properties"])["serialNumber"] = "SERIAL-PRIVATE123"
    with pytest.raises(ValueError, match="prohibited"):
        validate_private_collection(changed)
    changed = copy.deepcopy(document)
    changed["raw_response_persisted"] = True
    with pytest.raises(ValueError, match="never"):
        validate_private_collection(changed)

    outside = tmp_path / "outside"
    with pytest.raises(ValueError, match="inside"):
        write_private_collection(document, directory=outside, repository_root=root)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value.update({"unknown": True}), "unexpected"),
        (lambda value: value.update({"document_type": "wrong"}), "document type"),
        (lambda value: value.update({"records": {}}), "records must be an array"),
        (lambda value: value.update({"endpoint_statuses": {}}), "must be an array"),
        (lambda value: value.update({"retention": {}}), "retention"),
    ],
)
def test_private_collection_envelope_fails_closed(
    mutation: Callable[[dict[str, JsonValue]], None], message: str
) -> None:
    document = private_collection_document(
        _collection(previous=False), delete_after_utc="2026-07-20T15:00:00Z"
    )
    mutation(document)
    with pytest.raises(ValueError, match=message):
        validate_private_collection(document)


def test_private_collection_record_shapes_and_loader_fail_closed(tmp_path: Path) -> None:
    document = private_collection_document(
        _collection(previous=False), delete_after_utc="2026-07-20T15:00:00Z"
    )
    changed = copy.deepcopy(document)
    cast(list[dict[str, JsonValue]], changed["records"])[0]["unknown"] = True
    with pytest.raises(ValueError, match="record has unexpected"):
        validate_private_collection(changed)
    changed = copy.deepcopy(document)
    cast(list[dict[str, JsonValue]], changed["records"])[0]["properties"] = []
    with pytest.raises(ValueError, match="properties"):
        validate_private_collection(changed)
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="could not be read"):
        load_private_collection(invalid)


def test_public_validator_rejects_non_objects_and_bad_arrays() -> None:
    with pytest.raises(ValueError, match="string-keyed"):
        validate_public_mission_snapshot([])
    changed = build_mission_demo()
    changed["requirements"] = {}
    unsigned = {
        key: value
        for key, value in changed.items()
        if key not in {"snapshot_id", "content_fingerprint"}
    }
    digest = fingerprint(cast(JsonValue, unsigned))
    changed["content_fingerprint"] = digest
    changed["snapshot_id"] = f"mission-{digest[7:31]}"
    with pytest.raises(ValueError, match="must be an array"):
        validate_public_mission_snapshot(changed)
