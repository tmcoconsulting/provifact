from __future__ import annotations

import copy
import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from evidenceops.baselines import (
    APPROVAL_RECORD,
    BASELINE_RULE_TITLES,
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
from evidenceops.providers.apple import AppleIntuneCollection


def _requirement_for(snapshot: dict[str, JsonValue], rule_id: str) -> dict[str, JsonValue]:
    return next(
        item
        for item in cast(list[dict[str, JsonValue]], snapshot["requirements"])
        if item["rule_id"] == rule_id
    )


def _without_setting(
    collection: AppleIntuneCollection, definition_id: str
) -> AppleIntuneCollection:
    records = tuple(
        record
        for record in collection.records
        if cast(dict[str, JsonValue], record["properties"]).get("setting_definition_id")
        != definition_id
    )
    return replace(collection, records=records)


def test_pinned_mscp_inventory_and_approval_are_complete() -> None:
    verify_approved_baseline()
    rules = [rule for _, section_rules in BASELINE_RULES for rule in section_rules]
    assert len(rules) == len(set(rules)) == 98
    assert set(BASELINE_RULE_TITLES) == set(rules)
    assert BASELINE_RULE_TITLES["system_settings_filevault_enforce"] == "Enforce FileVault"
    assert BASELINE_RULE_TITLES["audit_auditd_enabled"] == "Enable Security Auditing"
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
    assert sum(item["evaluation_included"] is True for item in requirements) == 4
    assert sum(item["mapping_review_status"] == "reviewed" for item in requirements) == 4
    assert (
        sum(
            item["mapping_review_status"] == "not reviewed" and item["setting_key"] != "not mapped"
            for item in requirements
        )
        == 1
    )
    assert (
        sum(
            item["mapping_review_status"] == "not reviewed" and item["setting_key"] == "not mapped"
            for item in requirements
        )
        == 93
    )
    assert all(
        item["title"] == BASELINE_RULE_TITLES[cast(str, item["rule_id"])] for item in requirements
    )
    assert cast(dict[str, JsonValue], first["metrics"])["alignment_denominator"] == 4
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
    assert len(cast(list[dict[str, JsonValue]], first["findings"])) == 3
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


def test_exact_provider_mappings_recognize_filevault_and_link_public_parent() -> None:
    aligned = build_public_mission_snapshot(
        _collection(previous=True),
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=True,
        source_git_commit="synthetic-reviewed",
    )
    filevault = _requirement_for(aligned, "system_settings_filevault_enforce")
    assert filevault["outcome"] == DriftOutcome.ALIGNED.value
    assert filevault["matched_provider_definition_ids"] == ["com.apple.mcx.filevault2_enable"]
    assert filevault["mapping_review_status"] == "reviewed"
    parent_refs = cast(list[str], filevault["parent_resource_refs"])
    assert len(parent_refs) == 1
    resources = cast(list[dict[str, JsonValue]], aligned["resources"])
    assert any(resource["resource_ref"] == parent_refs[0] for resource in resources)
    assert any(
        resource["parent_resource_ref"] == parent_refs[0]
        and resource["provider_definition_id"] == "com.apple.mcx.filevault2_enable"
        for resource in resources
    )


def test_unknown_provider_setting_is_public_safe_and_not_evaluated_by_guessing() -> None:
    snapshot = build_mission_demo()
    resources = cast(list[dict[str, JsonValue]], snapshot["resources"])
    unknown = next(
        resource
        for resource in resources
        if resource["resource_family"] == "settings_catalog_settings"
        and resource["provider_definition_id"] is None
    )
    assert unknown["evaluation_reason"] == "provider setting not recognized"
    assert unknown["parent_resource_ref"] is not None
    serialized = json.dumps(snapshot)
    assert "com.apple.preference.security_dontAllowFireWallUI" not in serialized


def test_missing_requires_complete_settings_collection() -> None:
    collection = _without_setting(_collection(previous=False), "com.apple.mcx.filevault2_enable")
    snapshot = build_public_mission_snapshot(
        collection,
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=True,
        source_git_commit="synthetic-reviewed",
    )
    assert (
        _requirement_for(snapshot, "system_settings_filevault_enforce")["outcome"]
        == DriftOutcome.MISSING.value
    )

    statuses = list(collection.endpoint_statuses)
    relationship_index = next(
        index
        for index, status in enumerate(statuses)
        if status["key"] == "settings_catalog:settings"
    )
    statuses[relationship_index] = {**statuses[relationship_index], "status": "unavailable"}
    incomplete = replace(collection, endpoint_statuses=tuple(statuses))
    gap_snapshot = build_public_mission_snapshot(
        incomplete,
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=True,
        source_git_commit="synthetic-reviewed",
    )
    assert (
        _requirement_for(gap_snapshot, "system_settings_filevault_enforce")["outcome"]
        == DriftOutcome.COLLECTION_GAP.value
    )


def test_unsupported_value_shape_is_not_reported_as_missing_or_drift() -> None:
    collection = _collection(previous=True)
    records: list[dict[str, JsonValue]] = []
    for original in collection.records:
        record = copy.deepcopy(original)
        properties = cast(dict[str, JsonValue], record["properties"])
        if properties.get("setting_definition_id") == "com.apple.mcx.filevault2_enable":
            properties["normalization_state"] = "unsupported_value_shape"
            properties["normalized_value"] = None
        records.append(record)
    snapshot = build_public_mission_snapshot(
        replace(collection, records=tuple(records)),
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=True,
        source_git_commit="synthetic-reviewed",
    )
    assert (
        _requirement_for(snapshot, "system_settings_filevault_enforce")["outcome"]
        == DriftOutcome.UNSUPPORTED_VALUE_SHAPE.value
    )


def test_current_and_previous_snapshots_classify_new_resolved_and_unchanged() -> None:
    new_drift = build_mission_demo()
    new_changes = cast(dict[str, JsonValue], new_drift["changes"])
    assert new_changes["new_drift"] == [
        "system_settings_filevault_enforce",
        "system_settings_firewall_enable",
        "system_settings_screensaver_password_enforce",
    ]
    assert new_changes["resolved_drift"] == []
    assert len(cast(list[str], new_changes["unchanged_requirements"])) == 95
    assert new_changes["previous_collection_timestamp_utc"] == "2026-07-18T15:00:00Z"
    assert new_changes["current_collection_timestamp_utc"] == "2026-07-19T15:00:00Z"

    prior = build_public_mission_snapshot(
        _collection(previous=False),
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=True,
        source_git_commit="synthetic-reviewed",
    )
    current_collection = replace(
        _collection(previous=True), collected_at_utc="2026-07-20T15:00:00Z"
    )
    resolved = build_public_mission_snapshot(
        current_collection,
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=True,
        source_git_commit="synthetic-reviewed",
        previous=prior,
    )
    resolved_changes = cast(dict[str, JsonValue], resolved["changes"])
    assert resolved_changes["resolved_drift"] == [
        "system_settings_filevault_enforce",
        "system_settings_firewall_enable",
        "system_settings_screensaver_password_enforce",
    ]
    assert resolved_changes["new_drift"] == []
    assert len(cast(list[str], resolved_changes["unchanged_requirements"])) == 95


def test_previous_snapshot_validation_rejects_tampering_private_fields_and_wrong_mode() -> None:
    previous = build_public_mission_snapshot(
        _collection(previous=True),
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=True,
        source_git_commit="synthetic-reviewed",
    )
    current = _collection(previous=False)
    tampered = copy.deepcopy(previous)
    tampered["human_approval_status"] = "Approved"
    with pytest.raises(ValueError, match="identity mismatch"):
        build_public_mission_snapshot(
            current,
            pseudonym_key=MISSION_PSEUDONYM_KEY,
            synthetic=True,
            source_git_commit="synthetic-reviewed",
            previous=tampered,
        )
    private = copy.deepcopy(previous)
    private["private_trace"] = {"source_object_id": "private"}
    with pytest.raises(ValueError, match="unexpected"):
        build_public_mission_snapshot(
            current,
            pseudonym_key=MISSION_PSEUDONYM_KEY,
            synthetic=True,
            source_git_commit="synthetic-reviewed",
            previous=private,
        )
    with pytest.raises(ValueError, match="data mode"):
        build_public_mission_snapshot(
            current,
            pseudonym_key=MISSION_PSEUDONYM_KEY,
            synthetic=False,
            source_git_commit="a" * 40,
            previous=previous,
        )


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

    changed = copy.deepcopy(snapshot)
    cast(dict[str, JsonValue], changed["collection"])["unexpected_private_metadata"] = "x"
    unsigned = {
        key: value
        for key, value in changed.items()
        if key not in {"snapshot_id", "content_fingerprint"}
    }
    digest = fingerprint(cast(JsonValue, unsigned))
    changed["content_fingerprint"] = digest
    changed["snapshot_id"] = f"mission-{digest[7:31]}"
    with pytest.raises(ValueError, match="unexpected or missing"):
        validate_public_mission_snapshot(changed)

    changed = copy.deepcopy(snapshot)
    privacy = cast(dict[str, JsonValue], changed["privacy"])
    cast(dict[str, JsonValue], privacy["redaction_telemetry"])["unknown_counter"] = 1
    unsigned = {
        key: value
        for key, value in changed.items()
        if key not in {"snapshot_id", "content_fingerprint"}
    }
    digest = fingerprint(cast(JsonValue, unsigned))
    changed["content_fingerprint"] = digest
    changed["snapshot_id"] = f"mission-{digest[7:31]}"
    with pytest.raises(ValueError, match="unexpected or missing"):
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
