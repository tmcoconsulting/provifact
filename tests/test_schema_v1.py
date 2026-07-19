from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import cast

import pytest

from evidenceops.demo import build_synthetic_private_package
from evidenceops.domain import (
    EvidenceObject,
    EvidenceSchemaError,
    EvidenceStatus,
    make_evidence_object,
    schema_object_types,
    validate_evidence_object,
)
from evidenceops.evidence import publish_private_package
from evidenceops.narrative import build_offline_narrative, verify_narrative

TEST_KEY = bytes(range(32))


def test_schema_catalog_covers_phase_one_objects() -> None:
    assert set(schema_object_types()) == {
        "collection_metadata",
        "provider_metadata",
        "desired_state_record",
        "normalized_configuration_observation",
        "deterministic_drift_finding",
        "evidence_reference",
        "private_evidence_package",
        "sanitized_public_evidence_package",
        "generated_narrative",
        "narrative_verification_result",
    }


def test_machine_readable_schema_catalog_matches_runtime_catalog() -> None:
    path = Path(__file__).parents[1] / "schemas" / "evidenceops-v1.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert {reference["$ref"].removeprefix("#/$defs/") for reference in schema["oneOf"]} == set(
        schema_object_types()
    )
    assert all(
        schema["$defs"][object_type]["unevaluatedProperties"] is False
        for object_type in schema_object_types()
    )


def test_evidence_identity_is_stable_and_tamper_evident() -> None:
    first = make_evidence_object(
        "provider_metadata",
        {"provider": "synthetic", "provider_version": "1", "source_api_version": "v1"},
    )
    second = make_evidence_object(
        "provider_metadata",
        {"provider": "synthetic", "provider_version": "1", "source_api_version": "v1"},
    )
    assert first == second

    tampered = copy.deepcopy(first)
    tampered["provider_version"] = "2"
    with pytest.raises(EvidenceSchemaError, match="identity mismatch"):
        validate_evidence_object(tampered)


def test_schema_rejects_version_and_unknown_fields() -> None:
    provider = make_evidence_object(
        "provider_metadata",
        {"provider": "synthetic", "provider_version": "1", "source_api_version": "v1"},
    )
    wrong_version = copy.deepcopy(provider)
    wrong_version["schema_version"] = "2.0.0"
    with pytest.raises(EvidenceSchemaError, match="unsupported schema_version"):
        validate_evidence_object(wrong_version)

    unknown = copy.deepcopy(provider)
    unknown["new_vendor_field"] = "must fail closed"
    with pytest.raises(EvidenceSchemaError, match="unexpected fields"):
        validate_evidence_object(unknown, verify_identity=False)


def test_synthetic_flow_covers_all_four_deterministic_states() -> None:
    package = build_synthetic_private_package()
    validate_evidence_object(package)
    findings = cast(list[EvidenceObject], package["findings"])
    statuses = {finding["status"] for finding in findings}
    assert statuses == {
        EvidenceStatus.MATCHES_DESIRED_STATE.value,
        EvidenceStatus.DIFFERS_FROM_DESIRED_STATE.value,
        EvidenceStatus.ADDITIONAL_EVIDENCE_REQUIRED.value,
        EvidenceStatus.NOT_EVALUATED.value,
    }
    for finding in findings:
        assert finding["desired_state_evidence_id"]
        assert finding["collection_evidence_id"]
        assert finding["desired_state_git_commit_sha"] == "synthetic-reviewed-commit"
        assert finding["deterministic_algorithm_version"] == "evidenceops-drift-v1.1.0"
        assert cast(list[str], finding["input_fingerprints"])


def _invalid(document: EvidenceObject, field: str, value: object, match: str) -> None:
    changed = copy.deepcopy(document)
    changed[field] = value  # type: ignore[assignment]
    with pytest.raises(EvidenceSchemaError, match=match):
        validate_evidence_object(changed, verify_identity=False)


def test_schema_factory_and_identity_fail_closed() -> None:
    provider = build_synthetic_private_package()["provider"]
    assert isinstance(provider, dict)
    with pytest.raises(EvidenceSchemaError, match="unsupported object_type"):
        make_evidence_object("future_object", {})
    with pytest.raises(EvidenceSchemaError, match="reserved fields"):
        make_evidence_object("provider_metadata", {"evidence_id": "operator-chosen"})
    with pytest.raises(EvidenceSchemaError, match="string-keyed"):
        validate_evidence_object([])

    _invalid(provider, "object_type", "future_object", "unsupported object_type")
    missing = copy.deepcopy(provider)
    del missing["provider"]
    with pytest.raises(EvidenceSchemaError, match="missing fields"):
        validate_evidence_object(missing, verify_identity=False)
    _invalid(provider, "evidence_id", "invalid", "invalid evidence_id")
    _invalid(provider, "content_fingerprint", "invalid", "invalid content_fingerprint")
    _invalid(provider, "provider", "", "non-empty string")


