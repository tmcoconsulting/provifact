"""Deterministic verification for untrusted model narratives."""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Final, cast

from evidenceops.domain import (
    EvidenceObject,
    EvidenceSchemaError,
    JsonValue,
    fingerprint,
    make_evidence_object,
    validate_evidence_object,
)

VERIFIER_VERSION: Final = "evidenceops-narrative-verifier-v1.1.0"
_VERDICT_RE: Final = re.compile(
    r"\b(?:compliant|certified|control\s+(?:is\s+)?satisfied|MET|meets?\s+compliance)\b",
    re.IGNORECASE,
)
_FRAMEWORK_ID_RE: Final = re.compile(
    r"\b(?:(?:CMMC|NIST|CIS|STIG|ISO)\s*[-: ]?[A-Z]*\d+(?:\.\d+)*|[A-Z]{2}-\d+)\b",
    re.IGNORECASE,
)
_EVIDENCE_MENTION_RE: Final = re.compile(r"\bev1-[0-9a-f]{24}\b")


def verify_narrative(narrative: object, package: EvidenceObject) -> EvidenceObject:
    """Return a tamper-evident accept/quarantine result without trusting model text."""
    public = validate_evidence_object(package)
    if public["object_type"] != "sanitized_public_evidence_package":
        raise ValueError("narrative verification requires a sanitized public package")
    reasons: list[str] = []
    accepted_claims: list[str] = []
    rejected_claims: list[str] = []
    try:
        validated = validate_evidence_object(narrative)
        if validated["object_type"] != "generated_narrative":
            raise EvidenceSchemaError("input is not a generated narrative")
    except EvidenceSchemaError as exc:
        reasons.append(f"narrative schema rejected: {exc}")
        return _result(
            narrative_id=_fallback_evidence_id(narrative),
            package_id=cast(str, public["evidence_id"]),
            accepted_claims=accepted_claims,
            rejected_claims=["entire narrative quarantined"],
            reasons=reasons,
        )

    narrative_document = validated
    if narrative_document["source_package_evidence_id"] != public["evidence_id"]:
        reasons.append("narrative source package ID does not match the supplied package")
    package_text = json.dumps(public, sort_keys=True)
    package_ids = _package_evidence_ids(public)
    findings = {
        cast(str, item["evidence_id"]): item
        for item in cast(list[EvidenceObject], public["findings"])
    }
    full_text = _narrative_text(narrative_document)
    ungrounded_mentions = sorted(
        set(_EVIDENCE_MENTION_RE.findall(full_text)).difference(package_ids)
    )
    if ungrounded_mentions:
        reasons.append(
            "nonexistent evidence IDs in narrative text: " + ", ".join(ungrounded_mentions)
        )
    if _VERDICT_RE.search(full_text):
        reasons.append("unsupported compliance or certification verdict")
    unsupported_frameworks = {
        match.group(0)
        for match in _FRAMEWORK_ID_RE.finditer(full_text)
        if match.group(0) not in package_text
    }
    if unsupported_frameworks:
        reasons.append(
            "unsupported control or framework ID: " + ", ".join(sorted(unsupported_frameworks))
        )
    if not re.search(r"\bhuman (?:review|reviewer|assessor)\b", full_text, re.IGNORECASE):
        reasons.append("required human-review language is missing")

    explanations = cast(list[JsonValue], narrative_document["drift_explanations"])
    explanation_ids = [
        cast(str, cast(dict[str, JsonValue], item)["finding_evidence_id"]) for item in explanations
    ]
    explanation_id_counts = Counter(explanation_ids)
    duplicate_ids = sorted(
        finding_id for finding_id, count in explanation_id_counts.items() if count > 1
    )
    narrative_finding_ids = set(explanation_ids)
    expected_finding_ids = set(findings)
    missing_ids = sorted(expected_finding_ids.difference(narrative_finding_ids))
    unknown_ids = sorted(narrative_finding_ids.difference(expected_finding_ids))
    if duplicate_ids:
        reasons.append("duplicate finding explanation IDs: " + ", ".join(duplicate_ids))
    if missing_ids:
        reasons.append("missing deterministic finding explanations: " + ", ".join(missing_ids))
    if unknown_ids:
        reasons.append("unknown finding explanation IDs: " + ", ".join(unknown_ids))

    accepted_typed_claims: set[str] = set()
    rejected_typed_claims: set[str] = set()
    for explanation_value in explanations:
        explanation = cast(dict[str, JsonValue], explanation_value)
        finding_id = cast(str, explanation["finding_evidence_id"])
        evidence_references = cast(list[str], explanation["evidence_references"])
        claim_reasons: list[str] = []
        finding = findings.get(finding_id)
        if finding is not None and explanation["deterministic_status"] != finding["status"]:
            claim_reasons.append("narrative contradicts the deterministic finding status")
        deterministic_claim = explanation.get("deterministic_claim")
        if not isinstance(deterministic_claim, dict):
            claim_reasons.append("typed deterministic claim is missing")
        elif finding is not None:
            if deterministic_claim.get("claim_code") != "finding_status":
                claim_reasons.append("typed deterministic claim code is unsupported")
            if deterministic_claim.get("claim_value") != finding["status"]:
                claim_reasons.append("typed deterministic claim contradicts the finding status")
            if deterministic_claim.get("claim_value") != explanation["deterministic_status"]:
                claim_reasons.append("typed deterministic claim contradicts the narrative status")
        outside = sorted(set(evidence_references).difference(package_ids))
        if outside:
            claim_reasons.append(
                "evidence references outside supplied package: " + ", ".join(outside)
            )
        if finding is not None:
            permitted = {
                finding_id,
                cast(str, finding["collection_evidence_id"]),
                cast(str, finding["desired_state_evidence_id"]),
                *cast(list[str], finding["observation_evidence_ids"]),
            }
            unrelated = sorted(set(evidence_references).difference(permitted))
            if unrelated:
                claim_reasons.append("claim cites evidence unrelated to its finding")
        claim_label = f"{finding_id}:finding_status={explanation['deterministic_status']}"
        if claim_reasons or finding_id in duplicate_ids or finding is None:
            rejected_typed_claims.add(claim_label)
            reasons.extend(claim_reasons)
        else:
            accepted_typed_claims.add(claim_label)

    accepted_claims.extend(sorted(accepted_typed_claims))
    rejected_claims.extend(sorted(rejected_typed_claims))
    rejected_claims.extend(_generated_prose_claims(narrative_document))
    reasons.append(
        "free-form generated analysis is not machine-verifiable and remains quarantined for "
        "human review"
    )
    return _result(
        narrative_id=cast(str, narrative_document["evidence_id"]),
        package_id=cast(str, public["evidence_id"]),
        accepted_claims=accepted_claims,
        rejected_claims=rejected_claims,
        reasons=_deduplicate(reasons),
    )


