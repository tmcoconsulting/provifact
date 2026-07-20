"""Deterministic Provifact Mission Control evidence and drift model."""

from __future__ import annotations

import hashlib
import hmac
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Final, cast

from evidenceops.baselines import (
    APPROVAL_RECORD,
    BASELINE_RULE_TITLES,
    BASELINE_RULES,
    DEMO_RULE_MAPPINGS,
    INTUNE_PROVIDER_MAPPINGS,
    PROVIDER_MAPPING_REGISTRY_VERSION,
    AssignmentRequirement,
    MappingReviewStatus,
    ProviderRuleMapping,
    UnsupportedProviderValueError,
    matching_alias,
    normalize_provider_definition_id,
    normalize_provider_value,
    reviewed_provider_definition_ids,
)
from evidenceops.domain import JsonValue, canonical_json, fingerprint
from evidenceops.providers.apple import AppleIntuneCollection, summarize_devices
from evidenceops.sanitization import assert_public_safe

MISSION_SCHEMA_VERSION: Final = "2.1.0"
MISSION_ALGORITHM_VERSION: Final = "evidenceops-mission-drift-v2.1.0"
PUBLICATION_POLICY_VERSION: Final = "evidenceops-mission-public-v1.0.0"
FRESHNESS_SECONDS: Final = 86_400
MAX_PUBLIC_MISSION_BYTES: Final = 512 * 1024


class DriftOutcome(StrEnum):
    """Closed deterministic technical evidence outcomes."""

    ALIGNED = "Aligned"
    MISSING = "Missing from tenant"
    VALUE_DRIFT = "Value drift"
    ASSIGNMENT_DRIFT = "Assignment drift"
    CONFLICTING = "Conflicting policy"
    DEVICE_STATE_DRIFT = "Device-state drift"
    COLLECTION_GAP = "Collection gap"
    UNSUPPORTED = "Unsupported by provider"
    PROVIDER_MAPPING_NOT_REVIEWED = "Provider mapping not reviewed"
    UNSUPPORTED_VALUE_SHAPE = "Unsupported value shape"
    NOT_APPLICABLE = "Not applicable"
    HUMAN_REVIEW = "Human review required"


EVALUATED_OUTCOMES: Final = frozenset(
    {
        DriftOutcome.ALIGNED.value,
        DriftOutcome.MISSING.value,
        DriftOutcome.VALUE_DRIFT.value,
        DriftOutcome.ASSIGNMENT_DRIFT.value,
        DriftOutcome.CONFLICTING.value,
        DriftOutcome.DEVICE_STATE_DRIFT.value,
        DriftOutcome.COLLECTION_GAP.value,
        DriftOutcome.HUMAN_REVIEW.value,
    }
)

_TOP_LEVEL_FIELDS: Final = frozenset(
    {
        "schema_version",
        "snapshot_id",
        "content_fingerprint",
        "data_mode",
        "generated_at_utc",
        "collection",
        "baseline",
        "metrics",
        "devices",
        "requirements",
        "findings",
        "resources",
        "unmapped_objects",
        "collection_gaps",
        "changes",
        "framework_coverage",
        "privacy",
        "ai",
        "human_approval_status",
    }
)


