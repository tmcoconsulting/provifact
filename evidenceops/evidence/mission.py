"""Deterministic EvidenceOps Mission Control evidence and drift model."""

from __future__ import annotations

import hashlib
import hmac
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from typing import Final, cast

from evidenceops.baselines import APPROVAL_RECORD, BASELINE_RULES, DEMO_RULE_MAPPINGS
from evidenceops.domain import JsonValue, canonical_json, fingerprint
from evidenceops.providers.apple import AppleIntuneCollection, summarize_devices
from evidenceops.sanitization import assert_public_safe

MISSION_SCHEMA_VERSION: Final = "2.0.0"
MISSION_ALGORITHM_VERSION: Final = "evidenceops-mission-drift-v2.0.0"
PUBLICATION_POLICY_VERSION: Final = "evidenceops-mission-public-v1.0.0"
FRESHNESS_SECONDS: Final = 86_400


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
    requirements, findings, used_evidence_ids = _evaluate_requirements(collection)
    resources = _public_resources(collection.records, pseudonym_key, synthetic=synthetic)
    unmapped = [
        resource
        for resource in resources
        if cast(str, resource["source_evidence_id"]) not in used_evidence_ids
        and resource["resource_family"] not in {"managed_devices", "managed_devices_assignments"}
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
        "limitations": APPROVAL_RECORD["limitations"],
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
        "changes": _changes(previous, requirements, metrics),
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
                "EvidenceOps does not have sufficient collected evidence to answer this question."
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
    if not isinstance(document["collection"], dict) or not isinstance(document["baseline"], dict):
        raise ValueError("mission collection and baseline must be objects")
    assert_public_safe(cast(JsonValue, document))
    return document


def _evaluate_requirements(
    collection: AppleIntuneCollection,
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
    for ordinal, (section, rule_id) in enumerate(
        ((section, rule_id) for section, rules in BASELINE_RULES for rule_id in rules),
        start=1,
    ):
        mapping = DEMO_RULE_MAPPINGS.get(rule_id)
        if mapping is None:
            requirement = _requirement(
                ordinal=ordinal,
                section=section,
                rule_id=rule_id,
                title=rule_id.replace("_", " ").title(),
                expected="provider mapping not implemented",
                outcome=DriftOutcome.UNSUPPORTED,
                severity="informational",
                mappings={},
                evidence_ids=[],
                assignment_summary="not evaluated",
                observed="not evaluated",
            )
            requirements.append(requirement)
            continue
        candidates = _matching_settings(setting_records, mapping)
        evidence_ids = [cast(str, item["evidence_id"]) for item in candidates]
        used.update(evidence_ids)
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
        used.update(cast(str, item["evidence_id"]) for item in related_assignments)
        outcome, observed = _deterministic_outcome(mapping, candidates, related_assignments)
        assignment_summary = (
            f"{len(related_assignments)} normalized assignment(s)"
            if related_assignments
            else "no normalized assignment observed"
        )
        requirement = _requirement(
            ordinal=ordinal,
            section=section,
            rule_id=rule_id,
            title=cast(str, mapping["title"]),
            expected=mapping["expected_value"],
            outcome=outcome,
            severity=cast(str, mapping["severity"]),
            mappings={
                key: mapping[key]
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
        )
        requirements.append(requirement)
        if outcome is not DriftOutcome.ALIGNED:
            findings.append(_finding(requirement, mapping, collection.collected_at_utc))
    return requirements, findings, used


def _matching_settings(
    records: Sequence[dict[str, JsonValue]], mapping: Mapping[str, JsonValue]
) -> list[dict[str, JsonValue]]:
    needles = {
        cast(str, mapping["setting_key"]).lower(),
        cast(str, mapping["payload_key"]).lower(),
    }
    matches: list[dict[str, JsonValue]] = []
    for record in records:
        properties = cast(dict[str, JsonValue], record["properties"])
        definition = cast(str, properties["setting_definition_id"]).lower()
        if any(needle in definition for needle in needles):
            matches.append(record)
    return sorted(matches, key=lambda item: cast(str, item["evidence_id"]))


def _deterministic_outcome(
    mapping: Mapping[str, JsonValue],
    settings: Sequence[dict[str, JsonValue]],
    assignments: Sequence[dict[str, JsonValue]],
) -> tuple[DriftOutcome, JsonValue]:
    if not settings:
        return DriftOutcome.MISSING, "not observed"
    values = [
        cast(dict[str, JsonValue], item["properties"])["normalized_value"] for item in settings
    ]
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
    if not assignments:
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
    mapping: Mapping[str, JsonValue],
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
            "Review assignment scope and exclusions; EvidenceOps cannot assign policies."
        ),
        DriftOutcome.CONFLICTING.value: (
            "Review overlapping policies and effective precedence with an endpoint administrator."
        ),
        DriftOutcome.COLLECTION_GAP.value: (
            "Restore read-only evidence collection or provide alternate evidence."
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
            "Human review is required; EvidenceOps has no Intune write or remediation capability.",
        ),
        "limitations": [
            "Technical evidence does not establish organizational compliance.",
            "No Intune write or automatic remediation operation exists.",
        ],
        "setting_key": mapping["setting_key"],
    }
    digest = fingerprint(unsigned)
    return {**unsigned, "finding_id": f"finding-{digest[7:31]}", "fingerprint": digest}


def _public_resources(
    records: Sequence[dict[str, JsonValue]], pseudonym_key: bytes, *, synthetic: bool
) -> list[dict[str, JsonValue]]:
    result: list[dict[str, JsonValue]] = []
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
            }
        )
    return sorted(
        result,
        key=lambda item: (cast(str, item["resource_family"]), cast(str, item["resource_ref"])),
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
            "Mapped macOS baseline requirements with sufficient provider support; iOS/iPadOS "
            "and unsupported macOS rules are excluded."
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
) -> dict[str, JsonValue]:
    current = {cast(str, item["rule_id"]): cast(str, item["outcome"]) for item in requirements}
    if previous is None:
        return {
            "previous_snapshot_id": None,
            "alignment_change_points": None,
            "new_drift": [],
            "resolved_drift": [],
            "changed_requirements": [],
            "history_state": "no previous collection",
        }
    previous_requirements = cast(list[dict[str, JsonValue]], previous.get("requirements", []))
    old = {cast(str, item["rule_id"]): cast(str, item["outcome"]) for item in previous_requirements}
    changed = sorted(rule for rule, outcome in current.items() if old.get(rule) != outcome)
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
        "history_state": "compared",
    }


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