def test_collection_and_freshness_validation_fail_closed() -> None:
    private = build_synthetic_private_package()
    collection = cast(EvidenceObject, private["collection"])
    _invalid(collection, "collection_timestamp_utc", "not-utc", "ending in Z")
    _invalid(collection, "collection_timestamp_utc", "not-a-dateZ", "ISO-8601")
    _invalid(collection, "provider_evidence_id", "bad-id", "evidence ID")
    _invalid(collection, "desired_state_git_commit_sha", "main", "Git SHA")
    _invalid(collection, "freshness", None, "freshness must be an object")
    _invalid(collection, "freshness", {"state": "current"}, "unexpected or missing")
    _invalid(
        collection,
        "freshness",
        {"as_of_utc": "2026-07-18T18:00:00Z", "max_age_seconds": True, "state": "current"},
        "non-negative integer",
    )
    _invalid(
        collection,
        "freshness",
        {"as_of_utc": "2026-07-18T18:00:00Z", "max_age_seconds": 1, "state": "future"},
        "unsupported",
    )


def test_desired_observation_and_finding_shapes_fail_closed() -> None:
    private = build_synthetic_private_package()
    desired = cast(list[EvidenceObject], private["desired_state"])[0]
    observation = cast(list[EvidenceObject], private["observations"])[0]
    finding = cast(list[EvidenceObject], private["findings"])[0]
    reference = cast(list[EvidenceObject], private["evidence_references"])[0]

    _invalid(desired, "title", None, "non-empty string")
    _invalid(desired, "desired_state_git_commit_sha", 7, "Git SHA")
    _invalid(observation, "collection_evidence_id", "outside", "evidence ID")
    _invalid(observation, "private_trace", "wrong", "must be an object")
    nullable = copy.deepcopy(observation)
    nullable["source_modified_at_utc"] = None
    validate_evidence_object(nullable, verify_identity=False)
    _invalid(finding, "status", "compliant", "unsupported finding status")
    _invalid(finding, "observation_evidence_ids", ["bad"], "only evidence IDs")
    _invalid(finding, "input_fingerprints", ["bad"], "only fingerprints")
    _invalid(finding, "additional_evidence_required", [""], "non-empty strings")
    _invalid(reference, "referenced_evidence_id", "bad", "evidence ID")


def test_package_and_nested_object_validation_fail_closed() -> None:
    private = build_synthetic_private_package()
    public = publish_private_package(
        private, pseudonym_key=TEST_KEY, published_at_utc="2026-07-18T18:00:00Z"
    )
    _invalid(private, "synthetic", "yes", "must be a boolean")
    _invalid(private, "human_approval_status", "approved", "must require human review")
    _invalid(private, "retention", [], "must be an object")
    _invalid(private, "provider", cast(EvidenceObject, private["collection"]), "provider_metadata")
    _invalid(private, "desired_state", {}, "must be an array")
    _invalid(private, "desired_state", [private["provider"]], "desired_state_record")
    _invalid(public, "source_type", "raw-live-export", "unsupported public source_type")
    _invalid(public, "publication", [], "must be an object")


def test_narrative_and_verification_shapes_fail_closed() -> None:
    public = publish_private_package(
        build_synthetic_private_package(),
        pseudonym_key=TEST_KEY,
        published_at_utc="2026-07-18T18:00:00Z",
    )
    narrative = build_offline_narrative(public)
    result = verify_narrative(narrative, public)
    _invalid(narrative, "ai_generated_analysis", False, "ai_generated_analysis")
    _invalid(narrative, "human_review_required", False, "require human review")
    _invalid(narrative, "source_package_evidence_id", "bad", "evidence ID")
    _invalid(narrative, "drift_explanations", {}, "must be an array")
    _invalid(narrative, "drift_explanations", [{}], "unexpected or missing")
    explanations = copy.deepcopy(cast(list[dict[str, object]], narrative["drift_explanations"]))
    explanations[0]["deterministic_status"] = "compliant"
    _invalid(narrative, "drift_explanations", explanations, "status is unsupported")
    _invalid(narrative, "limitations", [], "must not be empty")
    _invalid(result, "accepted", "yes", "must be a boolean")
    _invalid(result, "human_review_required", False, "preserve human review")