def build_public_mission_snapshot(
    collection: AppleIntuneCollection,
    *,
    pseudonym_key: bytes,
    synthetic: bool,
    source_git_commit: str,
    previous: Mapping[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    """Build an allowlisted public/AI-safe artifact from a private collection.

    This is a construction boundary rather than an in-place redactor: only fields
    explicitly copied below can cross it. Unknown private fields are ignored and
    therefore cannot silently become public.
    """
    if len(pseudonym_key) < 32:
        raise ValueError("pseudonym_key must contain at least 32 bytes")
    previous_document = _validated_previous_snapshot(
        previous,
        current_synthetic=synthetic,
        current_collection_timestamp=collection.collected_at_utc,
    )
    requirements, findings, used_evidence_ids = _evaluate_requirements(collection, pseudonym_key)
    resources = _public_resources(collection.records, pseudonym_key, synthetic=synthetic)
    unmapped = [
        resource
        for resource in resources
        if cast(str, resource["source_evidence_id"]) not in used_evidence_ids
        and resource["resource_family"] not in {"managed_devices", "managed_devices_assignments"}
        and not cast(str, resource["resource_family"]).endswith(
            ("_assignments", "_scheduled_actions")
        )
    ]
    gaps = [_public_gap(gap) for gap in collection.collection_gaps]
    device_summary = summarize_devices(collection.records)
    metrics = _metrics(requirements, resources, gaps, unmapped_count=len(unmapped))
    collection_state: dict[str, JsonValue] = {
        "provider": collection.provider,
        "provider_version": collection.provider_version,
        "collected_at_utc": collection.collected_at_utc,
        "freshness": _freshness(collection.collected_at_utc),
        "endpoint_statuses": [dict(item) for item in collection.endpoint_statuses],
        "source_git_commit": source_git_commit,
        "deterministic_algorithm_version": MISSION_ALGORITHM_VERSION,
    }
    baseline = {
        "name": APPROVAL_RECORD["baseline_name"],
        "platform": APPROVAL_RECORD["platform"],
        "benchmark": APPROVAL_RECORD["benchmark"],
        "benchmark_version": APPROVAL_RECORD["benchmark_version"],
        "source_revision": APPROVAL_RECORD["mscp_source_revision"],
        "source_artifact_sha256": APPROVAL_RECORD["source_artifact_sha256"],
        "extracted_baseline_sha256": APPROVAL_RECORD["extracted_baseline_sha256"],
        "approval_status": APPROVAL_RECORD["approval_status"],
        "approver": APPROVAL_RECORD["approver"],
        "approval_date": APPROVAL_RECORD["approval_date"],
        "scope": APPROVAL_RECORD["scope"],
        "limitations": list(cast(list[JsonValue], APPROVAL_RECORD["limitations"])),
        "rule_count": APPROVAL_RECORD["rule_count"],
    }
    unsigned: dict[str, JsonValue] = {
        "schema_version": MISSION_SCHEMA_VERSION,
        "data_mode": "SYNTHETIC DEMO DATA" if synthetic else "LIVE SANITIZED TENANT DATA",
        "generated_at_utc": collection.collected_at_utc,
        "collection": collection_state,
        "baseline": baseline,
        "metrics": metrics,
        "devices": device_summary,
        "requirements": cast(JsonValue, requirements),
        "findings": cast(JsonValue, findings),
        "resources": cast(JsonValue, resources),
        "unmapped_objects": cast(JsonValue, unmapped),
        "collection_gaps": cast(JsonValue, gaps),
        "changes": _changes(
            previous_document,
            requirements,
            metrics,
            current_collection_timestamp=collection.collected_at_utc,
        ),
        "framework_coverage": _framework_coverage(requirements),
        "privacy": {
            "publication_policy_version": PUBLICATION_POLICY_VERSION,
            "allowlist_validation": "passed",
            "raw_response_persisted": False,
            "identifiers_public": False,
            "openai_egress_class": "same sanitized evidence package only",
            "redaction_telemetry": {
                "source_identifiers_pseudonymized": len(resources),
                "private_display_names_omitted": sum(
                    1
                    for record in collection.records
                    if "private_display_name" in cast(dict[str, JsonValue], record["properties"])
                ),
            },
        },
        "ai": {
            "model": "gpt-5.6-terra",
            "mode": "fixture",
            "authoritative": False,
            "output_label": "AI-generated analysis — human review required",
            "verifier_required": True,
            "insufficient_evidence_response": (
                "Provifact does not have sufficient collected evidence to answer this question."
            ),
        },
        "human_approval_status": "Human review required",
    }
    digest = fingerprint(unsigned)
    snapshot: dict[str, JsonValue] = {
        **unsigned,
        "snapshot_id": f"mission-{digest[7:31]}",
        "content_fingerprint": digest,
    }
    validate_public_mission_snapshot(snapshot)
    assert_public_safe(cast(JsonValue, snapshot))
    return snapshot


def validate_public_mission_snapshot(value: object) -> dict[str, JsonValue]:
    """Strictly validate a Mission Control public artifact and its fingerprint."""
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("mission snapshot must be a string-keyed object")
    document = cast(dict[str, JsonValue], value)
    if set(document) != _TOP_LEVEL_FIELDS:
        raise ValueError("mission snapshot has unexpected or missing top-level fields")
    if document["schema_version"] != MISSION_SCHEMA_VERSION:
        raise ValueError("unsupported mission snapshot schema version")
    data_mode = document["data_mode"]
    if data_mode not in {
        "SYNTHETIC DEMO DATA",
        "LIVE SANITIZED TENANT DATA",
        "DEGRADED OR STALE DATA",
    }:
        raise ValueError("unsupported mission snapshot data mode")
    snapshot_id = document["snapshot_id"]
    digest = document["content_fingerprint"]
    if not isinstance(snapshot_id, str) or not snapshot_id.startswith("mission-"):
        raise ValueError("invalid mission snapshot ID")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise ValueError("invalid mission snapshot fingerprint")
    unsigned = {
        key: item
        for key, item in document.items()
        if key not in {"snapshot_id", "content_fingerprint"}
    }
    expected = fingerprint(cast(JsonValue, unsigned))
    if digest != expected or snapshot_id != f"mission-{expected[7:31]}":
        raise ValueError("mission snapshot identity mismatch")
    _exact_list_items(document, "requirements", _requirement_fields())
    _exact_list_items(document, "findings", _finding_fields())
    _exact_list_items(document, "resources", _resource_fields())
    _exact_list_items(document, "unmapped_objects", _resource_fields())
    _exact_list_items(document, "collection_gaps", _gap_fields())
    _validate_nested_public_objects(document)
    assert_public_safe(cast(JsonValue, document))
    return document


def load_public_mission_snapshot(path: Path, *, require_live: bool = False) -> dict[str, JsonValue]:
    """Load one bounded public snapshot without accepting links or private envelopes."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("previous public Mission snapshot must be one regular file")
    if path.stat().st_size > MAX_PUBLIC_MISSION_BYTES:
        raise ValueError("previous public Mission snapshot exceeds the package limit")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("previous public Mission snapshot could not be read") from exc
    validated = validate_public_mission_snapshot(loaded)
    if require_live and validated["data_mode"] != "LIVE SANITIZED TENANT DATA":
        raise ValueError("previous public Mission snapshot must contain live sanitized data")
    return validated


def _evaluate_requirements(
    collection: AppleIntuneCollection,
    pseudonym_key: bytes,
) -> tuple[list[dict[str, JsonValue]], list[dict[str, JsonValue]], set[str]]:
    requirements: list[dict[str, JsonValue]] = []
    findings: list[dict[str, JsonValue]] = []
    used: set[str] = set()
    setting_records = [
        record
        for record in collection.records
        if record["resource_family"] == "settings_catalog_settings"
    ]
    assignments = [
        record
        for record in collection.records
        if cast(str, record["resource_family"]).endswith("_assignments")
    ]
    parents_by_evidence_id = {
        cast(str, record["evidence_id"]): record
        for record in collection.records
        if not cast(str, record["resource_family"]).endswith(
            ("_assignments", "_settings", "_scheduled_actions")
        )
    }
    for ordinal, (section, rule_id) in enumerate(
        ((section, rule_id) for section, rules in BASELINE_RULES for rule_id in rules),
        start=1,
    ):
        desired_mapping = DEMO_RULE_MAPPINGS.get(rule_id)
        provider_mapping = INTUNE_PROVIDER_MAPPINGS.get(rule_id)
        if (
            desired_mapping is None
            or provider_mapping is None
            or provider_mapping.review_status is not MappingReviewStatus.REVIEWED
        ):
            requirement = _requirement(
                ordinal=ordinal,
                section=section,
                rule_id=rule_id,
                title=BASELINE_RULE_TITLES[rule_id],
                expected=(
                    desired_mapping["expected_value"]
                    if desired_mapping is not None
                    else "not evaluated"
                ),
                outcome=DriftOutcome.PROVIDER_MAPPING_NOT_REVIEWED,
                severity="informational",
                mappings={},
                evidence_ids=[],
                assignment_summary="not evaluated",
                observed="not evaluated",
                setting_key=(
                    cast(str, desired_mapping["setting_key"])
                    if desired_mapping is not None
                    else "not mapped"
                ),
                provider_definition_ids=[],
                matched_provider_definition_ids=[],
                parent_resource_refs=[],
                mapping_review_status=MappingReviewStatus.NOT_REVIEWED.value,
            )
            requirements.append(requirement)
            continue
        candidates = _matching_settings(setting_records, provider_mapping)
        parent_ids = {
            cast(str, cast(dict[str, JsonValue], item["properties"])["parent_evidence_id"])
            for item in candidates
        }
        related_assignments = [
            item
            for item in assignments
            if cast(dict[str, JsonValue], item["properties"]).get("parent_evidence_id")
            in parent_ids
        ]
        evidence_ids = [
            cast(str, item["evidence_id"]) for item in [*candidates, *related_assignments]
        ]
        used.update(evidence_ids)
        used.update(parent_ids)
        outcome: DriftOutcome
        observed: JsonValue
        if not candidates and not _settings_catalog_is_complete(collection):
            outcome, observed = DriftOutcome.COLLECTION_GAP, "collection incomplete"
        else:
            outcome, observed = _deterministic_outcome(
                desired_mapping,
                candidates,
                related_assignments,
                provider_mapping=provider_mapping,
            )
        assignment_summary = (
            f"{len(related_assignments)} normalized assignment(s)"
            if related_assignments
            else "no normalized assignment observed"
        )
        parent_refs = sorted(
            _pseudonym(
                "resource",
                cast(str, parents_by_evidence_id[parent_id]["source_object_id"]),
                pseudonym_key,
            )
            for parent_id in parent_ids
            if parent_id in parents_by_evidence_id
        )
        matched_definition_ids = sorted(
            {
                cast(
                    str,
                    cast(dict[str, JsonValue], item["properties"])["setting_definition_id"],
                )
                for item in candidates
            },
            key=str.casefold,
        )
        requirement = _requirement(
            ordinal=ordinal,
            section=section,
            rule_id=rule_id,
            title=cast(str, desired_mapping["title"]),
            expected=desired_mapping["expected_value"],
            outcome=outcome,
            severity=cast(str, desired_mapping["severity"]),
            mappings={
                key: desired_mapping[key]
                for key in (
                    "cis_benchmark",
                    "nist_800_53r5",
                    "nist_800_171r3",
                    "stig",
                    "cmmc",
                )
            },
            evidence_ids=evidence_ids,
            assignment_summary=assignment_summary,
            observed=observed,
            setting_key=provider_mapping.setting_key,
            provider_definition_ids=[alias.definition_id for alias in provider_mapping.aliases],
            matched_provider_definition_ids=matched_definition_ids,
            parent_resource_refs=parent_refs,
            mapping_review_status=provider_mapping.review_status.value,
        )
        requirements.append(requirement)
        if outcome is not DriftOutcome.ALIGNED:
            findings.append(_finding(requirement, collection.collected_at_utc))
    return requirements, findings, used


def _matching_settings(
    records: Sequence[dict[str, JsonValue]], mapping: ProviderRuleMapping
) -> list[dict[str, JsonValue]]:
    matches: list[dict[str, JsonValue]] = []
    for record in records:
        properties = cast(dict[str, JsonValue], record["properties"])
        definition = cast(str, properties["setting_definition_id"])
        if matching_alias(mapping, definition) is not None:
            matches.append(record)
    return sorted(matches, key=lambda item: cast(str, item["evidence_id"]))


def _deterministic_outcome(
    mapping: Mapping[str, JsonValue],
    settings: Sequence[dict[str, JsonValue]],
    assignments: Sequence[dict[str, JsonValue]],
    *,
    provider_mapping: ProviderRuleMapping | None = None,
) -> tuple[DriftOutcome, JsonValue]:
    if not settings:
        return DriftOutcome.MISSING, "not observed"
    values: list[JsonValue] = []
    for item in settings:
        properties = cast(dict[str, JsonValue], item["properties"])
        if properties.get("normalization_state", "normalized") != "normalized":
            return DriftOutcome.UNSUPPORTED_VALUE_SHAPE, "unsupported value shape"
        value = properties["normalized_value"]
        if provider_mapping is not None:
            alias = matching_alias(provider_mapping, cast(str, properties["setting_definition_id"]))
            if alias is None:  # pragma: no cover - exact matcher selected these records
                raise AssertionError("provider setting lost its exact mapping")
            try:
                value = normalize_provider_value(alias, value)
            except UnsupportedProviderValueError:
                return DriftOutcome.UNSUPPORTED_VALUE_SHAPE, "unsupported value shape"
        values.append(value)
    canonical_values = {canonical_json(value) for value in values}
    if len(canonical_values) > 1:
        return DriftOutcome.CONFLICTING, cast(JsonValue, sorted(canonical_values))
    observed = values[0]
    expected = mapping["expected_value"]
    if mapping.get("evaluation_mode") == "maximum":
        if not _finite_number(expected) or not _finite_number(observed):
            return DriftOutcome.HUMAN_REVIEW, observed
        if cast(float, observed) > cast(float, expected):
            return DriftOutcome.VALUE_DRIFT, observed
    elif observed != expected:
        return DriftOutcome.VALUE_DRIFT, observed
    if (
        provider_mapping is None
        or provider_mapping.assignment_requirement is AssignmentRequirement.AT_LEAST_ONE
    ) and not assignments:
        return DriftOutcome.ASSIGNMENT_DRIFT, observed
    return DriftOutcome.ALIGNED, observed


def _requirement(
    *,
    ordinal: int,
    section: str,
    rule_id: str,
    title: str,
    expected: JsonValue,
    outcome: DriftOutcome,
    severity: str,
    mappings: Mapping[str, JsonValue],
    evidence_ids: Sequence[str],
    assignment_summary: str,
    observed: JsonValue,
    setting_key: str,
    provider_definition_ids: Sequence[str],
    matched_provider_definition_ids: Sequence[str],
    parent_resource_refs: Sequence[str],
    mapping_review_status: str,
) -> dict[str, JsonValue]:
    unsigned: dict[str, JsonValue] = {
        "ordinal": ordinal,
        "rule_id": rule_id,
        "title": title,
        "section": section,
        "platform": "macOS",
        "expected_value": expected,
        "observed_value": observed,
        "outcome": outcome.value,
        "severity": severity,
        "evaluation_included": outcome.value in EVALUATED_OUTCOMES,
        "assignment_summary": assignment_summary,
        "setting_key": setting_key,
        "provider_definition_ids": list(provider_definition_ids),
        "matched_provider_definition_ids": list(matched_provider_definition_ids),
        "parent_resource_refs": list(parent_resource_refs),
        "provider_mapping_registry_version": PROVIDER_MAPPING_REGISTRY_VERSION,
        "mapping_review_status": mapping_review_status,
        "mappings": dict(mappings),
        "source_evidence_ids": list(evidence_ids),
        "additional_evidence_required": outcome is not DriftOutcome.ALIGNED,
    }
    digest = fingerprint(unsigned)
    return {
        **unsigned,
        "requirement_id": f"req-{digest[7:31]}",
        "fingerprint": digest,
    }


def _finding(
    requirement: Mapping[str, JsonValue],
    observed_at: str,
) -> dict[str, JsonValue]:
    outcome = cast(str, requirement["outcome"])
    recommendations = {
        DriftOutcome.MISSING.value: (
            "Review whether an approved Intune policy should express this requirement."
        ),
        DriftOutcome.VALUE_DRIFT.value: (
            "Review the observed value against approved desired state before changing Intune."
        ),
        DriftOutcome.ASSIGNMENT_DRIFT.value: (
            "Review assignment scope and exclusions; Provifact cannot assign policies."
        ),
        DriftOutcome.CONFLICTING.value: (
            "Review overlapping policies and effective precedence with an endpoint administrator."
        ),
        DriftOutcome.COLLECTION_GAP.value: (
            "Restore read-only evidence collection or provide alternate evidence."
        ),
        DriftOutcome.UNSUPPORTED_VALUE_SHAPE.value: (
            "Review the provider value shape before adding a deterministic transform."
        ),
        DriftOutcome.HUMAN_REVIEW.value: (
            "Have a qualified reviewer evaluate the ambiguous evidence."
        ),
    }
    unsigned: dict[str, JsonValue] = {
        "requirement_id": requirement["requirement_id"],
        "rule_id": requirement["rule_id"],
        "title": requirement["title"],
        "platform": "macOS",
        "drift_type": outcome,
        "severity": requirement["severity"],
        "expected_value": requirement["expected_value"],
        "observed_value": requirement["observed_value"],
        "assignment_summary": requirement["assignment_summary"],
        "affected_device_count": None,
        "source_evidence_ids": requirement["source_evidence_ids"],
        "mapped_controls": requirement["mappings"],
        "additional_evidence_required": True,
        "observed_at_utc": observed_at,
        "baseline_rule_fingerprint": requirement["fingerprint"],
        "remediation_guidance": recommendations.get(
            outcome,
            "Human review is required; Provifact has no Intune write or remediation capability.",
        ),
        "limitations": [
            "Technical evidence does not establish organizational compliance.",
            "No Intune write or automatic remediation operation exists.",
        ],
        "setting_key": requirement["setting_key"],
        "provider_definition_ids": requirement["provider_definition_ids"],
        "matched_provider_definition_ids": requirement["matched_provider_definition_ids"],
        "parent_resource_refs": requirement["parent_resource_refs"],
        "provider_mapping_registry_version": requirement["provider_mapping_registry_version"],
        "mapping_review_status": requirement["mapping_review_status"],
    }
    digest = fingerprint(unsigned)
    return {**unsigned, "finding_id": f"finding-{digest[7:31]}", "fingerprint": digest}


def _settings_catalog_is_complete(collection: AppleIntuneCollection) -> bool:
    """Return true only when absence can be distinguished from a collection gap."""
    root_statuses = [
        item for item in collection.endpoint_statuses if item.get("key") == "settings-catalog"
    ]
    if len(root_statuses) != 1 or root_statuses[0].get("status") != "collected":
        return False
    relevant_gaps = [
        gap
        for gap in collection.collection_gaps
        if gap.get("source_endpoint_key") in {"settings-catalog", "settings_catalog:settings"}
    ]
    if relevant_gaps:
        return False
    parent_count = sum(
        record["resource_family"] == "settings_catalog" for record in collection.records
    )
    relationship_statuses = [
        item
        for item in collection.endpoint_statuses
        if item.get("key") == "settings_catalog:settings"
    ]
    if parent_count == 0:
        return True
    return len(relationship_statuses) == parent_count and all(
        item.get("status") == "collected" for item in relationship_statuses
    )


def _public_resources(
    records: Sequence[dict[str, JsonValue]], pseudonym_key: bytes, *, synthetic: bool
) -> list[dict[str, JsonValue]]:
    result: list[dict[str, JsonValue]] = []
    parent_resource_refs = {
        cast(str, record["evidence_id"]): _pseudonym(
            "resource", cast(str, record["source_object_id"]), pseudonym_key
        )
        for record in records
        if not cast(str, record["resource_family"]).endswith(
            ("_assignments", "_settings", "_scheduled_actions")
        )
    }
    reviewed_ids = reviewed_provider_definition_ids()
    for record in records:
        if record["resource_family"] == "managed_devices":
            continue
        properties = cast(dict[str, JsonValue], record["properties"])
        resource_ref = _pseudonym("resource", cast(str, record["source_object_id"]), pseudonym_key)
        platforms = properties.get("platforms", ["unknown"])
        safe_state = next(
            (properties[key] for key in ("state", "status", "token_state") if key in properties),
            "observed",
        )
        title = (
            cast(str, properties["private_display_name"])
            if synthetic
            and str(properties.get("private_display_name", "")).startswith("Synthetic ")
            else f"{str(record['resource_family']).replace('_', ' ').title()} {resource_ref[-6:]}"
        )
        assignment_count = sum(
            1
            for candidate in records
            if cast(str, candidate["resource_family"]).endswith("_assignments")
            and cast(dict[str, JsonValue], candidate["properties"]).get("parent_evidence_id")
            == record["evidence_id"]
        )
        parent_evidence_id = properties.get("parent_evidence_id")
        parent_resource_ref = (
            parent_resource_refs.get(parent_evidence_id)
            if isinstance(parent_evidence_id, str)
            else None
        )
        provider_definition_id: str | None = None
        definition = properties.get("setting_definition_id")
        if isinstance(definition, str):
            try:
                known_definition = normalize_provider_definition_id(definition) in reviewed_ids
            except ValueError:
                known_definition = False
            if known_definition:
                provider_definition_id = definition
        evaluation_reason, action_expected = _resource_evaluation_classification(
            record, provider_definition_id=provider_definition_id
        )
        result.append(
            {
                "resource_ref": resource_ref,
                "source_evidence_id": record["evidence_id"],
                "resource_family": record["resource_family"],
                "title": title,
                "platforms": platforms,
                "resource_type": properties.get("odata_type", "normalized relationship"),
                "assignment_count": assignment_count,
                "state": safe_state,
                "source_api_version": record["source_api_version"],
                "fingerprint": record["content_fingerprint"],
                "parent_resource_ref": parent_resource_ref,
                "provider_definition_id": provider_definition_id,
                "evaluation_reason": evaluation_reason,
                "action_expected": action_expected,
            }
        )
    return sorted(
        result,
        key=lambda item: (cast(str, item["resource_family"]), cast(str, item["resource_ref"])),
    )


def _resource_evaluation_classification(
    record: Mapping[str, JsonValue], *, provider_definition_id: str | None
) -> tuple[str, str]:
    family = cast(str, record["resource_family"])
    properties = cast(dict[str, JsonValue], record["properties"])
    platforms = properties.get("platforms", [])
    if family == "settings_catalog_settings":
        if properties.get("normalization_state") == "unsupported_value_shape":
            return (
                "unsupported value shape",
                "Review provider shape before adding deterministic evaluation.",
            )
        if provider_definition_id is None:
            return (
                "provider setting not recognized",
                "Review and approve an exact provider mapping before evaluation.",
            )
        return "collected setting not currently evaluated", "No configuration action inferred."
    if isinstance(platforms, list) and "macOS" not in platforms:
        return "platform baseline not loaded", "No action for the current macOS baseline."
    if family.endswith(("_assignments", "_scheduled_actions")):
        return (
            "supporting tenant service or inventory only",
            "Review only with its parent resource.",
        )
    if family in {"configuration_profiles", "settings_catalog", "compliance_policies"}:
        return (
            "provider mapping not reviewed",
            "Review exact provider settings before deterministic evaluation.",
        )
    return (
        "supporting tenant service or inventory only",
        "No posture action is inferred from inventory alone.",
    )


def _public_gap(gap: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    return {
        "gap_id": gap["gap_id"],
        "resource_family": gap["resource_family"],
        "source_endpoint_key": gap["source_endpoint_key"],
        "source_api_version": gap["source_api_version"],
        "required_permission": gap["required_permission"],
        "reason": gap["reason"],
        "http_status": gap["http_status"],
        "additional_evidence_required": True,
    }


def _metrics(
    requirements: Sequence[dict[str, JsonValue]],
    resources: Sequence[dict[str, JsonValue]],
    gaps: Sequence[dict[str, JsonValue]],
    *,
    unmapped_count: int,
) -> dict[str, JsonValue]:
    evaluated = [item for item in requirements if item["evaluation_included"] is True]
    aligned = sum(item["outcome"] == DriftOutcome.ALIGNED.value for item in evaluated)
    alignment_value = round((aligned / len(evaluated) * 100), 1) if evaluated else 0.0
    alignment: int | float = (
        int(alignment_value) if alignment_value.is_integer() else alignment_value
    )
    outcomes = Counter(cast(str, item["outcome"]) for item in evaluated)
    return {
        "alignment_percent": alignment,
        "alignment_denominator": len(evaluated),
        "alignment_denominator_explanation": (
            "Only reviewed exact macOS provider joins enter this denominator. The other approved "
            "rules remain visible as implementation work; iOS/iPadOS are outside the macOS scope."
        ),
        "aligned_requirements": aligned,
        "drifted_requirements": len(evaluated) - aligned,
        "high_severity_drift": sum(
            item["severity"] == "high" and item["outcome"] != DriftOutcome.ALIGNED.value
            for item in evaluated
        ),
        "baseline_rule_count": len(requirements),
        "policies_evaluated": sum(
            item["resource_family"]
            in {"configuration_profiles", "settings_catalog", "compliance_policies"}
            for item in resources
        ),
        "unmapped_objects": unmapped_count,
        "collection_gaps": len(gaps),
        "outcome_counts": dict(sorted(outcomes.items())),
    }


def _changes(
    previous: Mapping[str, JsonValue] | None,
    requirements: Sequence[dict[str, JsonValue]],
    metrics: Mapping[str, JsonValue],
    *,
    current_collection_timestamp: str,
) -> dict[str, JsonValue]:
    current = {cast(str, item["rule_id"]): cast(str, item["outcome"]) for item in requirements}
    if previous is None:
        return {
            "previous_snapshot_id": None,
            "alignment_change_points": None,
            "new_drift": [],
            "resolved_drift": [],
            "changed_requirements": [],
            "unchanged_requirements": [],
            "previous_collection_timestamp_utc": None,
            "current_collection_timestamp_utc": current_collection_timestamp,
            "history_state": "no previous collection",
        }
    previous_requirements = cast(list[dict[str, JsonValue]], previous.get("requirements", []))
    old = {cast(str, item["rule_id"]): cast(str, item["outcome"]) for item in previous_requirements}
    changed = sorted(rule for rule, outcome in current.items() if old.get(rule) != outcome)
    unchanged = sorted(rule for rule, outcome in current.items() if old.get(rule) == outcome)
    new_drift = sorted(
        rule
        for rule in changed
        if current[rule] != DriftOutcome.ALIGNED.value
        and old.get(rule) == DriftOutcome.ALIGNED.value
    )
    resolved = sorted(
        rule
        for rule in changed
        if current[rule] == DriftOutcome.ALIGNED.value
        and old.get(rule) not in {None, DriftOutcome.ALIGNED.value}
    )
    old_metrics = cast(dict[str, JsonValue], previous.get("metrics", {}))
    old_alignment = old_metrics.get("alignment_percent")
    alignment_change: float | None = None
    if isinstance(old_alignment, (int, float)) and not isinstance(old_alignment, bool):
        change = round(cast(float, metrics["alignment_percent"]) - old_alignment, 1)
        alignment_change = int(change) if change.is_integer() else change
    return {
        "previous_snapshot_id": previous.get("snapshot_id"),
        "alignment_change_points": alignment_change,
        "new_drift": cast(JsonValue, new_drift),
        "resolved_drift": cast(JsonValue, resolved),
        "changed_requirements": cast(JsonValue, changed),
        "unchanged_requirements": cast(JsonValue, unchanged),
        "previous_collection_timestamp_utc": cast(dict[str, JsonValue], previous["collection"])[
            "collected_at_utc"
        ],
        "current_collection_timestamp_utc": current_collection_timestamp,
        "history_state": "compared",
    }


def _validated_previous_snapshot(
    previous: Mapping[str, JsonValue] | None,
    *,
    current_synthetic: bool,
    current_collection_timestamp: str,
) -> dict[str, JsonValue] | None:
    if previous is None:
        return None
    validated = validate_public_mission_snapshot(previous)
    expected_mode = "SYNTHETIC DEMO DATA" if current_synthetic else "LIVE SANITIZED TENANT DATA"
    if validated["data_mode"] != expected_mode:
        raise ValueError("previous Mission snapshot data mode does not match the current package")
    previous_collection = cast(dict[str, JsonValue], validated["collection"])
    previous_timestamp = cast(str, previous_collection["collected_at_utc"])
    if _parse_utc(previous_timestamp) >= _parse_utc(current_collection_timestamp):
        raise ValueError("previous Mission snapshot must predate the current collection")
    previous_baseline = cast(dict[str, JsonValue], validated["baseline"])
    if (
        previous_baseline["source_revision"] != APPROVAL_RECORD["mscp_source_revision"]
        or previous_baseline["extracted_baseline_sha256"]
        != APPROVAL_RECORD["extracted_baseline_sha256"]
    ):
        raise ValueError("previous Mission snapshot uses a different approved baseline")
    return validated


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Mission collection timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError("Mission collection timestamp must include a UTC offset")
    return parsed.astimezone(UTC)


def _framework_coverage(requirements: Sequence[dict[str, JsonValue]]) -> dict[str, JsonValue]:
    frameworks = {
        "CIS benchmark": "cis_benchmark",
        "STIG": "stig",
        "NIST SP 800-171": "nist_800_171r3",
        "NIST SP 800-53": "nist_800_53r5",
        "CMMC": "cmmc",
    }
    result: dict[str, JsonValue] = {}
    for label, key in frameworks.items():
        identifiers: set[str] = set()
        for requirement in requirements:
            mappings = cast(dict[str, JsonValue], requirement["mappings"])
            values = mappings.get(key, [])
            if isinstance(values, list):
                identifiers.update(cast(list[str], values))
        result[label] = {
            "technical_evidence_identifier_count": len(identifiers),
            "identifiers": cast(JsonValue, sorted(identifiers)),
            "assessment_conclusion": "not evaluated",
        }
    return result


def _freshness(collected_at: str) -> dict[str, JsonValue]:
    """Record freshness at deterministic package-build time.

    A Mission snapshot is built immediately after its source collection. The
    browser and Worker derive current staleness from ``collected_at_utc`` rather
    than mutating the signed artifact.
    """
    parsed = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
    if parsed.utcoffset() is None or parsed.astimezone(UTC).utcoffset() is None:
        raise ValueError("collection timestamp must be timezone-aware")
    return {
        "age_seconds_at_build": 0,
        "maximum_age_seconds": FRESHNESS_SECONDS,
        "state": "current",
    }


def _pseudonym(prefix: str, value: str, key: bytes) -> str:
    digest = hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _finite_number(value: JsonValue) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _exact_list_items(
    document: Mapping[str, JsonValue], field: str, expected: frozenset[str]
) -> None:
    values = document.get(field)
    if not isinstance(values, list):
        raise ValueError(f"mission field {field} must be an array")
    if any(not isinstance(item, dict) or set(item) != expected for item in values):
        raise ValueError(f"mission field {field} contains an invalid object")


def _validate_nested_public_objects(document: Mapping[str, JsonValue]) -> None:
    collection = _exact_object(
        document,
        "collection",
        {
            "provider",
            "provider_version",
            "collected_at_utc",
            "freshness",
            "endpoint_statuses",
            "source_git_commit",
            "deterministic_algorithm_version",
        },
    )
    _exact_object(
        collection,
        "freshness",
        {"age_seconds_at_build", "maximum_age_seconds", "state"},
    )
    statuses = collection["endpoint_statuses"]
    if not isinstance(statuses, list):
        raise ValueError("mission collection endpoint_statuses must be an array")
    endpoint_fields = {
        "key",
        "record_count",
        "required_permission",
        "resource_family",
        "source_api_version",
        "status",
    }
    if any(
        not isinstance(item, dict)
        or not endpoint_fields.issubset(item)
        or not set(item).issubset(endpoint_fields | {"beta_reason"})
        for item in statuses
    ):
        raise ValueError("mission collection contains an invalid endpoint status")
    _exact_object(
        document,
        "baseline",
        {
            "name",
            "platform",
            "benchmark",
            "benchmark_version",
            "source_revision",
            "source_artifact_sha256",
            "extracted_baseline_sha256",
            "approval_status",
            "approver",
            "approval_date",
            "scope",
            "limitations",
            "rule_count",
        },
    )
    _exact_object(
        document,
        "metrics",
        {
            "alignment_percent",
            "alignment_denominator",
            "alignment_denominator_explanation",
            "aligned_requirements",
            "drifted_requirements",
            "high_severity_drift",
            "baseline_rule_count",
            "policies_evaluated",
            "unmapped_objects",
            "collection_gaps",
            "outcome_counts",
        },
    )
    devices = _exact_object(
        document,
        "devices",
        {
            "total",
            "by_platform",
            "by_compliance_state",
            "by_encryption_state",
            "by_supervision_state",
        },
    )
    for field in (
        "by_platform",
        "by_compliance_state",
        "by_encryption_state",
        "by_supervision_state",
    ):
        if not isinstance(devices[field], dict):
            raise ValueError(f"mission device field {field} must be an object")
    _exact_object(
        document,
        "changes",
        {
            "previous_snapshot_id",
            "alignment_change_points",
            "new_drift",
            "resolved_drift",
            "changed_requirements",
            "unchanged_requirements",
            "previous_collection_timestamp_utc",
            "current_collection_timestamp_utc",
            "history_state",
        },
    )
    frameworks = _exact_object(
        document,
        "framework_coverage",
        {"CIS benchmark", "STIG", "NIST SP 800-171", "NIST SP 800-53", "CMMC"},
    )
    for field in frameworks:
        _exact_object(
            frameworks,
            field,
            {"technical_evidence_identifier_count", "identifiers", "assessment_conclusion"},
        )
    privacy = _exact_object(
        document,
        "privacy",
        {
            "publication_policy_version",
            "allowlist_validation",
            "raw_response_persisted",
            "identifiers_public",
            "openai_egress_class",
            "redaction_telemetry",
        },
    )
    _exact_object(
        privacy,
        "redaction_telemetry",
        {"source_identifiers_pseudonymized", "private_display_names_omitted"},
    )
    _exact_object(
        document,
        "ai",
        {
            "model",
            "mode",
            "authoritative",
            "output_label",
            "verifier_required",
            "insufficient_evidence_response",
        },
    )
    allowed_mapping_fields = {
        "cis_benchmark",
        "nist_800_53r5",
        "nist_800_171r3",
        "stig",
        "cmmc",
    }
    for list_field, mapping_field in (
        ("requirements", "mappings"),
        ("findings", "mapped_controls"),
    ):
        values = cast(list[dict[str, JsonValue]], document[list_field])
        if any(
            not isinstance(item[mapping_field], dict)
            or not set(cast(dict[str, JsonValue], item[mapping_field])).issubset(
                allowed_mapping_fields
            )
            for item in values
        ):
            raise ValueError(f"mission field {list_field} contains an invalid mapping")
    _validate_mission_semantics(document)


def _validate_mission_semantics(document: Mapping[str, JsonValue]) -> None:
    requirements = cast(list[dict[str, JsonValue]], document["requirements"])
    rule_ids = [cast(str, item["rule_id"]) for item in requirements]
    if len(rule_ids) != len(set(rule_ids)) or len(rule_ids) != 98:
        raise ValueError("mission requirements must contain 98 unique baseline rules")
    allowed_outcomes = {item.value for item in DriftOutcome}
    for item in requirements:
        if item["outcome"] not in allowed_outcomes:
            raise ValueError("mission requirement has an unsupported outcome")
        if item["mapping_review_status"] not in {
            MappingReviewStatus.REVIEWED.value,
            MappingReviewStatus.NOT_REVIEWED.value,
        }:
            raise ValueError("mission requirement has an invalid mapping review status")
        for field in (
            "provider_definition_ids",
            "matched_provider_definition_ids",
            "parent_resource_refs",
            "source_evidence_ids",
        ):
            value = item[field]
            if not isinstance(value, list) or not all(isinstance(entry, str) for entry in value):
                raise ValueError(f"mission requirement field {field} must be a string array")
        configured = {
            normalize_provider_definition_id(value)
            for value in cast(list[str], item["provider_definition_ids"])
        }
        matched = {
            normalize_provider_definition_id(value)
            for value in cast(list[str], item["matched_provider_definition_ids"])
        }
        if not matched.issubset(configured):
            raise ValueError("mission requirement matched an unreviewed provider definition")
    resources = cast(list[dict[str, JsonValue]], document["resources"])
    resource_refs = {cast(str, item["resource_ref"]) for item in resources}
    for item in resources:
        parent = item["parent_resource_ref"]
        if parent is not None and (not isinstance(parent, str) or parent not in resource_refs):
            raise ValueError("mission resource has an invalid public parent link")
        provider_id = item["provider_definition_id"]
        if provider_id is not None and (
            not isinstance(provider_id, str)
            or normalize_provider_definition_id(provider_id)
            not in reviewed_provider_definition_ids()
        ):
            raise ValueError("mission resource exposed an unreviewed provider definition")
    changes = cast(dict[str, JsonValue], document["changes"])
    for field in (
        "new_drift",
        "resolved_drift",
        "changed_requirements",
        "unchanged_requirements",
    ):
        value = changes[field]
        if not isinstance(value, list) or not all(isinstance(entry, str) for entry in value):
            raise ValueError(f"mission changes field {field} must be a string array")
        if not set(cast(list[str], value)).issubset(rule_ids):
            raise ValueError(f"mission changes field {field} references an unknown rule")
    changed = set(cast(list[str], changes["changed_requirements"]))
    unchanged = set(cast(list[str], changes["unchanged_requirements"]))
    if changes["history_state"] == "compared":
        if changed.intersection(unchanged) or changed.union(unchanged) != set(rule_ids):
            raise ValueError("mission change sets do not exactly cover baseline requirements")
        if changes["previous_snapshot_id"] is None:
            raise ValueError("compared Mission snapshot lacks a previous snapshot ID")
    elif changes["history_state"] == "no previous collection":
        if changed or unchanged or changes["previous_snapshot_id"] is not None:
            raise ValueError("Mission snapshot without history contains comparison claims")
    else:
        raise ValueError("mission changes history state is invalid")
    collection = cast(dict[str, JsonValue], document["collection"])
    if changes["current_collection_timestamp_utc"] != collection["collected_at_utc"]:
        raise ValueError("mission comparison current timestamp is inconsistent")


def _exact_object(
    parent: Mapping[str, JsonValue], field: str, expected_fields: set[str]
) -> dict[str, JsonValue]:
    value = parent.get(field)
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise ValueError(f"mission field {field} contains an unexpected or missing field")
    return value


def _requirement_fields() -> frozenset[str]:
    return frozenset(
        {
            "ordinal",
            "rule_id",
            "title",
            "section",
            "platform",
            "expected_value",
            "observed_value",
            "outcome",
            "severity",
            "evaluation_included",
            "assignment_summary",
            "setting_key",
            "provider_definition_ids",
            "matched_provider_definition_ids",
            "parent_resource_refs",
            "provider_mapping_registry_version",
            "mapping_review_status",
            "mappings",
            "source_evidence_ids",
            "additional_evidence_required",
            "requirement_id",
            "fingerprint",
        }
    )


def _finding_fields() -> frozenset[str]:
    return frozenset(
        {
            "requirement_id",
            "rule_id",
            "title",
            "platform",
            "drift_type",
            "severity",
            "expected_value",
            "observed_value",
            "assignment_summary",
            "affected_device_count",
            "source_evidence_ids",
            "mapped_controls",
            "additional_evidence_required",
            "observed_at_utc",
            "baseline_rule_fingerprint",
            "remediation_guidance",
            "limitations",
            "setting_key",
            "provider_definition_ids",
            "matched_provider_definition_ids",
            "parent_resource_refs",
            "provider_mapping_registry_version",
            "mapping_review_status",
            "finding_id",
            "fingerprint",
        }
    )


def _resource_fields() -> frozenset[str]:
    return frozenset(
        {
            "resource_ref",
            "source_evidence_id",
            "resource_family",
            "title",
            "platforms",
            "resource_type",
            "assignment_count",
            "state",
            "source_api_version",
            "fingerprint",
            "parent_resource_ref",
            "provider_definition_id",
            "evaluation_reason",
            "action_expected",
        }
    )


def _gap_fields() -> frozenset[str]:
    return frozenset(
        {
            "gap_id",
            "resource_family",
            "source_endpoint_key",
            "source_api_version",
            "required_permission",
            "reason",
            "http_status",
            "additional_evidence_required",
        }
    )
