"""Schema-v1 deterministic comparison and evidence packaging."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from typing import Final, cast

from evidenceops.domain import (
    EvidenceObject,
    EvidenceSchemaError,
    EvidenceStatus,
    JsonValue,
    make_evidence_object,
    validate_evidence_object,
)

ALGORITHM_VERSION: Final = "evidenceops-drift-v1.1.0"


def evaluate_desired_state(
    desired_state: Sequence[EvidenceObject],
    observations: Sequence[EvidenceObject],
    collection: EvidenceObject,
) -> list[EvidenceObject]:
    """Produce reproducible findings without inference or source-system mutation."""
    validated_collection = validate_evidence_object(collection)
    if validated_collection["object_type"] != "collection_metadata":
        raise EvidenceSchemaError("collection must be collection_metadata")

    by_setting: dict[str, list[EvidenceObject]] = defaultdict(list)
    for observation in observations:
        validated = validate_evidence_object(observation)
        if validated["object_type"] != "normalized_configuration_observation":
            raise EvidenceSchemaError("observations must contain normalized observations")
        by_setting[cast(str, validated["setting_key"])].append(validated)

    findings: list[EvidenceObject] = []
    for desired in desired_state:
        validated_desired = validate_evidence_object(desired)
        if validated_desired["object_type"] != "desired_state_record":
            raise EvidenceSchemaError("desired_state must contain desired state records")
        setting_key = cast(str, validated_desired["setting_key"])
        candidates = sorted(
            by_setting.get(setting_key, []), key=lambda item: cast(str, item["evidence_id"])
        )
        status, additional = _compare(validated_desired, candidates)
        input_fingerprints = [cast(str, validated_desired["content_fingerprint"])]
        input_fingerprints.extend(cast(str, item["content_fingerprint"]) for item in candidates)
        findings.append(
            make_evidence_object(
                "deterministic_drift_finding",
                {
                    "collection_evidence_id": cast(str, validated_collection["evidence_id"]),
                    "desired_state_evidence_id": cast(str, validated_desired["evidence_id"]),
                    "observation_evidence_ids": cast(
                        JsonValue, [cast(str, item["evidence_id"]) for item in candidates]
                    ),
                    "status": status.value,
                    "desired_state_git_commit_sha": validated_desired[
                        "desired_state_git_commit_sha"
                    ],
                    "deterministic_algorithm_version": ALGORITHM_VERSION,
                    "input_fingerprints": cast(JsonValue, input_fingerprints),
                    "additional_evidence_required": cast(JsonValue, additional),
                },
            )
        )
    return findings


def build_references(
    desired_state: Sequence[EvidenceObject],
    observations: Sequence[EvidenceObject],
    findings: Sequence[EvidenceObject],
    collection: EvidenceObject,
) -> list[EvidenceObject]:
    """Build stable, human-readable links to every package evidence object."""
    references: list[EvidenceObject] = []
    collections = [(collection, "source collection")]
    groups: tuple[tuple[Sequence[EvidenceObject], str], ...] = (
        (desired_state, "desired state"),
        (observations, "normalized observation"),
        (findings, "deterministic finding"),
    )
    for item, label in collections:
        references.append(_reference(item, label))
    for items, label in groups:
        references.extend(_reference(item, label) for item in items)
    return references


def build_private_package(
    *,
    synthetic: bool,
    provider: EvidenceObject,
    collection: EvidenceObject,
    desired_state: Sequence[EvidenceObject],
    observations: Sequence[EvidenceObject],
    retention: dict[str, JsonValue],
    private_trace: dict[str, JsonValue],
) -> EvidenceObject:
    """Assemble one normalized private package; raw Graph responses are never included."""
    findings = evaluate_desired_state(desired_state, observations, collection)
    references = build_references(desired_state, observations, findings, collection)
    return make_evidence_object(
        "private_evidence_package",
        {
            "synthetic": synthetic,
            "provider": provider,
            "collection": collection,
            "desired_state": cast(JsonValue, list(desired_state)),
            "observations": cast(JsonValue, list(observations)),
            "findings": cast(JsonValue, findings),
            "evidence_references": cast(JsonValue, references),
            "retention": retention,
            "private_trace": private_trace,
            "human_approval_status": EvidenceStatus.HUMAN_REVIEW_REQUIRED.value,
        },
    )


def _compare(
    desired: EvidenceObject, observations: Sequence[EvidenceObject]
) -> tuple[EvidenceStatus, list[str]]:
    if desired["evaluation_mode"] == "unsupported":
        return EvidenceStatus.NOT_EVALUATED, ["A supported deterministic evaluator is required."]
    if not observations:
        return EvidenceStatus.ADDITIONAL_EVIDENCE_REQUIRED, [
            "No normalized observation was present for this desired-state record."
        ]
    if len(observations) > 1:
        return EvidenceStatus.HUMAN_REVIEW_REQUIRED, [
            "Multiple observations require an explicit deterministic selection rule."
        ]
    observation = observations[0]
    if observation["observation_state"] in {"unsupported", "not_evaluated"}:
        return EvidenceStatus.NOT_EVALUATED, [
            "The provider reported that this setting is unsupported or not evaluated."
        ]
    if observation["observation_state"] != EvidenceStatus.OBSERVED.value:
        return EvidenceStatus.ADDITIONAL_EVIDENCE_REQUIRED, [
            "The provider did not return an observed value."
        ]
    if desired["evaluation_mode"] == "maximum":
        desired_maximum = _finite_number(desired["desired_value"])
        observed_value = _finite_number(observation["observed_value"])
        if desired_maximum is None or observed_value is None:
            return EvidenceStatus.NOT_EVALUATED, [
                "Maximum evaluation requires finite numeric desired and observed values."
            ]
        if observed_value <= desired_maximum:
            return EvidenceStatus.MATCHES_DESIRED_STATE, []
        return EvidenceStatus.DIFFERS_FROM_DESIRED_STATE, []
    if desired["desired_value"] == observation["observed_value"]:
        return EvidenceStatus.MATCHES_DESIRED_STATE, []
    return EvidenceStatus.DIFFERS_FROM_DESIRED_STATE, []


def _finite_number(value: JsonValue) -> int | float | None:
    """Return a comparable JSON number while excluding booleans and non-finite floats."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return value


def _reference(item: EvidenceObject, label: str) -> EvidenceObject:
    validated = validate_evidence_object(item)
    return make_evidence_object(
        "evidence_reference",
        {
            "referenced_evidence_id": validated["evidence_id"],
            "reference_kind": validated["object_type"],
            "label": label,
        },
    )