def _generated_prose_claims(narrative: EvidenceObject) -> list[str]:
    """Name, but never semantically approve, every model-controlled prose field."""
    result = ["generated prose quarantined: executive_summary"]
    for field in (
        "limitations",
        "additional_evidence_required",
        "suggested_human_review_questions",
    ):
        for index, _ in enumerate(cast(list[str], narrative[field])):
            result.append(f"generated prose quarantined: {field}[{index}]")
    for index, _ in enumerate(cast(list[dict[str, JsonValue]], narrative["drift_explanations"])):
        result.append(
            f"generated prose quarantined: drift_explanations[{index}].change_or_drift_explanation"
        )
        result.append(f"generated prose quarantined: drift_explanations[{index}].technical_impact")
    return result


def _deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _package_evidence_ids(package: EvidenceObject) -> set[str]:
    result = {cast(str, package["evidence_id"])}
    for field in ("provider", "collection"):
        result.add(cast(str, cast(EvidenceObject, package[field])["evidence_id"]))
    for field in ("desired_state", "observations", "findings", "evidence_references"):
        result.update(
            cast(str, item["evidence_id"]) for item in cast(list[EvidenceObject], package[field])
        )
    return result


def _narrative_text(narrative: EvidenceObject) -> str:
    parts = [cast(str, narrative["executive_summary"])]
    for field in (
        "limitations",
        "additional_evidence_required",
        "suggested_human_review_questions",
    ):
        parts.extend(cast(list[str], narrative[field]))
    for item in cast(list[dict[str, JsonValue]], narrative["drift_explanations"]):
        parts.extend(
            [cast(str, item["change_or_drift_explanation"]), cast(str, item["technical_impact"])]
        )
    return "\n".join(parts)


def _fallback_evidence_id(value: object) -> str:
    try:
        encoded: JsonValue = cast(JsonValue, value)
        digest = fingerprint(encoded).removeprefix("sha256:")
    except (TypeError, ValueError):
        digest = fingerprint(repr(value)).removeprefix("sha256:")
    return f"ev1-{digest[:24]}"


def _result(
    *,
    narrative_id: str,
    package_id: str,
    accepted_claims: list[str],
    rejected_claims: list[str],
    reasons: list[str],
) -> EvidenceObject:
    return make_evidence_object(
        "narrative_verification_result",
        {
            "narrative_evidence_id": narrative_id,
            "source_package_evidence_id": package_id,
            "verifier_version": VERIFIER_VERSION,
            "accepted": not reasons and not rejected_claims,
            "accepted_claims": cast(JsonValue, accepted_claims),
            "rejected_claims": cast(JsonValue, rejected_claims),
            "reasons": cast(JsonValue, reasons),
            "human_review_required": True,
        },
    )
