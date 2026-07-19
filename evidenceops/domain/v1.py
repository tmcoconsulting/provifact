"""Strict, JSON-serializable EvidenceOps schema-v1 objects.

The Phase 0 dataclasses remain available for backward compatibility.  New evidence
packages use these self-fingerprinting dictionaries so artifacts can be inspected
without importing a vendor SDK or a model client.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Final, cast

from evidenceops.domain.models import JsonValue

SCHEMA_VERSION: Final = "1.0.0"
EVIDENCE_ID_PREFIX: Final = "ev1-"
FINGERPRINT_PREFIX: Final = "sha256:"
RESERVED_FIELDS: Final = frozenset(
    {"schema_version", "object_type", "evidence_id", "content_fingerprint"}
)


class EvidenceSchemaError(ValueError):
    """Raised when an evidence object violates the schema-v1 contract."""


class EvidenceStatus(StrEnum):
    """Restrained deterministic result vocabulary."""

    OBSERVED = "observed"
    MATCHES_DESIRED_STATE = "matches desired state"
    DIFFERS_FROM_DESIRED_STATE = "differs from desired state"
    ADDITIONAL_EVIDENCE_REQUIRED = "additional evidence required"
    HUMAN_REVIEW_REQUIRED = "human review required"
    NOT_EVALUATED = "not evaluated"


class FreshnessState(StrEnum):
    """Time-derived freshness state, never a compliance conclusion."""

    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"


class NarrativeClaimCode(StrEnum):
    """Closed vocabulary for narrative claims that deterministic code can verify."""

    FINDING_STATUS = "finding_status"


EvidenceObject = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class ObjectContract:
    """Exact top-level field contract for one object type."""

    required: frozenset[str]
    optional: frozenset[str] = frozenset()

    @property
    def allowed(self) -> frozenset[str]:
        return RESERVED_FIELDS | self.required | self.optional


_CONTRACTS: Final[dict[str, ObjectContract]] = {
    "provider_metadata": ObjectContract(
        frozenset({"provider", "provider_version", "source_api_version"})
    ),
    "collection_metadata": ObjectContract(
        frozenset(
            {
                "collection_timestamp_utc",
                "provider_evidence_id",
                "desired_state_git_commit_sha",
                "deterministic_algorithm_version",
                "freshness",
            }
        )
    ),
    "desired_state_record": ObjectContract(
        frozenset(
            {
                "record_key",
                "platform",
                "setting_key",
                "desired_value",
                "evaluation_mode",
                "title",
                "description",
                "desired_state_git_commit_sha",
            }
        )
    ),
    "normalized_configuration_observation": ObjectContract(
        frozenset(
            {
                "collection_evidence_id",
                "provider_evidence_id",
                "platform",
                "setting_key",
                "observed_value",
                "observation_state",
                "source_modified_at_utc",
                "freshness",
            }
        ),
        frozenset({"private_trace"}),
    ),
    "deterministic_drift_finding": ObjectContract(
        frozenset(
            {
                "collection_evidence_id",
                "desired_state_evidence_id",
                "observation_evidence_ids",
                "status",
                "desired_state_git_commit_sha",
                "deterministic_algorithm_version",
                "input_fingerprints",
                "additional_evidence_required",
            }
        )
    ),
    "evidence_reference": ObjectContract(
        frozenset({"referenced_evidence_id", "reference_kind", "label"})
    ),
    "private_evidence_package": ObjectContract(
        frozenset(
            {
                "synthetic",
                "provider",
                "collection",
                "desired_state",
                "observations",
                "findings",
                "evidence_references",
                "retention",
                "private_trace",
                "human_approval_status",
            }
        )
    ),
    "sanitized_public_evidence_package": ObjectContract(
        frozenset(
            {
                "synthetic",
                "source_type",
                "provider",
                "collection",
                "desired_state",
                "observations",
                "findings",
                "evidence_references",
                "publication",
                "human_approval_status",
            }
        )
    ),
    "generated_narrative": ObjectContract(
        frozenset(
            {
                "ai_generated_analysis",
                "human_review_required",
                "model",
                "source_package_evidence_id",
                "executive_summary",
                "drift_explanations",
                "limitations",
                "additional_evidence_required",
                "suggested_human_review_questions",
            }
        )
    ),
    "narrative_verification_result": ObjectContract(
        frozenset(
            {
                "narrative_evidence_id",
                "source_package_evidence_id",
                "verifier_version",
                "accepted",
                "accepted_claims",
                "rejected_claims",
                "reasons",
                "human_review_required",
            }
        )
    ),
}

_EVIDENCE_ID_RE: Final = re.compile(r"^ev1-[0-9a-f]{24}$")
_FINGERPRINT_RE: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_SHA_RE: Final = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$|^synthetic-[a-z0-9-]+$")


def canonical_json(value: JsonValue) -> str:
    """Return the one canonical JSON encoding used for fingerprints."""
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def fingerprint(value: JsonValue) -> str:
    """Return a versioned SHA-256 content fingerprint."""
    digest = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
    return f"{FINGERPRINT_PREFIX}{digest}"


def make_evidence_object(object_type: str, payload: dict[str, JsonValue]) -> EvidenceObject:
    """Create and validate an immutable-by-convention evidence dictionary.

    Identity fields are derived from canonical content.  Supplying them in ``payload``
    is rejected so callers cannot create misleading evidence identifiers.
    """
    if object_type not in _CONTRACTS:
        raise EvidenceSchemaError(f"unsupported object_type: {object_type}")
    overlap = RESERVED_FIELDS.intersection(payload)
    if overlap:
        raise EvidenceSchemaError(f"reserved fields supplied: {', '.join(sorted(overlap))}")
    unsigned: EvidenceObject = {
        "schema_version": SCHEMA_VERSION,
        "object_type": object_type,
        **payload,
    }
    content_fingerprint = fingerprint(unsigned)
    completed: EvidenceObject = {
        **unsigned,
        "evidence_id": f"{EVIDENCE_ID_PREFIX}{content_fingerprint[-64:-40]}",
        "content_fingerprint": content_fingerprint,
    }
    validate_evidence_object(completed)
    return completed


def validate_evidence_object(value: object, *, verify_identity: bool = True) -> EvidenceObject:
    """Validate one schema-v1 evidence object and all nested evidence objects."""
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise EvidenceSchemaError("evidence object must be a string-keyed object")
    document = cast(EvidenceObject, value)
    object_type = _required_string(document, "object_type")
    try:
        contract = _CONTRACTS[object_type]
    except KeyError as exc:
        raise EvidenceSchemaError(f"unsupported object_type: {object_type}") from exc
    if document.get("schema_version") != SCHEMA_VERSION:
        raise EvidenceSchemaError(f"unsupported schema_version for {object_type}")
    missing = contract.required.difference(document)
    if missing:
        raise EvidenceSchemaError(f"{object_type} missing fields: {', '.join(sorted(missing))}")
    unexpected = set(document).difference(contract.allowed)
    if unexpected:
        raise EvidenceSchemaError(
            f"{object_type} has unexpected fields: {', '.join(sorted(unexpected))}"
        )
    evidence_id = _required_string(document, "evidence_id")
    content_fingerprint = _required_string(document, "content_fingerprint")
    if not _EVIDENCE_ID_RE.fullmatch(evidence_id):
        raise EvidenceSchemaError(f"invalid evidence_id for {object_type}")
    if not _FINGERPRINT_RE.fullmatch(content_fingerprint):
        raise EvidenceSchemaError(f"invalid content_fingerprint for {object_type}")

    _validate_shape(document, object_type)
    if verify_identity:
        unsigned = {key: item for key, item in document.items() if key not in RESERVED_FIELDS}
        expected_unsigned: EvidenceObject = {
            "schema_version": SCHEMA_VERSION,
            "object_type": object_type,
            **unsigned,
        }
        expected_fingerprint = fingerprint(expected_unsigned)
        expected_id = f"{EVIDENCE_ID_PREFIX}{expected_fingerprint[-64:-40]}"
        if content_fingerprint != expected_fingerprint or evidence_id != expected_id:
            raise EvidenceSchemaError(f"identity mismatch for {object_type}")
    return document


def _validate_shape(document: EvidenceObject, object_type: str) -> None:
    if object_type == "provider_metadata":
        for field in ("provider", "provider_version", "source_api_version"):
            _required_string(document, field)
    elif object_type == "collection_metadata":
        _required_utc(document, "collection_timestamp_utc")
        _required_evidence_id(document, "provider_evidence_id")
        _optional_sha(document, "desired_state_git_commit_sha")
        _required_string(document, "deterministic_algorithm_version")
        _validate_freshness(document.get("freshness"))
    elif object_type == "desired_state_record":
        for field in (
            "record_key",
            "platform",
            "setting_key",
            "evaluation_mode",
            "title",
            "description",
        ):
            _required_string(document, field)
        _optional_sha(document, "desired_state_git_commit_sha")
    elif object_type == "normalized_configuration_observation":
        for field in ("collection_evidence_id", "provider_evidence_id"):
            _required_evidence_id(document, field)
        for field in ("platform", "setting_key", "observation_state"):
            _required_string(document, field)
        _required_utc(document, "source_modified_at_utc", allow_none=True)
        _validate_freshness(document.get("freshness"))
        _optional_mapping(document, "private_trace")
    elif object_type == "deterministic_drift_finding":
        _required_evidence_id(document, "collection_evidence_id")
        _required_evidence_id(document, "desired_state_evidence_id")
        _required_evidence_id_list(document, "observation_evidence_ids")
        status = _required_string(document, "status")
        if status not in EvidenceStatus:
            raise EvidenceSchemaError(f"unsupported finding status: {status}")
        _optional_sha(document, "desired_state_git_commit_sha")
        _required_string(document, "deterministic_algorithm_version")
        _required_fingerprint_list(document, "input_fingerprints")
        _required_string_list(document, "additional_evidence_required")
    elif object_type == "evidence_reference":
        _required_evidence_id(document, "referenced_evidence_id")
        _required_string(document, "reference_kind")
        _required_string(document, "label")
    elif object_type in {"private_evidence_package", "sanitized_public_evidence_package"}:
        _required_bool(document, "synthetic")
        _required_nested(document, "provider", "provider_metadata")
        _required_nested(document, "collection", "collection_metadata")
        _required_nested_list(document, "desired_state", "desired_state_record")
        _required_nested_list(document, "observations", "normalized_configuration_observation")
        _required_nested_list(document, "findings", "deterministic_drift_finding")
        _required_nested_list(document, "evidence_references", "evidence_reference")
        human_approval_status = _required_string(document, "human_approval_status")
        if human_approval_status != EvidenceStatus.HUMAN_REVIEW_REQUIRED.value:
            raise EvidenceSchemaError("evidence package must require human review")
        if object_type == "private_evidence_package":
            _required_mapping(document, "retention")
            _required_mapping(document, "private_trace")
        else:
            source_type = _required_string(document, "source_type")
            if source_type not in {"curated-synthetic-fixture", "sanitized-live-collection"}:
                raise EvidenceSchemaError(f"unsupported public source_type: {source_type}")
            _required_mapping(document, "publication")
    elif object_type == "generated_narrative":
        if document.get("ai_generated_analysis") is not True:
            raise EvidenceSchemaError("narrative must be labeled ai_generated_analysis")
        if document.get("human_review_required") is not True:
            raise EvidenceSchemaError("narrative must require human review")
        for field in ("model", "executive_summary"):
            _required_string(document, field)
        _required_evidence_id(document, "source_package_evidence_id")
        _validate_drift_explanations(document.get("drift_explanations"))
        for field in (
            "limitations",
            "additional_evidence_required",
            "suggested_human_review_questions",
        ):
            values = _required_string_list(document, field)
            if not values:
                raise EvidenceSchemaError(f"narrative field {field} must not be empty")
    elif object_type == "narrative_verification_result":
        _required_evidence_id(document, "narrative_evidence_id")
        _required_evidence_id(document, "source_package_evidence_id")
        _required_string(document, "verifier_version")
        _required_bool(document, "accepted")
        _required_string_list(document, "accepted_claims")
        _required_string_list(document, "rejected_claims")
        _required_string_list(document, "reasons")
        if document.get("human_review_required") is not True:
            raise EvidenceSchemaError("verification result must preserve human review")


def _required_string(document: EvidenceObject, field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value:
        raise EvidenceSchemaError(f"field {field} must be a non-empty string")
    return value


def _required_bool(document: EvidenceObject, field: str) -> bool:
    value = document.get(field)
    if not isinstance(value, bool):
        raise EvidenceSchemaError(f"field {field} must be a boolean")
    return value


def _required_utc(document: EvidenceObject, field: str, *, allow_none: bool = False) -> str | None:
    value = document.get(field)
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value.endswith("Z"):
        raise EvidenceSchemaError(f"field {field} must be a UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceSchemaError(f"field {field} must be an ISO-8601 timestamp") from exc
    utc_offset = parsed.utcoffset()
    if utc_offset is None or utc_offset.total_seconds() != 0:
        raise EvidenceSchemaError(f"field {field} must be UTC")
    return value


def _optional_sha(document: EvidenceObject, field: str) -> None:
    value = document.get(field)
    if value is not None and (not isinstance(value, str) or not _SHA_RE.fullmatch(value)):
        raise EvidenceSchemaError(f"field {field} must be a Git SHA, synthetic marker, or null")


def _required_evidence_id(document: EvidenceObject, field: str) -> str:
    value = _required_string(document, field)
    if not _EVIDENCE_ID_RE.fullmatch(value):
        raise EvidenceSchemaError(f"field {field} must be an evidence ID")
    return value


def _required_evidence_id_list(document: EvidenceObject, field: str) -> list[str]:
    values = _required_string_list(document, field)
    if any(not _EVIDENCE_ID_RE.fullmatch(value) for value in values):
        raise EvidenceSchemaError(f"field {field} must contain only evidence IDs")
    return values


def _required_fingerprint_list(document: EvidenceObject, field: str) -> list[str]:
    values = _required_string_list(document, field)
    if any(not _FINGERPRINT_RE.fullmatch(value) for value in values):
        raise EvidenceSchemaError(f"field {field} must contain only fingerprints")
    return values


def _required_string_list(document: EvidenceObject, field: str) -> list[str]:
    value = document.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise EvidenceSchemaError(f"field {field} must be an array of non-empty strings")
    return cast(list[str], value)


def _required_mapping(document: EvidenceObject, field: str) -> dict[str, JsonValue]:
    value = document.get(field)
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise EvidenceSchemaError(f"field {field} must be an object")
    return value


def _optional_mapping(document: EvidenceObject, field: str) -> None:
    if field in document:
        _required_mapping(document, field)


def _required_nested(document: EvidenceObject, field: str, object_type: str) -> EvidenceObject:
    nested = validate_evidence_object(document.get(field))
    if nested["object_type"] != object_type:
        raise EvidenceSchemaError(f"field {field} must contain {object_type}")
    return nested


def _required_nested_list(
    document: EvidenceObject, field: str, object_type: str
) -> list[EvidenceObject]:
    value = document.get(field)
    if not isinstance(value, list):
        raise EvidenceSchemaError(f"field {field} must be an array")
    result: list[EvidenceObject] = []
    for item in value:
        nested = validate_evidence_object(item)
        if nested["object_type"] != object_type:
            raise EvidenceSchemaError(f"field {field} must contain only {object_type}")
        result.append(nested)
    return result


def _validate_freshness(value: JsonValue | None) -> None:
    if not isinstance(value, dict):
        raise EvidenceSchemaError("freshness must be an object")
    if set(value) != {"as_of_utc", "max_age_seconds", "state"}:
        raise EvidenceSchemaError("freshness has unexpected or missing fields")
    _required_utc(value, "as_of_utc")
    max_age = value.get("max_age_seconds")
    if not isinstance(max_age, int) or isinstance(max_age, bool) or max_age < 0:
        raise EvidenceSchemaError("freshness.max_age_seconds must be a non-negative integer")
    state = value.get("state")
    if not isinstance(state, str) or state not in FreshnessState:
        raise EvidenceSchemaError("freshness.state is unsupported")


def _validate_drift_explanations(value: JsonValue | None) -> None:
    if not isinstance(value, list):
        raise EvidenceSchemaError("drift_explanations must be an array")
    required = {
        "finding_evidence_id",
        "deterministic_status",
        "change_or_drift_explanation",
        "technical_impact",
        "evidence_references",
    }
    optional = {"deterministic_claim"}
    for item in value:
        if (
            not isinstance(item, dict)
            or not required.issubset(item)
            or set(item).difference(required | optional)
        ):
            raise EvidenceSchemaError("drift explanation has unexpected or missing fields")
        explanation = item
        _required_evidence_id(explanation, "finding_evidence_id")
        status = _required_string(explanation, "deterministic_status")
        if status not in EvidenceStatus:
            raise EvidenceSchemaError("drift explanation status is unsupported")
        _required_string(explanation, "change_or_drift_explanation")
        _required_string(explanation, "technical_impact")
        _required_evidence_id_list(explanation, "evidence_references")
        if "deterministic_claim" in explanation:
            _validate_deterministic_claim(explanation["deterministic_claim"])


def _validate_deterministic_claim(value: JsonValue) -> None:
    if not isinstance(value, dict) or set(value) != {"claim_code", "claim_value"}:
        raise EvidenceSchemaError("deterministic claim has unexpected or missing fields")
    if value.get("claim_code") != NarrativeClaimCode.FINDING_STATUS.value:
        raise EvidenceSchemaError("deterministic claim code is unsupported")
    claim_value = value.get("claim_value")
    if not isinstance(claim_value, str) or claim_value not in EvidenceStatus:
        raise EvidenceSchemaError("deterministic claim value is unsupported")


def schema_object_types() -> tuple[str, ...]:
    """Return the complete schema-v1 object catalog for compatibility tests."""
    return tuple(_CONTRACTS)
